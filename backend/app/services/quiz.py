"""Orchestrates a study/review session: question selection, answer grading,
and persistence of BKT/Elo/FSRS state updates.

FSRS and Elo state are tracked at *skill* granularity (see
`UserSkillState`), while item-level (per-question) difficulty is
continuously recalibrated on `Question.elo_rating` via the same two-sided
Elo update. This keeps the scheduling state small (one row per user per
skill) while still letting individual questions carry their own calibrated
difficulty.
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

logger = logging.getLogger("whetzy.quiz")

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.services.dkt as _dkt
from app.core.config import settings
from app.models.content import Module, Question, Skill
from app.models.session import Response, StudySession
from app.models.user import User, UserSkillState
from app.schemas.content import QuestionPublic
from app.schemas.session import (
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizEndRequest,
    QuizEndResponse,
    QuizStartRequest,
    QuizStartResponse,
    SelectionReason,
)
from app.services import content_quota, lesson_gate
from app.services.ab_harness import get_cohort
from app.services.engine import (
    BKTModel,
    Card,
    EloEntity,
    EloRating,
    FSRSScheduler,
    SkillState,
)
from app.services.gamification import apply_quiz_event, get_or_create_current_entry

bkt = BKTModel()
elo = EloRating()
fsrs = FSRSScheduler()

TARGET_SUCCESS_PROBABILITY = 0.75
CANDIDATE_POOL_SIZE = 5

# Question types graded by answer-comparison (exec output or plain text).
# fill_blank_exec/fix_bug: Pyodide (Python); fill_blank: text compare only.
# sql_exec: sql.js worker; js_exec: sandboxed JS worker (F19+).
_EXEC_TYPES = frozenset({"fill_blank_exec", "fix_bug", "fill_blank", "sql_exec", "js_exec"})


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    """Normalize a datetime read back from the DB to tz-aware UTC.

    Postgres (asyncpg) always returns aware datetimes for `timestamptz`
    columns, but SQLite (used in local tooling/tests) returns naive ones —
    without this, `FSRSScheduler.review` would raise when subtracting a
    naive `last_review` from an aware `now`.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


async def _get_or_create_skill_state(
    db: AsyncSession, user_id: uuid.UUID, skill_id: str
) -> UserSkillState:
    result = await db.execute(
        select(UserSkillState).where(
            UserSkillState.user_id == user_id, UserSkillState.skill_id == skill_id
        )
    )
    state = result.scalar_one_or_none()
    if state is not None:
        return state

    # Check-then-insert is a race: two requests for the same skill both see no
    # row and both insert, and the loser hits `uq_user_skill_state` and takes
    # the whole request down with a 500. It is not hypothetical — a double tap
    # on "Practicar" is enough, and React's development double-render produced
    # it on the first try.
    #
    # Savepoint so the failed insert does not poison the outer transaction,
    # then re-read: whoever won created exactly the row we wanted.
    try:
        async with db.begin_nested():
            state = UserSkillState(user_id=user_id, skill_id=skill_id)
            db.add(state)
            await db.flush()
        return state
    except IntegrityError:
        result = await db.execute(
            select(UserSkillState).where(
                UserSkillState.user_id == user_id, UserSkillState.skill_id == skill_id
            )
        )
        return result.scalar_one()


async def _is_module_unlocked(db: AsyncSession, user_id: uuid.UUID, module: Module) -> bool:
    """A module is unlocked if it is the first in its track, or the
    previous module's average mastery clears its unlock threshold."""
    if module.order <= 0:
        return True

    prev_result = await db.execute(
        select(Module).where(Module.track_id == module.track_id, Module.order == module.order - 1)
    )
    prev_module = prev_result.scalar_one_or_none()
    if prev_module is None:
        return True

    skills_result = await db.execute(select(Skill.id).where(Skill.module_id == prev_module.id))
    prev_skill_ids = [row[0] for row in skills_result.all()]
    if not prev_skill_ids:
        return True

    states_result = await db.execute(
        select(UserSkillState.p_known).where(
            UserSkillState.user_id == user_id,
            UserSkillState.skill_id.in_(prev_skill_ids),
        )
    )
    p_known_values = [row[0] for row in states_result.all()]
    if not p_known_values:
        return False

    # Skills never attempted count as 0 mastery.
    padded = p_known_values + [0.0] * (len(prev_skill_ids) - len(p_known_values))
    avg_mastery = sum(padded) / len(padded)
    return bool(avg_mastery >= prev_module.min_mastery_to_unlock)


