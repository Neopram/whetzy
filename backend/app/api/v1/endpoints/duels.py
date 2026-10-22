"""Async 1-v-1 duel endpoints."""

from __future__ import annotations

import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    DuelRivalAnswer,
    DuelSummary,
)
from app.services import lesson_gate
from app.services.blocklist import blocked_user_ids, is_blocked_pair
from app.services.quiz import apply_evidence

logger = logging.getLogger(__name__)
router = APIRouter()

_EXEC_TYPES = frozenset({"fill_blank_exec", "fix_bug"})
_DUEL_QUESTIONS = 5
# H.52 (ADR-69 #6): un reto sin terminar caduca a los 7 días, sin ganador.
DUEL_EXPIRY = timedelta(days=7)
_OPEN = ("pending", "in_progress")


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime) -> datetime:
    # SQLite (tests) devuelve fechas sin zona; Postgres, con zona.
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _expire_if_stale(duel: Duel, now: datetime) -> bool:
    """Caducidad perezosa (42.5): no hay job; se marca al tocar el duelo."""
    if duel.status in _OPEN and _aware(duel.created_at) + DUEL_EXPIRY <= now:
        duel.status = "expired"
        duel.winner_id = None
        return True
    return False


def _server_time_ms(
    started: datetime | None, completed: datetime | None, answers: list[dict[str, object]] | None
) -> float:
    """Tiempo de una partida según el reloj del servidor (42.4, H.52)."""
    if started is None and answers:
        first = answers[0].get("answered_at")
        started = datetime.fromisoformat(first) if isinstance(first, str) else None
    if started is None or completed is None:
        return float("inf")
    return (_aware(completed) - _aware(started)).total_seconds() * 1000


def _count_correct(answers: list[dict[str, object]] | None) -> int:
    if not answers:
        return 0
    return sum(1 for a in answers if a.get("correct"))


def _total_time(answers: list[dict[str, object]] | None) -> int:
    if not answers:
        return 0
    return sum(int(a.get("response_time_ms", 0)) for a in answers)  # type: ignore[call-overload]


async def _load_user_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    return user


async def _pick_skill(
    db: AsyncSession, challenger: User, opponent: User, skill_id: str | None
) -> str:
    # 43.5 (ADR-65 D7): solo skills que los dos pueden practicar (lección vista,
    # o test-out / ventaja en la prueba de nivel, H.60).
    if skill_id:
        if not await lesson_gate.practice_unlocked_skill_ids(db, challenger.id, [skill_id]):
            raise HTTPException(status_code=409, detail={"code": "needs_lesson", "skill_id": skill_id})
        if not await lesson_gate.practice_unlocked_skill_ids(db, opponent.id, [skill_id]):
            raise HTTPException(
                status_code=409, detail={"code": "opponent_needs_lesson", "skill_id": skill_id}
            )
        return skill_id
    # Pick a skill the challenger has attempted
    result = await db.execute(
        select(UserSkillState.skill_id)
        .where(UserSkillState.user_id == challenger.id, UserSkillState.attempts > 0)
        .order_by(UserSkillState.attempts.desc())
        .limit(10)
    )
    attempted = [row[0] for row in result.all()]
    both = await lesson_gate.practice_unlocked_skill_ids(
        db, challenger.id, attempted
    ) & await lesson_gate.practice_unlocked_skill_ids(db, opponent.id, attempted)
    skill_ids = [sid for sid in attempted if sid in both]
    if not skill_ids:
        raise HTTPException(
            status_code=422,
            detail="You haven't studied any skill yet. Complete at least one quiz before challenging.",
        )
    return random.choice(skill_ids)


