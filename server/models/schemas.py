"""
schemas.py — Pydantic request/response models for the NotifyCompose API.
These mirror the Swift models in the iOS SDK exactly.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class CLVTier(str, Enum):
    platinum = "platinum"
    gold = "gold"
    silver = "silver"
    bronze = "bronze"


class NotificationDomain(str, Enum):
    social_media = "social_media"
    food_delivery = "food_delivery"
    e_commerce = "e_commerce"


class NotificationIntent(str, Enum):
    re_engagement = "re_engagement"
    new_content = "new_content"
    promotional_offer = "promotional_offer"
    abandoned_cart = "abandoned_cart"
    order_update = "order_update"
    social_activity = "social_activity"
    recommendation = "recommendation"
    flash_sale = "flash_sale"


class CompositionPath(str, Enum):
    llm_full = "LLM Full Pipeline"
    llm_hybrid = "LLM Hybrid (Title only)"
    template = "Template Path"
    blocked = "Blocked by Guardrail"
    frequency_capped = "Frequency Capped"


class FeedbackOutcome(str, Enum):
    opened = "opened"
    dismissed = "dismissed"
    converted = "converted"
    unsubscribed = "unsubscribed"


class SignalType(str, Enum):
    screen_view = "screen_view"
    item_click = "item_click"
    purchase = "purchase"
    share = "share"
    save = "save"
    dismiss = "dismiss"
    app_foreground = "app_foreground"
    app_background = "app_background"
    notification_received = "notification_received"
    notification_opened = "notification_opened"
    notification_dismissed = "notification_dismissed"
    notification_converted = "notification_converted"


# ── Signal Ingestion ───────────────────────────────────────────────────────────

class UserSignal(BaseModel):
    type: SignalType
    item_id: Optional[str] = None
    category: Optional[str] = None
    duration_seconds: Optional[float] = None
    notification_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeviceContext(BaseModel):
    timezone: str = "UTC"
    locale: str = "en_US"
    network_type: str = "wifi"
    app_version: Optional[str] = None


class SignalBatch(BaseModel):
    user_id: str
    signals: list[UserSignal]
    device_context: DeviceContext = Field(default_factory=DeviceContext)


class SignalResponse(BaseModel):
    status: str
    signals_ingested: int


# ── Compose Request ────────────────────────────────────────────────────────────

class ContentItem(BaseModel):
    item_id: str
    title: str
    category: str
    attributes: dict[str, str] = Field(default_factory=dict)
    image_url: Optional[str] = None


class TriggerContext(BaseModel):
    local_hour: int = Field(default=12, ge=0, le=23)
    day_of_week: int = Field(default=3, ge=1, le=7)
    weather_condition: Optional[str] = None
    recent_app_open: bool = False
    network_type: str = "wifi"


class PipelineOptions(BaseModel):
    max_candidates: int = Field(default=5, ge=1, le=10)
    max_title_length: int = Field(default=50, ge=20, le=100)
    max_body_length: int = Field(default=120, ge=50, le=300)
    enable_guardrails: bool = True
    enable_frequency_cap: bool = True
    enable_send_time_optimization: bool = True
    override_clv_tier: Optional[CLVTier] = None


class ComposeRequest(BaseModel):
    user_id: str
    domain: NotificationDomain
    intent: NotificationIntent
    content_item: ContentItem
    trigger_context: TriggerContext = Field(default_factory=TriggerContext)
    options: PipelineOptions = Field(default_factory=PipelineOptions)


# ── Compose Response ───────────────────────────────────────────────────────────

class PipelineTrace(BaseModel):
    budget_decision: str
    retrieved_context_keys: list[str] = Field(default_factory=list)
    candidates_generated: int = 0
    guardrails_applied: list[str] = Field(default_factory=list)
    candidates_filtered: int = 0
    winning_candidate_rank: int = 1
    send_time_optimized: bool = False
    latency_ms: float = 0.0


class ComposeResponse(BaseModel):
    notification_id: str
    title: str
    body: str
    scheduled_at: datetime
    composition_path: CompositionPath
    reward_score: float = Field(ge=0.0, le=1.0)
    pipeline_trace: PipelineTrace
    metadata: dict[str, str] = Field(default_factory=dict)


# ── Feedback ───────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    notification_id: str
    user_id: str
    outcome: FeedbackOutcome
    opened_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None


class FeedbackResponse(BaseModel):
    status: str
    message: str


# ── User Profile (internal, also returned by /debug/profile) ──────────────────

class UserProfileResponse(BaseModel):
    user_id: str
    clv_tier: CLVTier
    clv_score: float
    category_affinities: dict[str, float]
    notification_open_rate: float
    total_purchases: int
    preferred_send_hours: list[int]
    last_active: Optional[datetime]