# 32.4: modos que exigen haber abierto la lección del skill antes de darle
# preguntas nuevas de ese skill. "placement" y "exam" quedan fuera a
# propósito: miden lo que el alumno ya sabe, no lo que acaba de aprender.
_LESSON_GATED_MODES = frozenset({"study", "review"})


async def _candidate_skill_ids(
    db: AsyncSession,
    user: User,
    mode: str,
    track_id: str | None,
    skill_id: str | None,
) -> tuple[list[str], str]:
    if skill_id:
        if mode in _LESSON_GATED_MODES and not await lesson_gate.viewed_skill_ids(
            db, user.id, [skill_id]
        ):
            return [], "needs_lesson"
        return [skill_id], "skill_pinned"

    now = _now()

    if mode == "review":
        query = select(UserSkillState.skill_id).where(
            UserSkillState.user_id == user.id,
            UserSkillState.fsrs_due.is_not(None),
            UserSkillState.fsrs_due <= now,
        )
        if track_id:
            query = query.join(Skill, Skill.id == UserSkillState.skill_id).join(
                Module, Module.id == Skill.module_id
            ).where(Module.track_id == track_id)
        result = await db.execute(query)
        due = [row[0] for row in result.all()]
        if due:
            return due, "spaced_repetition_due"
        # fall through to study-mode selection if nothing is due

    modules_query = select(Module).options(selectinload(Module.skills))
    if track_id:
        modules_query = modules_query.where(Module.track_id == track_id)
    modules_result = await db.execute(modules_query.order_by(Module.track_id, Module.order))
    modules = modules_result.scalars().all()

    unlocked_skill_ids: list[str] = []
    for module in modules:
        if await _is_module_unlocked(db, user.id, module):
            unlocked_skill_ids.extend(s.id for s in module.skills)

    if not unlocked_skill_ids:
        return [], "no_skills"

    if mode in _LESSON_GATED_MODES:
        # 32.4: llegar aquí en modo "review" ya significa que no había nada
        # pendiente y se cayó al estudio de material nuevo, así que se exige
        # la lección igual que en "study". "placement"/"exam" evalúan lo que
        # el alumno ya sabe -- exigir la lección primero rompería el propio
        # propósito del examen de nivel.
        seen = await lesson_gate.viewed_skill_ids(db, user.id, unlocked_skill_ids)
        gated = [sid for sid in unlocked_skill_ids if sid in seen]
        if not gated:
            return [], "needs_lesson"
        unlocked_skill_ids = gated

    states_result = await db.execute(
        select(UserSkillState.skill_id, UserSkillState.p_known).where(
            UserSkillState.user_id == user.id,
            UserSkillState.skill_id.in_(unlocked_skill_ids),
        )
    )
    mastery_by_skill = {row[0]: row[1] for row in states_result.all()}

    not_mastered = [
        sid for sid in unlocked_skill_ids if mastery_by_skill.get(sid, 0.0) < 0.95
    ]
    if not_mastered:
        return not_mastered, "low_mastery"
    return unlocked_skill_ids, "all_mastered"


def _weighted_choice(items: list[str], weights: list[float]) -> str:
    total = sum(weights)
    if total <= 0:
        return random.choice(items)
    r = random.random() * total
    cumulative = 0.0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]