async def _pick_questions(db: AsyncSession, skill_id: str) -> list[Question]:
    # Duels have no code-execution UI, so exec-graded types are out (as
    # before) — but legacy `fill_blank` questions also have no options and no
    # correct_index (see quiz.py's _select_question for the same exclusion),
    # so `type.notin_(_EXEC_TYPES)` alone let them through with nothing to
    # click and no way to score the answer. Require a real correct_index too.
    # `pool != "simulacro"`: a duel is not the certification mock exam, so a
    # reserved question must never turn up here (37.18/ADR-53 §4) — same
    # invariant and same unconditional exclusion as quiz.py's _select_question.
    result = await db.execute(
        select(Question)
        .where(
            Question.skill_id == skill_id,
            Question.type.notin_(list(_EXEC_TYPES)),
            Question.correct_index.is_not(None),
            Question.pool != "simulacro",
        )
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
    # Un bloqueo posterior a la creación también cierra los duelos ya
    # pendientes (19.11): cubre /join, /answer y /result de un solo golpe,
    # ya que las tres llaman a este helper.
    if await is_blocked_pair(db, duel.challenger_id, duel.opponent_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This duel isn't available")
    return duel


def _resolve_winner(duel: Duel) -> uuid.UUID | None:
    c_correct = _count_correct(duel.challenger_answers)
    o_correct = _count_correct(duel.opponent_answers)
    if c_correct > o_correct:
        return duel.challenger_id
    if o_correct > c_correct:
        return duel.opponent_id
    # Tiebreak: less time on the SERVER's clock wins. The client's own
    # `response_time_ms` is not trusted for this: it can claim 0 (H.52).
    c_time = _server_time_ms(duel.created_at, duel.challenger_completed_at, duel.challenger_answers)
    o_time = _server_time_ms(duel.opponent_started_at, duel.opponent_completed_at, duel.opponent_answers)
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
    if await is_blocked_pair(db, current_user.id, opponent.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This challenge isn't allowed")
    # H.52: quien salió de las ligas no reta ni es retado. Del rival no se dice
    # el motivo, igual que con un bloqueo.
    if current_user.leagues_opt_out:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "duels_opt_out"})
    if opponent.leagues_opt_out:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This challenge isn't allowed")

    skill_id = await _pick_skill(db, current_user, opponent, payload.skill_id)
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

    # Fire push notification to opponent (best-effort — don't fail the response)
    from app.services import push_service as _push
    try:
        await _push.send_to_user(
            db,
            opponent.id,
            title=_push.localize(opponent.language, "⚔️ ¡Te han retado!", "⚔️ You've been challenged!"),
            body=_push.localize(
                opponent.language,
                f"{current_user.display_name} te retó a un duelo.",
                f"{current_user.display_name} challenged you to a duel.",
            ),
            tag="duel-challenge",
        )
    except Exception as exc:  # noqa: BLE001 — push delivery is best-effort, must not fail the challenge
        logger.warning("Duel challenge push notification failed: %s", exc)

    return DuelChallengeResponse(
        duel_id=str(duel.id),
        skill_id=skill_id,
        questions=[QuestionPublic.model_validate(q) for q in questions],
        opponent_username=opponent.username,
    )


# ── GET /my ──────────────────────────────────────────────────────────────────

@router.get("/my", response_model=list[DuelSummary])
async def my_duels(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DuelSummary]:
    # Un duelo (pendiente o ya jugado) con alguien bloqueado tras crearse no
    # sale en la lista — mismo criterio que /join, /answer y /result (19.11).
    hidden = await blocked_user_ids(db, current_user.id)

    result = await db.execute(
        select(Duel)
        .where(
            or_(Duel.challenger_id == current_user.id, Duel.opponent_id == current_user.id)
        )
        .order_by(Duel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    duels = result.scalars().all()
    now = _now()
    # Every stale one, not just the first: `any()` would stop at it.
    if [d for d in duels if _expire_if_stale(d, now)]:
        await db.commit()

    summaries = []
    for duel in duels:
        is_challenger = duel.challenger_id == current_user.id
        other_id = duel.opponent_id if is_challenger else duel.challenger_id
        if other_id in hidden:
            continue

        other_result = await db.execute(select(User).where(User.id == other_id))
        other_user = other_result.scalar_one_or_none()
        if other_user is None:
            continue

        my_answers = duel.challenger_answers if is_challenger else duel.opponent_answers
        their_answers = duel.opponent_answers if is_challenger else duel.challenger_answers
        my_completed_at = duel.challenger_completed_at if is_challenger else duel.opponent_completed_at

        is_your_turn = duel.status in _OPEN and my_completed_at is None

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


# ── GET /{id}/join ───────────────────────────────────────────────────────────

@router.get("/{duel_id}/join", response_model=DuelChallengeResponse)
async def join_duel(
    duel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelChallengeResponse:
    """The duel's questions for whoever still has to play their side: the
    opponent, or the challenger coming back to a duel left halfway (42.5)."""
    duel = await _get_duel_or_404(db, duel_id, current_user)
    is_challenger = duel.challenger_id == current_user.id
    if _expire_if_stale(duel, _now()):
        await db.commit()
    if duel.status == "expired":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"code": "duel_expired"})
    my_completed_at = duel.challenger_completed_at if is_challenger else duel.opponent_completed_at
    if my_completed_at is not None:
        raise HTTPException(status_code=409, detail="You already completed this duel")
    if duel.status == "completed":
        raise HTTPException(status_code=409, detail="This duel is already completed")
    if not is_challenger and duel.opponent_started_at is None:
        duel.opponent_started_at = _now()
        await db.commit()

    questions: list[Question] = []
    for qid in duel.question_ids:
        q_result = await db.execute(select(Question).where(Question.id == qid))
        q = q_result.scalar_one_or_none()
        if q is not None:
            questions.append(q)

    other_id = duel.opponent_id if is_challenger else duel.challenger_id
    other = (await db.execute(select(User).where(User.id == other_id))).scalar_one()
    mine = (duel.challenger_answers if is_challenger else duel.opponent_answers) or []

    return DuelChallengeResponse(
        duel_id=str(duel.id),
        skill_id=duel.skill_id,
        questions=[QuestionPublic.model_validate(q) for q in questions],
        opponent_username=other.username,
        answered_question_ids=[str(a["question_id"]) for a in mine],
    )


# ── POST /{id}/answer ────────────────────────────────────────────────────────

@router.post("/{duel_id}/answer", response_model=DuelAnswerResponse)
async def answer_duel(
    duel_id: str,
    payload: DuelAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelAnswerResponse:
    duel = await _get_duel_or_404(db, duel_id, current_user)

    if _expire_if_stale(duel, _now()):
        await db.commit()
    if duel.status == "expired":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"code": "duel_expired"})
    if duel.status == "completed":
        raise HTTPException(status_code=409, detail="Duel is already completed")

    is_challenger = duel.challenger_id == current_user.id
    my_completed_at = duel.challenger_completed_at if is_challenger else duel.opponent_completed_at

    if my_completed_at is not None:
        raise HTTPException(status_code=409, detail="You have already completed this duel")

    if payload.question_id not in duel.question_ids:
        raise HTTPException(status_code=422, detail="question_id is not part of this duel")

    my_answers: list[dict[str, Any]] = list(duel.challenger_answers or []) if is_challenger else list(duel.opponent_answers or [])
    answered_ids = {a["question_id"] for a in my_answers}
    if payload.question_id in answered_ids:
        raise HTTPException(status_code=409, detail="Already answered this question in the duel")

    # Load question to determine correctness
    q_result = await db.execute(select(Question).where(Question.id == payload.question_id))
    question = q_result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    # 42.4: con opciones, el índice tiene que ser una de ellas. Un ítem sin
    # opciones (exec) no puntúa nunca y se graba como fallo
    # (test_motor_wiring.test_duel_item_without_correct_index_never_scores).
    options = question.options_es or []
    if options and payload.selected_index >= len(options):
        raise HTTPException(status_code=422, detail="selected_index is not one of the options")

    # Duels only serve items with a correct_index (`_pick_questions`). An item
    # without one can never be right here: the old `selected_index == 1` branch
    # for exec types let the client decide.
    correct = question.correct_index is not None and payload.selected_index == question.correct_index

    # 42.9: un duelo mueve el dominio, pero no lo lleva a «dominada» ni cuenta
    # para la puerta de evidencia (ADR-63 §3-4).
    await apply_evidence(
        db, current_user.id, question, correct, payload.response_time_ms, source="duel"
    )

    now = _now()
    my_answers.append({
        "question_id": payload.question_id,
        "selected_index": payload.selected_index,
        "response_time_ms": payload.response_time_ms,
        "correct": correct,
        "answered_at": now.isoformat(),
    })

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

    rival: DuelRivalAnswer | None = None
    if opponent_completed:
        rival_answers = (duel.opponent_answers if is_challenger else duel.challenger_answers) or []
        theirs = next((a for a in rival_answers if a["question_id"] == payload.question_id), None)
        if theirs is not None:
            # Solo acierto y tiempo: la opción que eligió (`selected_index`) no sale.
            rival = DuelRivalAnswer.model_validate(theirs)

    return DuelAnswerResponse(
        duel_id=str(duel.id),
        answers_so_far=len(my_answers),
        completed=len(my_answers) == _DUEL_QUESTIONS,
        opponent_completed=opponent_completed,
        correct=correct,
        correct_index=question.correct_index,
        explanation_es=question.explanation_es,
        explanation_en=question.explanation_en,
        rival=rival,
    )


# ── GET /{id}/result ─────────────────────────────────────────────────────────

@router.get("/{duel_id}/result", response_model=DuelResultResponse)
async def duel_result(
    duel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DuelResultResponse:
    duel = await _get_duel_or_404(db, duel_id, current_user)

    if _expire_if_stale(duel, _now()):
        await db.commit()
    if duel.status == "expired":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"code": "duel_expired"})
    if duel.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Duel is not completed yet",
        )

    c_result = await db.execute(select(User).where(User.id == duel.challenger_id))
    challenger = c_result.scalar_one()
    o_result = await db.execute(select(User).where(User.id == duel.opponent_id))
    opponent = o_result.scalar_one()

    # Suggest practice on the duel skill when the requester didn't win (E2).
    current_won = duel.winner_id == current_user.id
    weak_skill_id = None if current_won else duel.skill_id

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
        weak_skill_id=weak_skill_id,
    )
