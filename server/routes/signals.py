"""
signals.py — Signal ingestion route.
POST /api/v1/signals — receives batched user signals from the iOS SDK.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db, UserSignalDB
from models.schemas import SignalBatch, SignalResponse
from services.profile_builder import update_profile_from_signals

router = APIRouter()


@router.post("/signals", response_model=SignalResponse, tags=["Signals"])
async def ingest_signals(batch: SignalBatch, db: AsyncSession = Depends(get_db)):
    """
    Receive a batch of user signals from the iOS SDK.

    Signals are:
    1. Written to the raw signal store (user_signals table)
    2. Used to update the user's aggregated profile (category affinities, CLV, STO bandit)

    The iOS SDK batches signals every 30 seconds to minimise network overhead.
    """
    # Write raw signals to DB
    for signal in batch.signals:
        db_signal = UserSignalDB(
            user_id=batch.user_id,
            signal_type=signal.type.value,
            item_id=signal.item_id,
            category=signal.category,
            duration_seconds=signal.duration_seconds,
            notification_id=signal.notification_id,
            metadata_json=str(signal.metadata),
            timezone=batch.device_context.timezone,
            locale=batch.device_context.locale,
            timestamp=signal.timestamp,
        )
        db.add(db_signal)

    await db.flush()

    # Update aggregated profile
    signals_dicts = [s.model_dump() for s in batch.signals]
    await update_profile_from_signals(batch.user_id, signals_dicts, db)

    return SignalResponse(status="ok", signals_ingested=len(batch.signals))
