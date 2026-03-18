"""
compose.py — Notification composition route.
POST /api/v1/compose — runs the full pipeline and returns a ComposedNotification.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.schemas import ComposeRequest, ComposeResponse
from services.pipeline import run_pipeline

router = APIRouter()


@router.post("/compose", response_model=ComposeResponse, tags=["Composition"])
async def compose_notification(
    request: ComposeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run the full NotifyCompose pipeline for a single notification request.

    Pipeline stages:
    1. Frequency Capper — enforce max-touch rules
    2. Budget Router — CLV-based path selection (LLM Full / Hybrid / Template)
    3. Context Retriever — assemble user + content context for RAG
    4. Message Composer — generate N candidate messages via LLM
    5. Guardrail Filter — block hallucinations and dark patterns
    6. Reward Ranker — score and rank candidates
    7. Send-Time Optimizer — Thompson Sampling bandit for optimal delivery time

    Returns the highest-scoring candidate with full pipeline trace.
    """
    try:
        result = await run_pipeline(request, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
