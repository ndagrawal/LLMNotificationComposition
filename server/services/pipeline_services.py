"""
pipeline_services.py — All pipeline component services.

Implements the seven components from Figure 2 of the paper:
  1. BudgetRouter       — CLV-based path selection
  2. ContextRetriever   — RAG-style context assembly
  3. MessageComposer    — LLM candidate generation
  4. GuardrailFilter    — Factuality and policy checks
  5. RewardRanker       — Pairwise-inspired candidate scoring
  6. FrequencyCapper    — Max-touch enforcement
  7. SendTimeOptimizer  — Thompson Sampling bandit
"""
from __future__ import annotations
import json
import math
import random
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import UserProfileDB, NotificationLogDB
from models.schemas import (
    CLVTier, CompositionPath, ComposeRequest, ComposeResponse,
    PipelineTrace, NotificationDomain, NotificationIntent
)

import os

COMPOSE_MODEL = os.getenv("COMPOSE_MODEL", "gpt-4o-mini")
REWARD_MODEL = os.getenv("REWARD_MODEL", "gpt-4o-mini")
MAX_NOTIFICATIONS_PER_DAY = int(os.getenv("MAX_NOTIFICATIONS_PER_DAY", "3"))
MAX_NOTIFICATIONS_PER_HOUR = int(os.getenv("MAX_NOTIFICATIONS_PER_HOUR", "1"))

client = AsyncOpenAI()


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class CandidateMessage:
    title: str
    body: str
    reward_score: float = 0.0
    generation_strategy: str = "llm"


@dataclass
class PipelineContext:
    """Assembled context passed through the pipeline."""
    user_id: str
    clv_tier: CLVTier
    composition_path: CompositionPath
    category_affinities: dict[str, float]
    notification_open_rate: float
    retrieved_keys: list[str] = field(default_factory=list)
    candidates: list[CandidateMessage] = field(default_factory=list)
    guardrails_applied: list[str] = field(default_factory=list)
    candidates_filtered: int = 0
    send_time_optimized: bool = False
    scheduled_at: datetime = field(default_factory=datetime.utcnow)


# ── 1. Budget Router ───────────────────────────────────────────────────────────

def route_budget(profile: UserProfileDB, options) -> tuple[CompositionPath, str]:
    """
    Maps CLV tier to a composition path.
    High-value users receive full LLM pipeline; low-value users receive templates.
    This implements the cost-benefit framework from Section 6 of the paper.
    """
    tier = CLVTier(options.override_clv_tier or profile.clv_tier or "bronze")

    if tier == CLVTier.platinum:
        path = CompositionPath.llm_full
        decision = f"CLV={tier.value} → LLM Full Pipeline (max personalisation)"
    elif tier == CLVTier.gold:
        path = CompositionPath.llm_full
        decision = f"CLV={tier.value} → LLM Full Pipeline (moderate context)"
    elif tier == CLVTier.silver:
        path = CompositionPath.llm_hybrid
        decision = f"CLV={tier.value} → LLM Hybrid (title only, template body)"
    else:
        path = CompositionPath.template
        decision = f"CLV={tier.value} → Template Path (cost-efficient)"

    return path, decision


# ── 2. Context Retriever ───────────────────────────────────────────────────────