async def _select_skill(
    db: AsyncSession, user: User, candidate_skill_ids: list[str]
) -> tuple[str | None, str]:
    if not candidate_skill_ids:
        return None, "no_candidates"
    if len(candidate_skill_ids) == 1:
        return candidate_skill_ids[0], "single_candidate"

    # A/B experiment (4.6): DKT cohort uses deep knowledge tracing predictions
    if get_cohort(user.id) == "dkt":
        history_result = await db.execute(
            select(Question.skill_id, Response.correct)
            .select_from(Response)
            .join(Question, Response.question_id == Question.id)
            .join(StudySession, Response.session_id == StudySession.id)
            .where(StudySession.user_id == user.id)
            .order_by(Response.created_at.desc())
            .limit(100)
        )
        history_rows = history_result.all()
        if history_rows:
            history = [{"skill_id": r[0], "correct": bool(r[1])} for r in reversed(history_rows)]
            predictions = _dkt.predict(history)
            if predictions:
                weights = [1.1 - predictions.get(sid, 0.5) for sid in candidate_skill_ids]
                return _weighted_choice(candidate_skill_ids, weights), "dkt_prediction"

    states_result = await db.execute(
        select(UserSkillState.skill_id, UserSkillState.p_known).where(
            UserSkillState.user_id == user.id,
            UserSkillState.skill_id.in_(candidate_skill_ids),
        )
    )
    mastery_by_skill = {row[0]: row[1] for row in states_result.all()}

    weights = [1.1 - mastery_by_skill.get(sid, 0.1) for sid in candidate_skill_ids]
    return _weighted_choice(candidate_skill_ids, weights), "mastery_weighting"


async def _select_question(
    db: AsyncSession,
    user: User,
    skill_id: str,
    exclude_question_ids: set[str] | None = None,
) -> tuple[Question | None, float | None]:
    # Serve index-graded (mcq/true_false/code_output) and exec-graded
    # (fill_blank_exec/fix_bug) questions; skip legacy fill_blank which has no
    # correct_index and no correct_answer field. Practice and spaced review
    # both go through this one function, so excluding pool == "simulacro"
    # here covers both halves of the invariant: a reserved mock-exam question
    # must never turn up outside a mock exam (37.18/ADR-53 §4). Unconditional,
    # not behind MOCK_EXAM_RESERVED_POOL_ENABLED — that flag only gates
    # mock_exam.py's "draw only from the reserved pool" requirement, which
    # needs content to exist first; excluding reserved questions from
    # practice is safe from day one and a no-op until 37.24 populates them.
    conditions = [
        Question.skill_id == skill_id,
        or_(
            Question.correct_index.is_not(None),
            Question.type.in_(list(_EXEC_TYPES)),
        ),
        Question.pool != "simulacro",
    ]
    query = select(Question).where(*conditions)
    if exclude_question_ids:
        query = query.where(Question.id.not_in(exclude_question_ids))
    result = await db.execute(query)
    questions = result.scalars().all()
    if not questions:
        return None, None

    state = await _get_or_create_skill_state(db, user.id, skill_id)
    user_entity = EloEntity(rating=state.elo_rating, interactions=state.attempts)

    scored = []
    for q in questions:
        item_entity = EloEntity(rating=q.elo_rating, interactions=30)
        p = elo.expected_score(user_entity.rating, item_entity.rating)
        scored.append((q, abs(p - TARGET_SUCCESS_PROBABILITY), p))

    scored.sort(key=lambda x: x[1])
    top_n = scored[:CANDIDATE_POOL_SIZE]
    chosen = random.choice(top_n)
    return chosen[0], round(chosen[2], 3)


async def _to_question_public(question: Question) -> QuestionPublic:
    return QuestionPublic.model_validate(question)


async def count_due_reviews(db: AsyncSession, user: User) -> int:
    now = _now()
    result = await db.execute(
        select(func.count(UserSkillState.id)).where(
            UserSkillState.user_id == user.id,
            UserSkillState.fsrs_due.is_not(None),
            UserSkillState.fsrs_due <= now,
        )
    )
    return int(result.scalar_one() or 0)


