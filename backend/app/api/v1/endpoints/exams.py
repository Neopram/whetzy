"""Timed certification mock exam endpoints (10.3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.content import Question
from app.models.exam import MockExamAttempt
from app.models.user import User
from app.schemas.content import QuestionPublic
from app.schemas.exam import (
    MockExamStartRequest,
    MockExamStartResponse,
    MockExamSubmitRequest,
    MockExamSubmitResponse,
)
from app.services import mock_exam as mock_exam_service

router = APIRouter()


async def _load_own_attempt(
    db: AsyncSession, attempt_id: uuid.UUID, user: User
) -> MockExamAttempt:
    attempt = await db.get(MockExamAttempt, attempt_id)
    # Same 404 whether it does not exist or belongs to someone else: telling
    # the two apart would let anyone enumerate other people's attempts.
    if attempt is None or attempt.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mock exam attempt not found")
    return attempt


@router.post("/mock/start", response_model=MockExamStartResponse, status_code=201)
async def start_mock_exam(
    payload: MockExamStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MockExamStartResponse:
    try:
        attempt = await mock_exam_service.start_attempt(db, current_user, payload.track_id)
    except mock_exam_service.MockExamError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(err)) from err

    questions = (
        await db.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
    ).all()
    # Return them in the drawn order, not whatever order the database chose.
    by_id = {q.id: q for q in questions}
    ordered = [by_id[qid] for qid in attempt.question_ids if qid in by_id]

    return MockExamStartResponse(
        attempt_id=attempt.id,
        track_id=attempt.track_id,
        duration_minutes=attempt.duration_minutes,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        questions=[QuestionPublic.model_validate(q) for q in ordered],
    )


@router.post("/mock/{attempt_id}/submit", response_model=MockExamSubmitResponse)
async def submit_mock_exam(
    attempt_id: uuid.UUID,
    payload: MockExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MockExamSubmitResponse:
    attempt = await _load_own_attempt(db, attempt_id, current_user)
    if attempt.status != "in_progress":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"attempt already {attempt.status}"
        )

    # A late submission is still graded - refusing to score it would lose the
    # learner's work - but it is recorded as expired, so a score obtained past
    # the deadline can never be read as one obtained within it.
    expired = mock_exam_service.is_expired(attempt)
    answers = {a.question_id: a.selected_index for a in payload.answers}
    report = await mock_exam_service.score_attempt(db, attempt, answers)

    attempt.report = report
    attempt.submitted_at = datetime.now(UTC)
    attempt.status = "expired" if expired else "submitted"
    await db.flush()

    return MockExamSubmitResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        expired=expired,
        report=report,  # type: ignore[arg-type]
    )


@router.get("/mock/{attempt_id}", response_model=MockExamSubmitResponse)
async def get_mock_exam_result(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MockExamSubmitResponse:
    """Rereads a finished attempt, returning the report exactly as it was
    scored - the numbers a learner was shown must not change afterwards."""
    attempt = await _load_own_attempt(db, attempt_id, current_user)
    if attempt.report is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "attempt has not been submitted yet")
    return MockExamSubmitResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        expired=attempt.status == "expired",
        report=attempt.report,  # type: ignore[arg-type]
    )
