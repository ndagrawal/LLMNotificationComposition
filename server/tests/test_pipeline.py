"""
test_pipeline.py — Integration tests for the NotifyCompose pipeline.

Run with:
  pytest tests/ -v

These tests use an in-memory SQLite database and mock the OpenAI API
so they run without a real API key.
"""
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "test-key"

from main import app
from db.database import Base, engine, get_db, AsyncSessionLocal


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables in the in-memory test database before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Mock LLM response ──────────────────────────────────────────────────────────

MOCK_LLM_CANDIDATES = json.dumps([
    {"title": "Rainy evening? Tony's Margherita is 25 min away", "body": "Your go-to Italian spot has a 4.8-star special tonight. Order now."},
    {"title": "Perfect pizza night incoming 🍕", "body": "Tony's Margherita Pizza — rated 4.8 stars. Delivered in 25 min for $12.99."},
    {"title": "Your favourite pizza is calling", "body": "Margherita Pizza from Tony's. 4.8 stars, $12.99, 25 min delivery."},
])

def make_mock_openai_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "NotifyCompose API"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSignalIngestion:
    @pytest.mark.asyncio
    async def test_ingest_signals_creates_profile(self, client):
        payload = {
            "user_id": "test_user_001",
            "signals": [
                {
                    "type": "screen_view",
                    "item_id": "pizza_001",
                    "category": "food/italian",
                    "duration_seconds": 12.5,
                    "timestamp": "2026-03-18T18:30:00Z"
                },
                {
                    "type": "purchase",
                    "item_id": "pizza_001",
                    "category": "food/italian",
                    "timestamp": "2026-03-18T18:31:00Z"
                }
            ],
            "device_context": {
                "timezone": "America/Los_Angeles",
                "locale": "en_US",
                "network_type": "wifi"
            }
        }
        response = await client.post("/api/v1/signals", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["signals_ingested"] == 2

    @pytest.mark.asyncio
    async def test_profile_updated_after_signals(self, client):
        # Send purchase signals to build up CLV
        for i in range(12):
            await client.post("/api/v1/signals", json={
                "user_id": "test_user_002",
                "signals": [{"type": "purchase", "item_id": f"item_{i}",
                              "category": "electronics", "timestamp": "2026-03-18T12:00:00Z"}],
                "device_context": {}
            })

        # Check profile
        response = await client.get("/api/v1/debug/profile/test_user_002")
        assert response.status_code == 200
        profile = response.json()
        assert profile["total_purchases"] == 12
        assert "electronics" in profile["category_affinities"]


class TestComposePipeline:
    @pytest.mark.asyncio
    async def test_compose_template_path_bronze_user(self, client):
        """Bronze tier users should receive template-composed notifications."""
        payload = {
            "user_id": "bronze_user_001",
            "domain": "food_delivery",
            "intent": "re_engagement",
            "content_item": {
                "item_id": "pizza_margherita",
                "title": "Margherita Pizza",
                "category": "food/italian",
                "attributes": {"price": "$12.99", "rating": "4.8", "deliveryTime": "25 min", "restaurant": "Tony's Pizza"}
            },
            "trigger_context": {"local_hour": 18, "day_of_week": 3},
            "options": {"override_clv_tier": "bronze", "enable_frequency_cap": False}
        }
        response = await client.post("/api/v1/compose", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] != ""
        assert data["body"] != ""
        assert data["composition_path"] == "Template Path"
        assert data["reward_score"] >= 0.0

    @pytest.mark.asyncio
    @patch("services.pipeline_services.client")
    async def test_compose_llm_full_path_platinum_user(self, mock_openai, client):
        """Platinum tier users should receive LLM-composed notifications."""
        mock_openai.chat.completions.create = AsyncMock(
            return_value=make_mock_openai_response(MOCK_LLM_CANDIDATES)
        )

        payload = {
            "user_id": "platinum_user_001",
            "domain": "food_delivery",
            "intent": "re_engagement",
            "content_item": {
                "item_id": "pizza_margherita",
                "title": "Margherita Pizza",
                "category": "food/italian",
                "attributes": {"price": "$12.99", "rating": "4.8", "deliveryTime": "25 min", "restaurant": "Tony's Pizza"}
            },
            "trigger_context": {"local_hour": 18, "day_of_week": 3, "weather_condition": "rainy"},
            "options": {"override_clv_tier": "platinum", "enable_frequency_cap": False, "max_candidates": 3}
        }
        response = await client.post("/api/v1/compose", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["composition_path"] == "LLM Full Pipeline"
        assert len(data["title"]) <= 50
        assert data["pipeline_trace"]["candidates_generated"] >= 1

    @pytest.mark.asyncio
    async def test_frequency_cap_enforced(self, client):
        """After max daily notifications, further requests should be capped."""
        user_id = "freq_cap_test_user"
        payload = {
            "user_id": user_id,
            "domain": "e_commerce",
            "intent": "flash_sale",
            "content_item": {"item_id": "item_001", "title": "Test Item", "category": "electronics", "attributes": {}},
            "trigger_context": {},
            "options": {"override_clv_tier": "bronze", "enable_frequency_cap": True}
        }

        # Send MAX_NOTIFICATIONS_PER_DAY (3) notifications
        for _ in range(3):
            r = await client.post("/api/v1/compose", json=payload)
            assert r.status_code == 200

        # 4th request should be frequency capped
        response = await client.post("/api/v1/compose", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["composition_path"] == "Frequency Capped"


class TestFeedbackLoop:
    @pytest.mark.asyncio
    async def test_feedback_updates_profile(self, client):
        """Notification open feedback should update the STO bandit state."""
        user_id = "feedback_test_user"

        # First compose a notification to get an ID
        compose_payload = {
            "user_id": user_id,
            "domain": "social_media",
            "intent": "new_content",
            "content_item": {"item_id": "post_001", "title": "Viral Video", "category": "entertainment", "attributes": {}},
            "trigger_context": {"local_hour": 9},
            "options": {"override_clv_tier": "bronze", "enable_frequency_cap": False}
        }
        compose_response = await client.post("/api/v1/compose", json=compose_payload)
        notification_id = compose_response.json()["notification_id"]

        # Send feedback
        feedback_payload = {
            "notification_id": notification_id,
            "user_id": user_id,
            "outcome": "opened",
            "opened_at": "2026-03-18T09:05:00Z"
        }
        feedback_response = await client.post("/api/v1/feedback", json=feedback_payload)
        assert feedback_response.status_code == 200
        assert feedback_response.json()["status"] == "ok"

        # Verify profile open rate updated
        profile_response = await client.get(f"/api/v1/debug/profile/{user_id}")
        profile = profile_response.json()
        assert profile["notification_open_rate"] > 0.0