def retrieve_context(
    request: ComposeRequest,
    profile: UserProfileDB,
    ctx: PipelineContext
) -> str:
    """
    Assembles a rich context string for the LLM prompt.
    Implements RAG-style retrieval from the user profile and content item.
    In production, this would query a vector store for similar items.
    """
    affinities = json.loads(profile.category_affinities_json or "{}")
    category = request.content_item.category

    # Top affinity categories
    top_cats = sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:3]
    top_cats_str = ", ".join(f"{c}({v:.2f})" for c, v in top_cats) if top_cats else "none"
    ctx.retrieved_keys.append(f"preference:{category}")

    # Notification history signal
    open_rate = profile.notification_open_rate or 0.0
    ctx.retrieved_keys.append(f"open_rate:{open_rate:.0%}")

    # Item affinity
    item_affinity = affinities.get(category, 0.0)
    ctx.retrieved_keys.append(f"item_affinity:{item_affinity:.2f}")

    # Weather context
    weather = request.trigger_context.weather_condition
    if weather:
        ctx.retrieved_keys.append(f"context:weather:{weather}")

    # Time context
    hour = request.trigger_context.local_hour
    time_label = _hour_to_label(hour)
    ctx.retrieved_keys.append(f"context:time:{time_label}")

    # Build context string
    attrs = request.content_item.attributes
    attrs_str = ", ".join(f"{k}: {v}" for k, v in attrs.items()) if attrs else "no attributes"

    context = f"""USER CONTEXT:
- Category affinity for '{category}': {item_affinity:.2f} (scale: -1 to 1, higher = stronger preference)
- Top interest categories: {top_cats_str}
- Historical notification open rate: {open_rate:.0%}
- CLV tier: {ctx.clv_tier.value}

CONTENT ITEM:
- Title: {request.content_item.title}
- Category: {category}
- Attributes: {attrs_str}

TRIGGER CONTEXT:
- Time of day: {time_label} ({hour}:00 local time)
- Day: {_day_to_label(request.trigger_context.day_of_week)}
- Weather: {weather or 'unknown'}
- Recent app open: {request.trigger_context.recent_app_open}

NOTIFICATION INTENT: {request.intent.value.replace('_', ' ').title()}
DOMAIN: {request.domain.value.replace('_', ' ').title()}"""

    return context


def _hour_to_label(hour: int) -> str:
    if 5 <= hour < 9: return "early morning"
    if 9 <= hour < 12: return "morning"
    if 12 <= hour < 14: return "lunchtime"
    if 14 <= hour < 17: return "afternoon"
    if 17 <= hour < 20: return "evening"
    if 20 <= hour < 23: return "night"
    return "late night"


def _day_to_label(dow: int) -> str:
    days = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday",
            5: "Thursday", 6: "Friday", 7: "Saturday"}
    return days.get(dow, "weekday")


# ── 3. Message Composer ────────────────────────────────────────────────────────

DOMAIN_TONE = {
    "social_media": "casual, engaging, FOMO-inducing, social proof",
    "food_delivery": "warm, appetising, time-sensitive, sensory",
    "e_commerce": "value-focused, urgency-appropriate, benefit-led",
}

INTENT_GUIDANCE = {
    "re_engagement": "Re-engage a lapsed user. Remind them what they are missing. Do NOT use false urgency.",
    "abandoned_cart": "The user left items in their cart. Gently remind them. Highlight value, not pressure.",
    "flash_sale": "Limited-time offer. Urgency is appropriate but must be factually accurate.",
    "recommendation": "Personalised recommendation based on their interests. Feel like a friend's suggestion.",
    "promotional_offer": "Highlight the offer clearly. Lead with the benefit.",
    "new_content": "Something new they will love based on their interests.",
    "social_activity": "A friend or connection did something. Make it feel personal and warm.",
    "order_update": "Factual order status update. Clear, reassuring, no marketing language.",
}


async def compose_candidates(
    request: ComposeRequest,
    context_str: str,
    ctx: PipelineContext,
    n: int = 5
) -> list[CandidateMessage]:
    """
    Generates N candidate notification messages using the LLM.
    For template path (bronze tier), returns a single template-filled message.
    """
    if ctx.composition_path == CompositionPath.template:
        return _compose_template(request)

    tone = DOMAIN_TONE.get(request.domain.value, "professional, clear")
    intent_guide = INTENT_GUIDANCE.get(request.intent.value, "Compose a helpful notification.")

    # For hybrid path, only generate the title via LLM
    if ctx.composition_path == CompositionPath.llm_hybrid:
        n = 3
        format_instruction = """Return ONLY a JSON array of objects with "title" and "body" keys.
The title should be LLM-composed (personalised, engaging, max 50 chars).
The body should be a clean template fill: use the item name and one key attribute."""
    else:
        format_instruction = """Return ONLY a JSON array of objects with "title" and "body" keys.
Each title: max 50 characters. Each body: max 120 characters.
Vary the style, angle, and emotional hook across candidates."""

    system_prompt = f"""You are NotifyCompose, an expert notification copywriter.
Your task: write {n} diverse push notification candidates for a {request.domain.value.replace('_', ' ')} app.

Tone: {tone}
Intent guidance: {intent_guide}

Rules:
1. NEVER fabricate facts not present in the context (no hallucinated prices, ratings, or claims).
2. NEVER use false urgency (e.g., "Only 1 left!" unless explicitly provided as an attribute).
3. NEVER use dark patterns (e.g., "You MUST act now or lose this forever").
4. Write naturally — avoid robotic slot-fill language like "Hello [User], your [Item] is ready."
5. Each candidate must have a distinct emotional angle or hook.
6. {format_instruction}"""

    user_prompt = f"""Context:
{context_str}

Generate {n} notification candidates. Return ONLY valid JSON."""

    try:
        response = await client.chat.completions.create(
            model=COMPOSE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.85,
            max_tokens=800,
            response_format={"type": "json_object"} if "gpt-4" in COMPOSE_MODEL else None,
        )

        raw = response.choices[0].message.content.strip()
        # Handle both {"notifications": [...]} and [...] formats
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            candidates_data = parsed.get("notifications", parsed.get("candidates",
                             parsed.get("messages", list(parsed.values())[0])))
        else:
            candidates_data = parsed

        candidates = []
        for item in candidates_data[:n]:
            title = str(item.get("title", "")).strip()
            body = str(item.get("body", "")).strip()
            if title and body:
                candidates.append(CandidateMessage(
                    title=title[:100],
                    body=body[:300],
                    generation_strategy="llm"
                ))

        if not candidates:
            return _compose_template(request)

        return candidates

    except Exception as e:
        # Fallback to template on any LLM error
        print(f"[Composer] LLM error: {e}. Falling back to template.")
        return _compose_template(request)