async def start_session(
    db: AsyncSession, user: User, req: QuizStartRequest
) -> QuizStartResponse:
    session = StudySession(
        user_id=user.id, mode=req.mode, track_id=req.track_id, skill_id=req.skill_id
    )
    db.add(session)
    await db.flush()

    question_public = None
    reason: SelectionReason | None = None
    if req.force_question_id is not None:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="force_question_id is a dev/E2E-only override",
            )
        result = await db.execute(select(Question).where(Question.id == req.force_question_id))
        question = result.scalar_one_or_none()
        if question is None:
            raise HTTPException(status_code=404, detail=f"Unknown question_id '{req.force_question_id}'")
        question_public = await _to_question_public(question)
        reason = SelectionReason(pool="forced")
    else:
        candidate_skill_ids, pool = await _candidate_skill_ids(db, user, req.mode, req.track_id, req.skill_id)
        # 32.4: el frontend necesita distinguir "sin preguntas por lo que sea"
        # de "faltó abrir la lección" para poder mandar a la lección en vez de
        # a un error genérico; sin esto `pool` se perdía en cuanto no había
        # skill_id/question que devolver.
        reason = SelectionReason(pool=pool)
        skill_id, strategy = await _select_skill(db, user, candidate_skill_ids)
        if skill_id:
            question, expected_p = await _select_question(db, user, skill_id)
            if question:
                question_public = await _to_question_public(question)
                reason = SelectionReason(
                    pool=pool,
                    skill_strategy=strategy,
                    difficulty_target=TARGET_SUCCESS_PROBABILITY,
                    expected_p=expected_p,
                )

    session.current_question_id = question_public.id if question_public else None
    reviews_due = await count_due_reviews(db, user)
    await db.commit()

    return QuizStartResponse(
        session_id=session.id,
        mode=session.mode,
        question=question_public,
        reviews_due=reviews_due,
        selection_reason=reason,
    )


def _grade_from_response(correct: bool, response_time_ms: int, expected_time_ms: int) -> int:
    """Map an answer outcome to an FSRS grade (1=Again .. 4=Easy)."""
    if not correct:
        return 1
    expected = max(1, expected_time_ms)
    ratio = response_time_ms / expected
    if ratio < 0.3:
        return 4  # fast + correct => easy
    if ratio < 1.0:
        return 3  # within expected time => good
    return 2  # slow but correct => hard


def _calculate_xp(correct: bool, combo: int, grade: int) -> int:
    if not correct:
        return 3
    base = 10
    if combo >= 15:
        multiplier = 5
    elif combo >= 7:
        multiplier = 3
    elif combo >= 3:
        multiplier = 2
    else:
        multiplier = 1
    bonus = 5 if grade == 4 else 0
    return base * multiplier + bonus


