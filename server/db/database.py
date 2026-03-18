"""
database.py — SQLAlchemy async database setup and ORM models.
Uses SQLite for local development; swap DATABASE_URL for PostgreSQL in production.
"""
from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, JSON
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./notifycompose.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── ORM Models ─────────────────────────────────────────────────────────────────

class UserSignalDB(Base):
    """Raw signal events from the iOS SDK."""
    __tablename__ = "user_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    signal_type = Column(String(64), nullable=False)
    item_id = Column(String(256), nullable=True)
    category = Column(String(256), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    notification_id = Column(String(128), nullable=True)
    metadata_json = Column(Text, default="{}")
    timezone = Column(String(64), default="UTC")
    locale = Column(String(32), default="en_US")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class UserProfileDB(Base):
    """Aggregated user profile — updated on every signal batch."""
    __tablename__ = "user_profiles"

    user_id = Column(String(128), primary_key=True)
    clv_tier = Column(String(32), default="bronze")
    clv_score = Column(Float, default=0.0)
    # JSON-serialised dict: category → affinity score
    category_affinities_json = Column(Text, default="{}")
    # JSON-serialised list of (hour, alpha, beta) for STO bandit
    sto_bandit_state_json = Column(Text, default="[]")
    notification_open_rate = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    total_notifications_sent = Column(Integer, default=0)
    total_notifications_opened = Column(Integer, default=0)
    last_active = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationLogDB(Base):
    """Log of every composed notification — used for frequency capping and reward model updates."""
    __tablename__ = "notification_log"

    notification_id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False, index=True)
    domain = Column(String(64), nullable=False)
    intent = Column(String(64), nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    composition_path = Column(String(64), nullable=False)
    reward_score = Column(Float, default=0.0)
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    pipeline_trace_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Session Dependency ─────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
