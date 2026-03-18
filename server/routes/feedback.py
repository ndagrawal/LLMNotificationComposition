"""
feedback.py — Notification feedback and debug routes.
POST /api/v1/feedback — records notification outcomes (open/dismiss/convert).
GET  /api/v1/debug/profile/{user_id} — returns the current user profile state.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db, NotificationLogDB, UserProfileDB
from models.schemas import (
    FeedbackRequest, FeedbackResponse, FeedbackOutcome, UserProfileResponse
)
from services.profile_builder import get_profile_response, update_profile_from_signals

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def record_feedback(
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a notification outcome from the iOS SDK.

    This closes the online learning feedback loop:
    - opened / converted → positive reward signal → STO bandit alpha++
    - dismissed / unsubscribed → negative reward signal → STO bandit beta++

    The signal is processed via the same signal ingestion pipeline,
    which updates the user's STO bandit state and reward model inputs.
    """
    # Update notification log
    result = await db.execute(
        select(NotificationLogDB).where(
            NotificationLogDB.notification_id == feedback.notification_id
        )
    )
    log = result.scalar_one_or_none()

    if log:
        if feedback.outcome == FeedbackOutcome.opened and feedback.opened_at:
            log.opened_at = feedback.opened_at
        elif feedback.outcome == FeedbackOutcome.converted:
            log.opened_at = feedback.opened_at or datetime.utcnow()
            log.converted_at = feedback.converted_at or datetime.utcnow()
        elif feedback.outcome == FeedbackOutcome.dismissed:
            log.dismissed_at = datetime.utcnow()

    # Translate feedback outcome to a signal for profile update
    signal_type_map = {
        FeedbackOutcome.opened: "notification_opened",
        FeedbackOutcome.converted: "notification_converted",
        FeedbackOutcome.dismissed: "notification_dismissed",
        FeedbackOutcome.unsubscribed: "notification_dismissed",
    }

    signal = {
        "type": signal_type_map[feedback.outcome],
        "notification_id": feedback.notification_id,
        "timestamp": (feedback.opened_at or datetime.utcnow()).isoformat(),
    }

    await update_profile_from_signals(feedback.user_id, [signal], db)

    return FeedbackResponse(
        status="ok",
        message=f"Feedback recorded: {feedback.outcome.value} for notification {feedback.notification_id}"
    )


@router.get("/debug/profile/{user_id}", response_model=UserProfileResponse, tags=["Debug"])
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint: returns the current aggregated user profile.
    Shows CLV tier, category affinities, open rate, and preferred send hours.
    Useful for verifying that signal ingestion is working correctly.
    """
    profile = await get_profile_response(user_id, db)
    if not profile:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return profile


@router.get("/debug/notifications/{user_id}", tags=["Debug"])
async def get_notification_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint: returns the notification history for a user.
    Shows all composed notifications with their outcomes.
    """
    result = await db.execute(
        select(NotificationLogDB)
        .where(NotificationLogDB.user_id == user_id)
        .order_by(NotificationLogDB.created_at.desc())
        .limit(20)
    )
    logs = result.scalars().all()

    return {
        "user_id": user_id,
        "total": len(logs),
        "notifications": [
            {
                "notification_id": log.notification_id,
                "domain": log.domain,
                "intent": log.intent,
                "title": log.title,
                "body": log.body,
                "composition_path": log.composition_path,
                "reward_score": log.reward_score,
                "scheduled_at": log.scheduled_at.isoformat() if log.scheduled_at else None,
                "opened": log.opened_at is not None,
                "converted": log.converted_at is not None,
                "dismissed": log.dismissed_at is not None,
            }
            for log in logs
        ]
    }
