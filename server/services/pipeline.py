"""
pipeline.py — Main NotificationPipeline orchestrator.

Wires all seven components in sequence:
  FrequencyCapper → BudgetRouter → ContextRetriever →
  MessageComposer → GuardrailFilter → RewardRanker → SendTimeOptimizer
"""
from __future__ import annotations
import json
import time
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from db.database import UserProfileDB, NotificationLogDB
from models.schemas import (
    ComposeRequest, ComposeResponse, CompositionPath,
    PipelineTrace, CLVTier
)
from services.profile_builder import get_or_create_profile
from services.pipeline_services import (
    route_budget, retrieve_context, compose_candidates,
    apply_guardrails, rank_candidates, check_frequency_cap,
    optimize_send_time, PipelineContext
)


async def run_pipeline(request: ComposeRequest, db: AsyncSession) -> ComposeResponse:
    """
    Execute the full NotifyCompose pipeline for a single notification request.

    Returns a ComposeResponse with the best candidate message,
    delivery schedule, reward score, and full pipeline trace.
    """
    start_time = time.monotonic()
    notification_id = str(uuid.uuid4())

    # ── Fetch User Profile ─────────────────────────────────────────────────────
    profile = await get_or_create_profile(request.user_id, db)

    # ── Step 1: Frequency Capper ───────────────────────────────────────────────
    if request.options.enable_frequency_cap:
        is_capped, cap_reason = await check_frequency_cap(request.user_id, db)
        if is_capped:
            latency = (time.monotonic() - start_time) * 1000
            return ComposeResponse(
                notification_id=notification_id,
                title="",
                body="",
                scheduled_at=datetime.utcnow(),
                composition_path=CompositionPath.frequency_capped,
                reward_score=0.0,
                pipeline_trace=PipelineTrace(
                    budget_decision=cap_reason,
                    latency_ms=round(latency, 1)
                ),
                metadata={"capped": "true", "reason": cap_reason}
            )

    # ── Step 2: Budget Router ──────────────────────────────────────────────────
    composition_path, budget_decision = route_budget(profile, request.options)

    # Build pipeline context object
    affinities = json.loads(profile.category_affinities_json or "{}")
    ctx = PipelineContext(
        user_id=request.user_id,
        clv_tier=CLVTier(request.options.override_clv_tier or profile.clv_tier or "bronze"),
        composition_path=composition_path,
        category_affinities=affinities,
        notification_open_rate=profile.notification_open_rate or 0.0,
    )

    # ── Step 3: Context Retriever ──────────────────────────────────────────────
    context_str = retrieve_context(request, profile, ctx)

    # ── Step 4: Message Composer ───────────────────────────────────────────────
    n_candidates = request.options.max_candidates if composition_path != CompositionPath.template else 1
    candidates = await compose_candidates(request, context_str, ctx, n=n_candidates)

    # ── Step 5: Guardrail Filter ───────────────────────────────────────────────
    if request.options.enable_guardrails:
        candidates = apply_guardrails(candidates, request, ctx)

    # ── Step 6: Reward Ranker ──────────────────────────────────────────────────
    candidates = await rank_candidates(candidates, request, ctx)

    # Best candidate is now candidates[0]
    winner = candidates[0]
    winning_rank = 1  # after sorting, winner is always rank 1

    # ── Step 7: Send-Time Optimizer ────────────────────────────────────────────
    scheduled_at = datetime.utcnow()
    sto_optimized = False
    if request.options.enable_send_time_optimization:
        scheduled_at, sto_optimized = optimize_send_time(
            profile, request.trigger_context.local_hour
        )
        ctx.send_time_optimized = sto_optimized

    # ── Enforce length limits ──────────────────────────────────────────────────
    title = winner.title[:request.options.max_title_length]
    body = winner.body[:request.options.max_body_length]

    # ── Build trace ────────────────────────────────────────────────────────────
    latency = (time.monotonic() - start_time) * 1000
    trace = PipelineTrace(
        budget_decision=budget_decision,
        retrieved_context_keys=ctx.retrieved_keys,
        candidates_generated=len(candidates) + ctx.candidates_filtered,
        guardrails_applied=list(set(ctx.guardrails_applied)),
        candidates_filtered=ctx.candidates_filtered,
        winning_candidate_rank=winning_rank,
        send_time_optimized=sto_optimized,
        latency_ms=round(latency, 1)
    )

    # ── Persist to notification log ────────────────────────────────────────────
    log_entry = NotificationLogDB(
        notification_id=notification_id,
        user_id=request.user_id,
        domain=request.domain.value,
        intent=request.intent.value,
        title=title,
        body=body,
        composition_path=composition_path.value,
        reward_score=winner.reward_score,
        scheduled_at=scheduled_at,
        pipeline_trace_json=trace.model_dump_json(),
    )
    db.add(log_entry)

    # Update total notifications sent counter
    profile.total_notifications_sent = (profile.total_notifications_sent or 0) + 1
    await db.commit()

    return ComposeResponse(
        notification_id=notification_id,
        title=title,
        body=body,
        scheduled_at=scheduled_at,
        composition_path=composition_path,
        reward_score=winner.reward_score,
        pipeline_trace=trace,
        metadata={
            "generation_strategy": winner.generation_strategy,
            "clv_tier": ctx.clv_tier.value,
            "domain": request.domain.value,
        }
    )
