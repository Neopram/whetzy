"""Adaptive study/review quiz endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.entitlements import user_meets_tier
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.session import (
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizEndRequest,
    QuizEndResponse,
    QuizStartRequest,
    QuizStartResponse,
    ReviewDueResponse,
)
from app.services import quiz as quiz_service

router = APIRouter()


@router.post("/start", response_model=QuizStartResponse)
async def start_quiz(
    payload: QuizStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizStartResponse:
    # El repaso espaciado (FSRS) es el motor, no un extra: gratis para todos. La
    # landing lo promete y Home lo ofrece con «Repasar»; hasta el 2026-09-24 ese
    # botón devolvía 403 a cualquiera sin plan, es decir, a todo el mundo.
    # El modo examen sigue siendo de Pro (ADR-41).
    if payload.mode == "exam" and not user_meets_tier(current_user, "plus") and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{payload.mode.capitalize()} mode requires a Plus subscription.",
        )
    return await quiz_service.start_session(db, current_user, payload)


@router.post("/answer", response_model=QuizAnswerResponse)
async def answer_quiz(
    payload: QuizAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizAnswerResponse:
    return await quiz_service.submit_answer(db, current_user, payload)


@router.post("/end", response_model=QuizEndResponse)
async def end_quiz(
    payload: QuizEndRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizEndResponse:
    return await quiz_service.end_session(db, current_user, payload)


@router.get("/review-due", response_model=ReviewDueResponse)
async def review_due(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewDueResponse:
    count = await quiz_service.count_due_reviews(db, current_user)
    return ReviewDueResponse(due_count=count)
