"""Timed certification mock exam endpoints (10.3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.content import Question, Track
from app.models.exam import Certificate, MockExamAttempt
from app.models.user import User
from app.schemas.content import QuestionPublic
from app.schemas.exam import (
    CertificatePublic,
    MockExamStartRequest,
    MockExamStartResponse,
    MockExamSubmitRequest,
    MockExamSubmitResponse,
    TrackExamBlueprint,
    TrackExamStartResponse,
    TrackExamSubmitResponse,
)
from app.services import mock_exam as mock_exam_service
from app.services import quiz as quiz_service
from app.services import track_exam as track_exam_service

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

    # `get_db` yields a session and never commits, so every endpoint that writes
    # commits for itself - see auth.py, which does it at each write. A flush
    # alone is not enough: on Postgres the transaction is discarded when the
    # session closes and the attempt would not exist by the time the learner
    # answers. It survives on SQLite, which is what local tooling and the tests
    # use, so this is a difference that only shows up in production.
    await db.commit()

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
    await db.commit()

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


# ── Track final exam and module test-out (17.2) ─────────────────────────────


async def _start_and_serialise(
    db: AsyncSession, attempt: MockExamAttempt
) -> TrackExamStartResponse:
    # See the note in `start_mock_exam`: `get_db` never commits, and on Postgres
    # an uncommitted attempt is gone by the time the learner answers.
    await db.commit()

    questions = (
        await db.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
    ).all()
    by_id = {q.id: q for q in questions}
    ordered = [by_id[qid] for qid in attempt.question_ids if qid in by_id]

    return TrackExamStartResponse(
        attempt_id=attempt.id,
        track_id=attempt.track_id,
        module_id=attempt.module_id,
        kind=attempt.kind,
        duration_minutes=attempt.duration_minutes,
        pass_pct=attempt.pass_pct or track_exam_service.DEFAULT_PASS_PCT,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        questions=[QuestionPublic.model_validate(q) for q in ordered],
    )


@router.get("/track/{track_id}/blueprint", response_model=TrackExamBlueprint)
async def get_track_exam_blueprint(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackExamBlueprint:
    """How many questions, how long, and what passing means - before committing.

    Starting an exam you cannot finish is a bad way to find out it is 50
    questions long, so the numbers are published first and come from the same
    function that draws the exam.
    """
    try:
        blueprint = await track_exam_service.track_exam_blueprint(db, track_id)
    except track_exam_service.TrackExamError as err:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(err)) from err
    return TrackExamBlueprint(**blueprint)


@router.post("/track/{track_id}/start", response_model=TrackExamStartResponse, status_code=201)
async def start_track_exam(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackExamStartResponse:
    try:
        attempt = await track_exam_service.start_track_final(db, current_user, track_id)
    except track_exam_service.TrackExamError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(err)) from err
    return await _start_and_serialise(db, attempt)


@router.post(
    "/module/{module_id}/test-out/start",
    response_model=TrackExamStartResponse,
    status_code=201,
)
async def start_test_out(
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackExamStartResponse:
    try:
        attempt = await track_exam_service.start_test_out(db, current_user, module_id)
    except track_exam_service.TrackExamError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(err)) from err
    return await _start_and_serialise(db, attempt)


@router.post("/track/{attempt_id}/submit", response_model=TrackExamSubmitResponse)
async def submit_track_exam(
    attempt_id: uuid.UUID,
    payload: MockExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackExamSubmitResponse:
    """Grades a track final or a test-out.

    `{attempt_id}` rather than a track id: you submit a *sitting*, and a learner
    can have sat the same track more than once.
    """
    attempt = await _load_own_attempt(db, attempt_id, current_user)
    if attempt.kind == "certification":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "this is a certification mock - submit it to POST /exams/mock/{attempt_id}/submit",
        )
    if attempt.status != "in_progress":
        raise HTTPException(status.HTTP_409_CONFLICT, f"attempt already {attempt.status}")

    # Graded even when late - refusing would lose the learner's work - but
    # recorded as expired so a late score is never read as an on-time one.
    expired = track_exam_service.is_expired(attempt)
    answers = {a.question_id: a.selected_index for a in payload.answers}
    report = await track_exam_service.score_attempt(db, attempt, answers)

    mastery_updated: dict[str, float] = {}
    if attempt.kind == track_exam_service.KIND_TEST_OUT and report["passed"] and not expired:
        # Only a passed, on-time test-out moves mastery. A failed one is still a
        # sitting the learner did, but letting it push mastery *down* would
        # punish trying to skip ahead - and an expired one says nothing about
        # what they know, only about the clock.
        questions = (
            await db.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
        ).all()
        by_id = {q.id: q for q in questions}
        for question_id in attempt.question_ids:
            question = by_id.get(question_id)
            if question is None:
                continue
            chosen = answers.get(question_id)
            correct = chosen is not None and chosen == question.correct_index
            mastery_updated[question.skill_id] = await quiz_service.apply_exam_evidence(
                db,
                current_user,
                question,
                correct,
                # The exam clock is per-sitting, not per-question, so there is no
                # honest per-question timing to hand FSRS. The expected time is
                # the neutral choice: it grades the answer on correctness alone
                # instead of inventing a speed the learner never demonstrated.
                response_time_ms=question.expected_time_ms,
            )

    certificate = await track_exam_service.issue_certificate(db, attempt, report, expired=expired)
    certificate_public = await _certificate_public(db, certificate) if certificate else None

    attempt.report = report
    attempt.submitted_at = datetime.now(UTC)
    attempt.status = "expired" if expired else "submitted"
    await db.commit()

    return TrackExamSubmitResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        expired=expired,
        report=report,  # type: ignore[arg-type]
        certificate=certificate_public,
        mastery_updated=mastery_updated,
    )


async def _certificate_public(db: AsyncSession, certificate: Certificate) -> CertificatePublic:
    user = await db.get(User, certificate.user_id)
    track = await db.get(Track, certificate.track_id)
    return CertificatePublic(
        code=certificate.code,
        username=user.username if user else "",
        track_id=certificate.track_id,
        track_name_es=track.name_es if track else certificate.track_id,
        track_name_en=track.name_en if track else certificate.track_id,
        score_pct=certificate.score_pct,
        questions=certificate.questions,
        issued_at=certificate.issued_at,
        revoked=certificate.revoked,
    )


@router.get("/certificates/{code}", response_model=CertificatePublic)
async def verify_certificate(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> CertificatePublic:
    """Public verification. **No authentication on purpose.**

    A certificate whose holder must be logged in to prove it is not verifiable
    by the person who needs to verify it - an employer, a reviewer - so this
    endpoint is open. What keeps it from becoming a directory of everyone who
    ever passed anything is that the only key is a 128-bit code: it is not
    enumerable, not derived from the user or the track, and only reaches someone
    because the holder chose to give it to them.

    It returns the holder's username, which is already the public identity used
    in leagues and duels, plus the score, the track and the date. No email, no
    id, nothing about any other sitting. A revoked certificate still resolves
    and says so - a 404 cannot be told apart from a code that never existed.
    """
    certificate = (await db.scalars(select(Certificate).where(Certificate.code == code))).first()
    if certificate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "certificate not found")
    return await _certificate_public(db, certificate)
