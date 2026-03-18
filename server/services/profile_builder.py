"""
profile_builder.py — Builds and updates UserProfile from raw signals.

Implements:
  - Exponential time-decay affinity scoring (Section 4.1 of the paper)
  - CLV tier computation from purchase history
  - Notification open rate tracking
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import UserProfileDB, UserSignalDB, NotificationLogDB
from models.schemas import CLVTier, UserProfileResponse

import os
AFFINITY_DECAY_RATE = float(os.getenv("AFFINITY_DECAY_RATE", "0.1"))

# Action weights for affinity scoring
ACTION_WEIGHTS = {
    "purchase": 1.0,
    "save": 0.6,
    "share": 0.5,
    "item_click": 0.4,
    "screen_view": 0.2,
    "dismiss": -0.3,
    "notification_dismissed": -0.1,
}

CLV_PLATINUM = float(os.getenv("CLV_PLATINUM_THRESHOLD", "95"))
CLV_GOLD = float(os.getenv("CLV_GOLD_THRESHOLD", "80"))
CLV_SILVER = float(os.getenv("CLV_SILVER_THRESHOLD", "50"))


async def get_or_create_profile(user_id: str, db: AsyncSession) -> UserProfileDB:
    """Fetch existing profile or create a blank one."""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserProfileDB(
            user_id=user_id,
            category_affinities_json="{}",
            sto_bandit_state_json=json.dumps(_init_bandit_state()),
        )
        db.add(profile)
        await db.flush()
    return profile


async def update_profile_from_signals(
    user_id: str,
    signals: list[dict],
    db: AsyncSession
) -> UserProfileDB:
    """
    Process a batch of new signals and update the user profile.
    Called by the signal ingestion route after writing raw signals to DB.
    """
    profile = await get_or_create_profile(user_id, db)
    affinities: dict[str, float] = json.loads(profile.category_affinities_json or "{}")
    bandit_state: list[dict] = json.loads(profile.sto_bandit_state_json or "[]")
    if not bandit_state:
        bandit_state = _init_bandit_state()

    now = datetime.utcnow()

    for signal in signals:
        signal_type = signal.get("type", "")
        category = signal.get("category")
        timestamp_str = signal.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else now
        days_ago = max(0.0, (now - timestamp.replace(tzinfo=None)).total_seconds() / 86400.0)

        # Update category affinity with time-decay
        if category and signal_type in ACTION_WEIGHTS:
            weight = ACTION_WEIGHTS[signal_type]
            decay = math.exp(-AFFINITY_DECAY_RATE * days_ago)
            current = affinities.get(category, 0.0)
            affinities[category] = max(-1.0, min(1.0, current + weight * decay))

        # Track purchases for CLV
        if signal_type == "purchase":
            profile.total_purchases = (profile.total_purchases or 0) + 1

        # Update STO bandit on notification feedback
        hour = timestamp.hour
        if signal_type == "notification_opened":
            bandit_state = _update_bandit(bandit_state, hour, reward=1)
            profile.total_notifications_opened = (profile.total_notifications_opened or 0) + 1
        elif signal_type == "notification_dismissed":
            bandit_state = _update_bandit(bandit_state, hour, reward=0)

        # Update last active
        if signal_type in ("screen_view", "item_click", "purchase", "app_foreground"):
            profile.last_active = now

    # Recompute CLV score and tier
    profile.clv_score = _compute_clv_score(profile)
    profile.clv_tier = _compute_clv_tier(profile.clv_score).value

    # Recompute open rate
    total_sent = profile.total_notifications_sent or 0
    total_opened = profile.total_notifications_opened or 0
    profile.notification_open_rate = (total_opened / total_sent) if total_sent > 0 else 0.0

    # Persist
    profile.category_affinities_json = json.dumps(affinities)
    profile.sto_bandit_state_json = json.dumps(bandit_state)
    profile.updated_at = now

    await db.commit()
    await db.refresh(profile)
    return profile


def _compute_clv_score(profile: UserProfileDB) -> float:
    """
    Simplified CLV score. In production, replace with a trained regression model.
    Score = purchases × open_rate_bonus × recency_bonus
    """
    purchases = profile.total_purchases or 0
    open_rate = profile.notification_open_rate or 0.0
    base = purchases * 10.0
    engagement_bonus = open_rate * 20.0
    return round(min(100.0, base + engagement_bonus), 2)


def _compute_clv_tier(clv_score: float) -> CLVTier:
    """Map CLV score (0–100) to a tier using configurable percentile thresholds."""
    if clv_score >= CLV_PLATINUM:
        return CLVTier.platinum
    elif clv_score >= CLV_GOLD:
        return CLVTier.gold
    elif clv_score >= CLV_SILVER:
        return CLVTier.silver
    return CLVTier.bronze


def _init_bandit_state() -> list[dict]:
    """Initialise Thompson Sampling Beta priors for each hour of the day."""
    return [{"hour": h, "alpha": 1.0, "beta": 1.0} for h in range(24)]


def _update_bandit(state: list[dict], hour: int, reward: int) -> list[dict]:
    """Update Beta distribution parameters for the given hour."""
    for entry in state:
        if entry["hour"] == hour:
            if reward == 1:
                entry["alpha"] += 1
            else:
                entry["beta"] += 1
            break
    return state


async def get_profile_response(user_id: str, db: AsyncSession) -> Optional[UserProfileResponse]:
    """Return a UserProfileResponse for the debug endpoint."""
    profile = await get_or_create_profile(user_id, db)
    affinities = json.loads(profile.category_affinities_json or "{}")
    bandit_state = json.loads(profile.sto_bandit_state_json or "[]")

    # Top 3 preferred send hours by expected CTR (alpha / (alpha + beta))
    if bandit_state:
        sorted_hours = sorted(
            bandit_state,
            key=lambda x: x["alpha"] / (x["alpha"] + x["beta"]),
            reverse=True
        )
        preferred_hours = [h["hour"] for h in sorted_hours[:3]]
    else:
        preferred_hours = [12, 18, 9]

    return UserProfileResponse(
        user_id=profile.user_id,
        clv_tier=CLVTier(profile.clv_tier or "bronze"),
        clv_score=profile.clv_score or 0.0,
        category_affinities=affinities,
        notification_open_rate=profile.notification_open_rate or 0.0,
        total_purchases=profile.total_purchases or 0,
        preferred_send_hours=preferred_hours,
        last_active=profile.last_active,
    )
