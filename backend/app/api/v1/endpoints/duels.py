"""Async 1-v-1 duel endpoints."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.content import Question
from app.models.duel import Duel
from app.models.user import User, UserSkillState
from app.schemas.content import QuestionPublic
from app.schemas.duel import (
    DuelAnswerRequest,
    DuelAnswerResponse,
    DuelChallengeRequest,
    DuelChallengeResponse,
    DuelPlayerResult,
    DuelResultResponse,
    DuelSummary,
)

router = APIRouter()

_EXEC_TYPES = frozenset({"fill_blank_exec", "fix_bug"})
_DUEL_QUESTIONS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _count_correct(answers: list[dict[str, object]] | None) -> int:
    if not answers:
        return 0
    return sum(1 for a in answers if a.get("correct"))


def _total_time(answers: list[dict[str, object]] | None) -> int:
    if not answers:
        return 0
    return sum(int(a.get("response_time_ms", 0)) for a in answers)


async def _load_user_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    return user


async def _pick_skill(db: AsyncSession, challenger: User, skill_id: str | None) -> str:
    if skill_id:
        return skill_id
    # Pick a skill the challenger has attempted
    result = await db.execute(
        select(UserSkillState.skill_id)
        .where(UserSkillState.user_id == challenger.id, UserSkillState.attempts > 0)
        .order_by(UserSkillState.attempts.desc())
        .limit(10)
    )
    skill_ids = [row[0] for row in result.all()]
    if not skill_ids:
        raise HTTPException(
            status_code=422,
            detail="You haven't studied any skill yet. Complete at least one quiz before challenging.",
        )
    return random.choice(skill_ids)


async def _pick_questions(db: AsyncSession, skill_id: str) -> list[Question]:
    result = await db.execute(
        select(Question)
        .where(Question.skill_id == skill_id, Question.type.notin_(list(_EXEC_TYPES)))
        .order_by(Question.elo_rating)
    )
    questions = result.scalars().all()
    if len(questions) < _DUEL_QUESTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Skill '{skill_id}' has fewer than {_DUEL_QUESTIONS} MCQ questions — choose another.",
        )
    return random.sample(list(questions), _DUEL_QUESTIONS)


async def _get_duel_or_404(db: AsyncSession, duel_id: str, user: User) -> Duel:
    try:
        uid = uuid.UUID(duel_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Duel not found")
    result = await db.execute(select(Duel).where(Duel.id == uid))
    duel = result.scalar_one_or_none()
    if duel is None:
        raise HTTPException(status_code=404, detail="Duel not found")
    if duel.challenger_id != user.id and duel.opponent_id != user.id:
        raise HTTPException(status_code=403, detail="You are not part of this duel")
    return duel


def _resolve_winner(duel: Duel) -> uuid.UUID | None:
    c_correct = _count_correct(duel.challenger_answers)
    o_correct = _count_correct(duel.opponent_answers)
    if c_correct > o_correct:
        return duel.challenger_id
    if o_correct > c_correct:
        return duel.opponent_id
    # Tiebreak: less total time wins
    c_time = _total_time(duel.challenger_answers)
    o_time = _total_time(duel.opponent_answers)
    if c_time < o_time:
        return duel.challenger_id
    if o_time < c_time:
        return duel.opponent_id
    return None  # draw


# ── POST /challenge ──────────────────────────────────────────────────────────

@router.post("/challenge", status_code=status.HTTP_201_CREATED, response_model=DuelChallengeResponse)
async def challenge(
    payload: DuelChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelChallengeResponse:
    opponent = await _load_user_by_username(db, payload.opponent_username)
    if opponent.id == current_user.id:
        raise HTTPException(status_code=422, detail="You cannot challenge yourself")

    skill_id = await _pick_skill(db, current_user, payload.skill_id)
    questions = await _pick_questions(db, skill_id)

    duel = Duel(
        challenger_id=current_user.id,
        opponent_id=opponent.id,
        skill_id=skill_id,
        question_ids=[q.id for q in questions],
        status="pending",
    )
    db.add(duel)
    await db.commit()
    await db.refresh(duel)

    return DuelChallengeResponse(
        duel_id=str(duel.id),
        skill_id=skill_id,
        questions=[QuestionPublic.model_validate(q) for q in questions],
        opponent_username=opponent.username,
    )


# ── GET /my ──────────────────────────────────────────────────────────────────

@router.get("/my", response_model=list[DuelSummary])
async def my_duels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DuelSummary]:
    result = await db.execute(
        select(Duel)
        .where(
            or_(Duel.challenger_id == current_user.id, Duel.opponent_id == current_user.id)
        )
        .order_by(Duel.created_at.desc())
        .limit(50)
    )
    duels = result.scalars().all()

    summaries = []
    for duel in duels:
        is_challenger = duel.challenger_id == current_user.id
        other_id = duel.opponent_id if is_challenger else duel.challenger_id

        other_result = await db.execute(select(User).where(User.id == other_id))
        other_user = other_result.scalar_one_or_none()
        if other_user is None:
            continue

        my_answers = duel.challenger_answers if is_challenger else duel.opponent_answers
        their_answers = duel.opponent_answers if is_challenger else duel.challenger_answers
        my_completed_at = duel.challenger_completed_at if is_challenger else duel.opponent_completed_at

        is_your_turn = duel.status != "completed" and my_completed_at is None

        summaries.append(
            DuelSummary(
                duel_id=str(duel.id),
                status=duel.status,
                skill_id=duel.skill_id,
                opponent_username=other_user.username,
                opponent_avatar=other_user.avatar_emoji,
                your_correct=_count_correct(my_answers) if my_completed_at else None,
                opponent_correct=_count_correct(their_answers) if (
                    duel.opponent_completed_at if is_challenger else duel.challenger_completed_at
                ) else None,
                winner_id=str(duel.winner_id) if duel.winner_id else None,
                is_your_turn=is_your_turn,
                created_at=duel.created_at,
            )
        )
    return summaries


# ── POST /{id}/answer ────────────────────────────────────────────────────────

@router.post("/{duel_id}/answer", response_model=DuelAnswerResponse)
async def answer_duel(
    duel_id: str,
    payload: DuelAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelAnswerResponse:
    duel = await _get_duel_or_404(db, duel_id, current_user)

    if duel.status == "completed":
        raise HTTPException(status_code=409, detail="Duel is already completed")

    is_challenger = duel.challenger_id == current_user.id
    my_completed_at = duel.challenger_completed_at if is_challenger else duel.opponent_completed_at

    if my_completed_at is not None:
        raise HTTPException(status_code=409, detail="You have already completed this duel")

    if payload.question_id not in duel.question_ids:
        raise HTTPException(status_code=422, detail="question_id is not part of this duel")

    my_answers: list = list(duel.challenger_answers or []) if is_challenger else list(duel.opponent_answers or [])
    answered_ids = {a["question_id"] for a in my_answers}
    if payload.question_id in answered_ids:
        raise HTTPException(status_code=409, detail="Already answered this question in the duel")

    # Load question to determine correctness
    q_result = await db.execute(select(Question).where(Question.id == payload.question_id))
    question = q_result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.type in _EXEC_TYPES:
        correct = payload.selected_index == 1
    else:
        correct = question.correct_index is not None and payload.selected_index == question.correct_index

    my_answers.append({
        "question_id": payload.question_id,
        "selected_index": payload.selected_index,
        "response_time_ms": payload.response_time_ms,
        "correct": correct,
    })

    now = _now()
    if is_challenger:
        duel.challenger_answers = my_answers
        if len(my_answers) == _DUEL_QUESTIONS:
            duel.challenger_completed_at = now
    else:
        duel.opponent_answers = my_answers
        if len(my_answers) == _DUEL_QUESTIONS:
            duel.opponent_completed_at = now

    # Check if both sides are done
    both_done = (
        duel.challenger_completed_at is not None
        and duel.opponent_completed_at is not None
    )
    if both_done:
        duel.winner_id = _resolve_winner(duel)
        duel.status = "completed"
    elif duel.status == "pending":
        duel.status = "in_progress"

    await db.commit()
    await db.refresh(duel)

    opponent_completed = (
        duel.opponent_completed_at is not None if is_challenger else duel.challenger_completed_at is not None
    )

    return DuelAnswerResponse(
        duel_id=str(duel.id),
        answers_so_far=len(my_answers),
        completed=len(my_answers) == _DUEL_QUESTIONS,
        opponent_completed=opponent_completed,
    )


# ── GET /{id}/result ─────────────────────────────────────────────────────────

@router.get("/{duel_id}/result", response_model=DuelResultResponse)
async def duel_result(
    duel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelResultResponse:
    duel = await _get_duel_or_404(db, duel_id, current_user)

    if duel.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Duel is not completed yet",
        )

    c_result = await db.execute(select(User).where(User.id == duel.challenger_id))
    challenger = c_result.scalar_one()
    o_result = await db.execute(select(User).where(User.id == duel.opponent_id))
    opponent = o_result.scalar_one()

    return DuelResultResponse(
        duel_id=str(duel.id),
        status=duel.status,
        skill_id=duel.skill_id,
        challenger=DuelPlayerResult(
            user_id=str(challenger.id),
            username=challenger.username,
            display_name=challenger.display_name,
            avatar_emoji=challenger.avatar_emoji,
            correct=_count_correct(duel.challenger_answers),
            total_time_ms=_total_time(duel.challenger_answers),
        ),
        opponent=DuelPlayerResult(
            user_id=str(opponent.id),
            username=opponent.username,
            display_name=opponent.display_name,
            avatar_emoji=opponent.avatar_emoji,
            correct=_count_correct(duel.opponent_answers),
            total_time_ms=_total_time(duel.opponent_answers),
        ),
        winner_id=str(duel.winner_id) if duel.winner_id else None,
        is_draw=duel.winner_id is None,
        created_at=duel.created_at,
    )