def _compose_template(request: ComposeRequest) -> list[CandidateMessage]:
    """
    Template-based composition for bronze tier users or LLM fallback.
    Uses simple slot-filling with the content item attributes.
    """
    item = request.content_item
    attrs = item.attributes
    domain = request.domain
    intent = request.intent

    templates = {
        ("food_delivery", "re_engagement"): (
            f"Hungry? {item.title} is waiting 🍽️",
            f"Order {item.title} from {attrs.get('restaurant', 'your favourite spot')}. "
            f"Delivery in {attrs.get('deliveryTime', '30 min')}."
        ),
        ("food_delivery", "recommendation"): (
            f"You might love: {item.title}",
            f"Rated {attrs.get('rating', '4.5')}★ · {attrs.get('deliveryTime', '25 min')} delivery · "
            f"{attrs.get('price', '')}"
        ),
        ("e_commerce", "abandoned_cart"): (
            f"Still thinking about {item.title}?",
            f"Your cart is waiting. {item.title} — {attrs.get('price', '')}. "
            f"Complete your order before it sells out."
        ),
        ("e_commerce", "flash_sale"): (
            f"Flash Sale: {item.title} {attrs.get('discount', '')} off",
            f"{item.title} is on sale now. {attrs.get('price', '')}. Limited time offer."
        ),
        ("social_media", "new_content"): (
            f"New from {attrs.get('creator', 'someone you follow')}",
            f"{item.title} — {attrs.get('views', '')} views. Check it out now."
        ),
        ("social_media", "social_activity"): (
            f"{attrs.get('friend', 'Someone you follow')} liked this",
            f"\"{item.title}\" is trending in your network."
        ),
    }

    key = (domain.value, intent.value)
    if key in templates:
        title, body = templates[key]
    else:
        title = f"Check out {item.title}"
        body = f"{item.title} — {', '.join(f'{v}' for v in attrs.values()[:2]) if attrs else 'available now'}."

    return [CandidateMessage(title=title, body=body, generation_strategy="template")]


# ── 4. Guardrail Filter ────────────────────────────────────────────────────────

# Prohibited patterns (false urgency, dark patterns, hallucination triggers)
PROHIBITED_PATTERNS = [
    (r"\bonly\s+\d+\s+left\b", "false_scarcity"),
    (r"\bexpires?\s+in\s+\d+\s+minutes?\b", "false_urgency_timer"),
    (r"\byou\s+will\s+lose\b", "loss_aversion_dark_pattern"),
    (r"\blast\s+chance\b", "false_urgency"),
    (r"\bact\s+now\s+or\b", "coercive_language"),
    (r"\b(free|win|winner|prize|congratulations)\b", "potential_spam_language"),
    (r"\b\$\d+\s+off\b(?!.*\battributes?\b)", "unverified_discount_claim"),
]

MAX_TITLE_LENGTH = 100
MAX_BODY_LENGTH = 300


