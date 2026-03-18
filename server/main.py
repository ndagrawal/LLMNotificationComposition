"""
main.py — NotifyCompose FastAPI Server

LLM-Based Intelligent Notification Composition
Implements the full pipeline from the paper:
  "LLM-Based Intelligent Notification Composition: From Static Personalization
   to Context-Aware Persuasive Messaging" — Nilesh Agrawal (2026)

Usage:
  uvicorn main:app --reload --port 8000

API Docs:
  http://localhost:8000/docs   (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)
"""
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routes.signals import router as signals_router
from routes.compose import router as compose_router
from routes.feedback import router as feedback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database on startup."""
    await init_db()
    print("✅ NotifyCompose server started. Database initialised.")
    print("📖 API docs: http://localhost:8000/docs")
    yield
    print("🛑 NotifyCompose server shutting down.")


app = FastAPI(
    title="NotifyCompose API",
    description="""
## LLM-Based Intelligent Notification Composition

This server implements the full pipeline from the research paper:
**"LLM-Based Intelligent Notification Composition: From Static Personalization to Context-Aware Persuasive Messaging"**
by Nilesh Agrawal (2026).

### Pipeline Stages
1. **Signal Ingestion** — iOS SDK sends batched user signals (views, clicks, purchases)
2. **Profile Building** — Signals are aggregated into user profiles (CLV, affinities, STO bandit state)
3. **Composition** — Full 7-stage pipeline: Frequency Cap → Budget Router → Context Retrieval → LLM Composer → Guardrails → Reward Ranker → Send-Time Optimizer
4. **Feedback Loop** — Notification outcomes (open/dismiss/convert) close the online learning loop

### Supported Domains
- 📱 **Social Media** — Re-engagement, new content, social activity
- 🍕 **Food Delivery** — Re-engagement, recommendations, order updates
- 🛒 **E-Commerce** — Abandoned cart, flash sales, promotional offers

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start the server
uvicorn main:app --reload --port 8000
```
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the iOS simulator and any local development client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(signals_router, prefix="/api/v1")
app.include_router(compose_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "NotifyCompose API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "paper": "https://github.com/ndagrawal/LLMNotificationComposition"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