def _level_from_xp(total_xp: int) -> int:
    return max(1, total_xp // 500 + 1)


# Racha amable (COMPETENCIA.md §A.4, ledger 35.3): cada semana ISO nueva devuelve
# un comodín gratis si no queda ninguno. No se acumulan (los comprados sí se
# conservan): el comodín cubre un despiste, no compra semanas enteras. Perder la
# racha nunca toca el dominio (BKT), que vive aparte.
WEEKLY_FREE_FREEZES = 1


def _update_streak(user: User, now: datetime) -> None:
    today = now.date()
    if user.last_active is None:
        user.current_streak = 1
    else:
        last_day = user.last_active.date()
        if last_day.isocalendar()[:2] != today.isocalendar()[:2]:
            user.streak_freeze_available = max(user.streak_freeze_available, WEEKLY_FREE_FREEZES)
        if last_day == today:
            pass  # already counted today
        elif last_day == today - timedelta(days=1):
            user.current_streak += 1
        elif user.streak_freeze_available > 0 and last_day == today - timedelta(days=2):
            user.streak_freeze_available -= 1
            user.current_streak += 1
        else:
            user.current_streak = 1
    user.max_streak = max(user.max_streak, user.current_streak)
    user.last_active = now


async def _current_combo(db: AsyncSession, session_id: uuid.UUID) -> int:
    result = await db.execute(
        select(Response.correct)
        .where(Response.session_id == session_id)
        .order_by(Response.created_at.desc())
    )
    combo = 0
    for (correct,) in result.all():
        if correct:
            combo += 1
        else:
            break
    return combo


async def submit_answer(
    db: AsyncSession, user: User, req: QuizAnswerRequest
) -> QuizAnswerResponse:
    # Idempotency: if the client resends an answer with the same event_id,
    # return the cached result instead of double-counting (33.2).
    if req.event_id:
        dup = (
            await db.execute(
                select(Response).where(Response.event_id == req.event_id)
            )
        ).scalar_one_or_none()
        if dup is not None:
            q = (await db.execute(select(Question).where(Question.id == dup.question_id))).scalar_one()
            state = await _get_or_create_skill_state(db, user.id, q.skill_id)
            return QuizAnswerResponse(
                correct=dup.correct,
                correct_index=q.correct_index,
                explanation_es=q.explanation_es or "",
                explanation_en=q.explanation_en or "",
                source=q.source,
                grade=dup.grade,
                xp_earned=0,
                combo=0,
                user_elo=state.elo_rating,
                skill_mastery={q.skill_id: state.p_known},
                session_accuracy=0.0,
            )

    session_result = await db.execute(
        select(StudySession).where(StudySession.id == req.session_id, StudySession.user_id == user.id)
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if session.ended_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session already ended")
    # S.4: solo se acepta la pregunta que esta sesión acaba de servir, y solo
    # una vez — en cuanto se responde, `current_question_id` avanza a la
    # siguiente (o a None), así que repetir el mismo `question_id` ya no
    # coincide sin necesitar una comprobación aparte de "ya respondida".
    if session.current_question_id != req.question_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "question_id is not the one this session served (or it was already answered)",
        )

    question_result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = question_result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    declared_unknown = req.declared_unknown
    if declared_unknown:
        # An explicit "I don't know" is never correct, but it is not a wrong
        # answer either: it carries no guessing and no slip, so the models below
        # treat it through a separate path.
        correct = False
    elif question.type in _EXEC_TYPES:
        # Some exec questions ask the learner to print a message, and the message
        # is legitimately different per language ("Cannot divide by zero" vs "No
        # se puede dividir entre cero"). Grading against the Spanish string no
        # matter who is answering marked correct English work as wrong, while
        # the client — which compares against the learner's own language — said
        # it was right. Grade against the language the learner is actually using.
        expected = question.correct_answer_es
        if user.language == "en" and question.correct_answer_en is not None:
            expected = question.correct_answer_en
        # The server grades; it never takes the client's word for it. Until
        # 2026-10-01 the web client sent no exec_output at all, so every one of
        # these answers fell into a fallback that trusted `selected_index == 1`:
        # anyone could mark any executable exercise as solved straight from the
        # API (seen in production: q130103_fbe001 at 20:43:49 UTC). Missing
        # evidence now counts as a wrong answer.
        submitted = req.answer_text if question.type == "fill_blank" else req.exec_output
        if expected is None or submitted is None:
            logger.warning(
                "%s question %s answered without %s — graded as wrong",
                question.type,
                question.id,
                "answer_text" if question.type == "fill_blank" else "exec_output",
            )
            correct = False
        elif question.type == "fill_blank":
            # Same rule the client shows: trimmed, case-insensitive text.
            correct = submitted.strip().casefold() == expected.strip().casefold()
        else:
            correct = submitted.strip() == expected.strip()
    else:
        correct = req.selected_index is not None and req.selected_index == question.correct_index
    now = _now()

    state = await _get_or_create_skill_state(db, user.id, question.skill_id)

    p_known_before = state.p_known
    elo_before = state.elo_rating

    # --- Elo: two-sided update between user's per-skill ability and item difficulty ---
    user_entity = EloEntity(rating=state.elo_rating, interactions=state.attempts)
    item_entity = EloEntity(rating=question.elo_rating, interactions=30)
    user_entity, item_entity, expected_p = elo.update(user_entity, item_entity, correct)
    state.elo_rating = user_entity.rating
    if not declared_unknown:
        question.elo_rating = item_entity.rating
    # On "I don't know" the learner's rating still falls — they could not answer,
    # and the selector should ease off. The item's rating is left alone: nobody
    # attempted it, so the interaction says nothing about how hard it is.

    # --- BKT: skill mastery update ---
    bkt_state = SkillState(
        skill_id=question.skill_id,
        p_known=state.p_known,
        attempts=state.attempts,
        correct=state.correct_count,
    )
    if declared_unknown:
        bkt.update_unknown(bkt_state)
        state.unknown_count += 1
    else:
        bkt.update(bkt_state, correct)
    state.p_known = bkt_state.p_known
    state.attempts = bkt_state.attempts
    state.correct_count = bkt_state.correct

    # --- FSRS: skill-level spaced-repetition scheduling ---
    grade = _grade_from_response(correct, req.response_time_ms, question.expected_time_ms)
    card = Card(
        stability=state.fsrs_stability,
        difficulty=state.fsrs_difficulty,
        reps=max(0, bkt_state.attempts - 1),
        due=_ensure_aware(state.fsrs_due),
        last_review=_ensure_aware(state.updated_at),
        state="new" if bkt_state.attempts <= 1 else "review",
    )
    card, _log = fsrs.review(card, grade, now)
    state.fsrs_stability = card.stability
    state.fsrs_difficulty = card.difficulty
    state.fsrs_due = card.due

    # --- Persist the raw response event ---
    response = Response(
        session_id=session.id,
        question_id=question.id,
        correct=correct,
        grade=grade,
        response_time_ms=req.response_time_ms,
        question_version=question.content_version,
        declared_unknown=declared_unknown,
        event_id=req.event_id,
        p_known_before=p_known_before,
        p_known_after=state.p_known,
        elo_before=elo_before,
        elo_after=state.elo_rating,
        expected_p=expected_p,
    )
    db.add(response)
    await db.flush()

    combo = await _current_combo(db, session.id)
    xp = _calculate_xp(correct, combo, grade)

    # Fire first_quiz_answer event on the user's very first answer ever.
    if session.questions_answered == 0:
        from app.services.analytics import (
            track as _analytics_track,  # local import to avoid cycles
        )
        await _analytics_track(db, "first_quiz_answer", user_id=user.id)

    session.questions_answered += 1
    if correct:
        session.correct_count += 1
    session.max_combo = max(session.max_combo, combo)
    session.xp_earned += xp

    user.total_xp += xp
    user.level = _level_from_xp(user.total_xp)
    _update_streak(user, now)

    # Fuera de las ligas (35.4) no se crea ni se suma entrada de liga.
    league_entry = None if user.leagues_opt_out else await get_or_create_current_entry(db, user)
    if league_entry is not None:
        league_entry.xp_earned += xp

    # Cupo Free (39.4): con las preguntas nuevas del día gastadas no se sirve otra;
    # el cliente ve `next_question: null` y cierra la sesión con sus resultados.
    quota_reached = await content_quota.new_questions_left(db, user, session.mode) == 0

    # Pick the next question, avoiding every item already served in this session
    # while the skill still has others; only when they are all used up does it
    # fall back to "not the one just answered". Excluding only the last one let
    # a new learner, with a single skill unlocked, cycle over the same five.
    # Same scope the session was opened with: passing None here is how
    # «Practicar» on one module drifted to other tracks from question two.
    next_question: Question | None = None
    next_expected_p: float | None = None
    strategy = None
    pool = None
    if not quota_reached:
        candidate_skill_ids, pool = await _candidate_skill_ids(
            db, user, session.mode, session.track_id, session.skill_id
        )
        next_skill_id, strategy = await _select_skill(db, user, candidate_skill_ids)
        next_skill_id = next_skill_id or question.skill_id
        served = set(
            (await db.execute(select(Response.question_id).where(Response.session_id == session.id)))
            .scalars()
            .all()
        ) | {question.id}
        next_question, next_expected_p = await _select_question(
            db, user, next_skill_id, exclude_question_ids=served
        )
        if next_question is None:
            next_question, next_expected_p = await _select_question(
                db, user, next_skill_id, exclude_question_ids={question.id}
            )
    next_question_public = await _to_question_public(next_question) if next_question else None
    next_reason: SelectionReason | None = None
    if next_question:
        next_reason = SelectionReason(
            pool=pool or "",
            skill_strategy=strategy,
            difficulty_target=TARGET_SUCCESS_PROBABILITY,
            expected_p=next_expected_p,
        )

    session_accuracy = session.correct_count / max(1, session.questions_answered)

    session.current_question_id = next_question.id if next_question else None
    await apply_quiz_event(db, user, correct, xp, combo)
    await db.commit()

    return QuizAnswerResponse(
        correct=correct,
        correct_index=question.correct_index,
        explanation_es=question.explanation_es,
        explanation_en=question.explanation_en,
        source=question.source,
        grade=grade,
        xp_earned=xp,
        combo=combo,
        user_elo=state.elo_rating,
        next_review=state.fsrs_due.isoformat() if state.fsrs_due else None,
        skill_mastery={question.skill_id: state.p_known},
        session_accuracy=round(session_accuracy, 4),
        next_question=next_question_public,
        next_selection_reason=next_reason,
        quota_reached=quota_reached,
    )


async def end_session(db: AsyncSession, user: User, req: QuizEndRequest) -> QuizEndResponse:
    result = await db.execute(
        select(StudySession).where(StudySession.id == req.session_id, StudySession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    now = _now()
    if session.ended_at is None:
        session.ended_at = now
        await db.commit()

    duration = int(
        (_ensure_aware(session.ended_at) - _ensure_aware(session.started_at)).total_seconds()  # type: ignore[operator]
    )
    accuracy = session.correct_count / max(1, session.questions_answered)

    return QuizEndResponse(
        total_questions=session.questions_answered,
        correct=session.correct_count,
        accuracy=round(accuracy, 4),
        max_combo=session.max_combo,
        xp_earned=session.xp_earned,
        duration_seconds=duration,
    )


async def apply_exam_evidence(
    db: AsyncSession,
    user: User,
    question: Question,
    correct: bool,
    *,
    response_time_ms: int,
) -> float:
    """Feeds one exam answer to the engine exactly as a quiz answer is fed (17.2).

    This is what makes module test-out honest. The alternative — writing
    `p_known = 1.0` across the module when someone passes — would put a mastery
    figure on screen for skills the draw may never have asked about, which is
    red line 1 in the one place a learner is most likely to believe us.

    Going through BKT/Elo/FSRS instead means passing a test-out raises mastery
    exactly as far as the answers support: enough to clear
    `min_mastery_to_unlock` on the skills that were actually tested, and not one
    point further. Skills the draw never touched keep the mastery they had.

    No `Response` row is written and no XP is awarded: an exam is an assessment,
    not a study session, and counting it as both would inflate streaks and the
    answered-question totals that the analytics of 5.4 report.

    Returns the skill's mastery after the update.
    """
    state = await _get_or_create_skill_state(db, user.id, question.skill_id)

    user_entity = EloEntity(rating=state.elo_rating, interactions=state.attempts)
    item_entity = EloEntity(rating=question.elo_rating, interactions=30)
    user_entity, item_entity, _expected = elo.update(user_entity, item_entity, correct)
    state.elo_rating = user_entity.rating
    question.elo_rating = item_entity.rating

    bkt_state = SkillState(
        skill_id=question.skill_id,
        p_known=state.p_known,
        attempts=state.attempts,
        correct=state.correct_count,
    )
    bkt.update(bkt_state, correct)
    state.p_known = bkt_state.p_known
    state.attempts = bkt_state.attempts
    state.correct_count = bkt_state.correct

    grade = _grade_from_response(correct, response_time_ms, question.expected_time_ms)
    card = Card(
        stability=state.fsrs_stability,
        difficulty=state.fsrs_difficulty,
        reps=max(0, bkt_state.attempts - 1),
        due=_ensure_aware(state.fsrs_due),
        last_review=_ensure_aware(state.updated_at),
        state="new" if bkt_state.attempts <= 1 else "review",
    )
    card, _log = fsrs.review(card, grade, _now())
    state.fsrs_stability = card.stability
    state.fsrs_difficulty = card.difficulty
    state.fsrs_due = card.due

    return state.p_known