def apply_guardrails(
    candidates: list[CandidateMessage],
    request: ComposeRequest,
    ctx: PipelineContext
) -> list[CandidateMessage]:
    """
    Filters candidates that violate factuality or policy rules.
    Implements the Factuality & Policy Guard from the pipeline (Figure 2).
    """
    passed = []
    for candidate in candidates:
        violations = []
        full_text = f"{candidate.title} {candidate.body}".lower()

        # Length check
        if len(candidate.title) > MAX_TITLE_LENGTH:
            violations.append("title_too_long")
        if len(candidate.body) > MAX_BODY_LENGTH:
            violations.append("body_too_long")

        # Prohibited pattern check
        for pattern, label in PROHIBITED_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                # Allow if the claim is backed by attributes
                attr_values = " ".join(request.content_item.attributes.values()).lower()
                if not any(word in attr_values for word in ["left", "expires", "off", "free"]):
                    violations.append(label)

        if violations:
            ctx.candidates_filtered += 1
            ctx.guardrails_applied.extend(v for v in violations if v not in ctx.guardrails_applied)
        else:
            passed.append(candidate)

    ctx.guardrails_applied.append("length_check")
    ctx.guardrails_applied.append("prohibited_pattern_check")

    # If all candidates filtered, fall back to template
    if not passed:
        fallback = _compose_template(request)
        ctx.guardrails_applied.append("fallback_to_template")
        return fallback

    return passed


# ── 5. Reward Ranker ───────────────────────────────────────────────────────────

async def rank_candidates(
    candidates: list[CandidateMessage],
    request: ComposeRequest,
    ctx: PipelineContext
) -> list[CandidateMessage]:
    """
    Scores and ranks candidates using a heuristic reward model.
    For platinum/gold users, uses LLM-based pairwise scoring.
    For silver/bronze, uses fast heuristic scoring.

    Implements the Pairwise Reward Model from Section 4.3 of the paper.
    """
    if len(candidates) == 1:
        candidates[0].reward_score = 0.75
        return candidates

    if ctx.clv_tier in (CLVTier.platinum, CLVTier.gold):
        return await _llm_reward_rank(candidates, request, ctx)
    else:
        return _heuristic_reward_rank(candidates, request, ctx)


async def _llm_reward_rank(
    candidates: list[CandidateMessage],
    request: ComposeRequest,
    ctx: PipelineContext
) -> list[CandidateMessage]:
    """LLM-based reward scoring using pairwise comparison."""
    try:
        candidates_str = "\n".join(
            f"[{i+1}] Title: {c.title}\n    Body: {c.body}"
            for i, c in enumerate(candidates)
        )

        prompt = f"""You are a notification quality judge. Score each notification candidate from 0.0 to 1.0.

Scoring criteria:
- Relevance to user context and intent (0.3 weight)
- Naturalness and engagement (0.3 weight)
- Clarity and actionability (0.2 weight)
- Absence of dark patterns or false urgency (0.2 weight)

Domain: {request.domain.value.replace('_', ' ')}
Intent: {request.intent.value.replace('_', ' ')}
Item: {request.content_item.title}

Candidates:
{candidates_str}

Return ONLY a JSON array of scores in order, e.g.: [0.82, 0.71, 0.65, 0.78, 0.55]"""

        response = await client.chat.completions.create(
            model=REWARD_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
        )

        raw = response.choices[0].message.content.strip()
        # Extract JSON array
        match = re.search(r'\[[\d.,\s]+\]', raw)
        if match:
            scores = json.loads(match.group())
            for i, candidate in enumerate(candidates):
                if i < len(scores):
                    candidate.reward_score = float(scores[i])

        candidates.sort(key=lambda c: c.reward_score, reverse=True)
        return candidates

    except Exception:
        return _heuristic_reward_rank(candidates, request, ctx)


def _heuristic_reward_rank(
    candidates: list[CandidateMessage],
    request: ComposeRequest,
    ctx: PipelineContext
) -> list[CandidateMessage]:
    """
    Fast heuristic reward scoring based on:
    - Title length (optimal: 30–50 chars)
    - Body length (optimal: 60–120 chars)
    - Presence of item name (relevance)
    - Presence of action words (engagement)
    - Absence of prohibited words (safety)
    """
    action_words = {"now", "today", "new", "just", "check", "see", "get", "try",
                    "discover", "explore", "back", "ready", "waiting", "available"}
    item_words = set(request.content_item.title.lower().split())

    for candidate in candidates:
        score = 0.5  # base

        # Title length score
        tl = len(candidate.title)
        if 25 <= tl <= 50:
            score += 0.15
        elif tl < 15 or tl > 70:
            score -= 0.1

        # Body length score
        bl = len(candidate.body)
        if 60 <= bl <= 120:
            score += 0.1
        elif bl < 30 or bl > 200:
            score -= 0.05

        # Item name presence
        title_words = set(candidate.title.lower().split())
        if title_words & item_words:
            score += 0.1

        # Action word presence
        body_words = set(candidate.body.lower().split())
        if body_words & action_words:
            score += 0.05

        # Penalise all-caps words (shouting)
        if re.search(r'\b[A-Z]{4,}\b', candidate.title):
            score -= 0.1

        # Penalise excessive punctuation
        if candidate.title.count('!') > 1 or candidate.body.count('!') > 2:
            score -= 0.05

        candidate.reward_score = round(max(0.0, min(1.0, score)), 3)

    candidates.sort(key=lambda c: c.reward_score, reverse=True)
    return candidates


# ── 6. Frequency Capper ────────────────────────────────────────────────────────

async def check_frequency_cap(user_id: str, db: AsyncSession) -> tuple[bool, str]:
    """
    Enforces max-touch rules per user.
    Returns (is_capped, reason).
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)

    # Count notifications in last hour
    result_hour = await db.execute(
        select(func.count(NotificationLogDB.notification_id))
        .where(NotificationLogDB.user_id == user_id)
        .where(NotificationLogDB.created_at >= one_hour_ago)
    )
    count_hour = result_hour.scalar() or 0

    if count_hour >= MAX_NOTIFICATIONS_PER_HOUR:
        return True, f"Frequency cap: {count_hour} notifications sent in the last hour (max={MAX_NOTIFICATIONS_PER_HOUR})"

    # Count notifications in last 24 hours
    result_day = await db.execute(
        select(func.count(NotificationLogDB.notification_id))
        .where(NotificationLogDB.user_id == user_id)
        .where(NotificationLogDB.created_at >= one_day_ago)
    )
    count_day = result_day.scalar() or 0

    if count_day >= MAX_NOTIFICATIONS_PER_DAY:
        return True, f"Frequency cap: {count_day} notifications sent in the last 24 hours (max={MAX_NOTIFICATIONS_PER_DAY})"

    return False, ""


# ── 7. Send-Time Optimizer ─────────────────────────────────────────────────────

def optimize_send_time(profile: UserProfileDB, trigger_hour: int) -> tuple[datetime, bool]:
    """
    Thompson Sampling bandit for send-time optimization.
    Samples from Beta(alpha, beta) for each hour and picks the argmax.

    Implements Section 4.4 of the paper.
    """
    try:
        bandit_state = json.loads(profile.sto_bandit_state_json or "[]")
        if not bandit_state:
            return _schedule_at_hour(trigger_hour), False

        # Thompson Sampling: draw from Beta distribution for each hour
        samples = []
        for entry in bandit_state:
            alpha = entry.get("alpha", 1.0)
            beta = entry.get("beta", 1.0)
            # Sample from Beta distribution using numpy-free approximation
            sample = _beta_sample(alpha, beta)
            samples.append((entry["hour"], sample))

        # Select hour with highest sample
        best_hour = max(samples, key=lambda x: x[1])[0]

        # Only override if the optimal hour is meaningfully different from trigger
        if abs(best_hour - trigger_hour) <= 1:
            return _schedule_at_hour(trigger_hour), False

        return _schedule_at_hour(best_hour), True

    except Exception:
        return _schedule_at_hour(trigger_hour), False


def _beta_sample(alpha: float, beta: float) -> float:
    """Approximate Beta sample using the ratio of Gamma samples."""
    # Use Python's random.gammavariate (available without numpy)
    x = random.gammavariate(alpha, 1.0)
    y = random.gammavariate(beta, 1.0)
    if x + y == 0:
        return 0.5
    return x / (x + y)


def _schedule_at_hour(hour: int) -> datetime:
    """Schedule for the next occurrence of the given hour."""
    now = datetime.utcnow()
    scheduled = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if scheduled <= now:
        scheduled += timedelta(days=1)
    return scheduled
