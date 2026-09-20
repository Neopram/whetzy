"""Computer-Adaptive Testing (CAT) placement flow.

Because HTTP is stateless, the `PlacementEngine`/`PlacementState` from
`app.services.engine.placement` are rebuilt on every request from the
`Response` rows already persisted for the placement `StudySession`. This
keeps the engine module itself pure/stateless while the API stays
horizontally scalable (no in-memory session affinity required).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Module, Question, Skill, Track
from app.models.session import Response, StudySession
from app.models.user import User
from app.schemas.content import QuestionPublic
from app.schemas.placement import (
    ModuleSkipRecommendation,
    PlacementAnswerResponse,
    PlacementResultResponse,
    PlacementStartResponse,
)
from app.services.engine import IRTItem, PlacementEngine, PlacementState

ELO_TO_LOGIT_SCALE = 400.0 / 2.302585093  # 400 / ln(10), matches Elo<->IRT equivalence


def _now() -> datetime:
    return datetime.now(UTC)


def _elo_to_irt_difficulty(elo_rating: float) -> float:
    return (elo_rating - 1500.0) / ELO_TO_LOGIT_SCALE


#: Tipos que se responden eligiendo una opcion, que es el unico canal que
#: tiene `PlacementAnswerRequest` (`selected_index`). El pool los incluia
#: todos, asi que una sesion podia servir un `sql_exec` sin opciones: el
#: alumno se quedaba sin forma de contestar y la prueba no avanzaba.
#: `multiple_choice` esta aqui porque el banco usa ese nombre en 1.015
#: preguntas ademas de `mcq`; dejarlo fuera vaciaba el pool de los tracks de
#: certificacion enteros.
_TIPOS_RESPONDIBLES = ("mcq", "multiple_choice", "true_false", "code_output")


async def _track_item_pool(db: AsyncSession, track_id: str) -> list[IRTItem]:
    result = await db.execute(
        select(Question)
        .join(Skill, Skill.id == Question.skill_id)
        .join(Module, Module.id == Skill.module_id)
        .where(Module.track_id == track_id)
        .where(Question.type.in_(_TIPOS_RESPONDIBLES))
    )
    questions = result.scalars().all()
    return [
        IRTItem(
            item_id=q.id,
            difficulty=_elo_to_irt_difficulty(q.elo_rating),
            discrimination=q.discrimination,
            guessing=q.guessing,
            skill_ids=[q.skill_id],
        )
        for q in questions
    ]


async def _questions_by_id(db: AsyncSession, question_ids: list[str]) -> dict[str, Question]:
    if not question_ids:
        return {}
    result = await db.execute(select(Question).where(Question.id.in_(question_ids)))
    return {q.id: q for q in result.scalars().all()}


async def _rebuild_state(
    db: AsyncSession, engine: PlacementEngine, session_id: uuid.UUID
) -> PlacementState:
    """Replay all persisted responses for this placement session through the
    engine to reconstruct ability_estimate/ability_se/skill_estimates."""
    result = await db.execute(
        select(Response).where(Response.session_id == session_id).order_by(Response.created_at)
    )
    responses = result.scalars().all()

    state = PlacementState()
    for resp in responses:
        item = engine.items.get(resp.question_id)
        if item is None:
            continue
        engine.update_ability(state, item, resp.correct)
    return state


async def _get_track_or_404(db: AsyncSession, track_id: str) -> Track:
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    if track is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Track not found")
    return track


async def _get_session_or_404(
    db: AsyncSession, user: User, session_id: uuid.UUID
) -> StudySession:
    result = await db.execute(
        select(StudySession).where(
            StudySession.id == session_id,
            StudySession.user_id == user.id,
            StudySession.mode == "placement",
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placement session not found")
    return session


async def _session_track_id(db: AsyncSession, session: StudySession) -> str | None:
    result = await db.execute(
        select(Module.track_id)
        .join(Skill, Skill.module_id == Module.id)
        .join(Question, Question.skill_id == Skill.id)
        .join(Response, Response.question_id == Question.id)
        .where(Response.session_id == session.id)
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


async def start_placement(db: AsyncSession, user: User, track_id: str) -> PlacementStartResponse:
    await _get_track_or_404(db, track_id)

    session = StudySession(user_id=user.id, mode="placement")
    db.add(session)
    await db.flush()

    items = await _track_item_pool(db, track_id)
    if not items:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Track {track_id} has no questions that can be answered by choosing "
            f"an option, so no placement test can be built from it",
        )
    # Un pool mas corto que `min_questions` NO es un error: el motor se queda
    # sin items, da la prueba por terminada y lo refleja en `reliability`. La
    # interfaz enseña esa fiabilidad; inventarse aqui un minimo rechazaba
    # sesiones que funcionan.

    engine = PlacementEngine(items=items)
    state = PlacementState()
    first_item = engine.select_next_item(state)

    question_public = None
    if first_item:
        questions = await _questions_by_id(db, [first_item.item_id])
        q = questions.get(first_item.item_id)
        if q:
            question_public = QuestionPublic.model_validate(q)

    await db.commit()

    return PlacementStartResponse(
        session_id=session.id,
        track_id=track_id,
        question=question_public,
        questions_answered=0,
    )


async def answer_placement(
    db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    question_id: str,
    selected_index: int | None,
    response_time_ms: int,
) -> PlacementAnswerResponse:
    session = await _get_session_or_404(db, user, session_id)
    track_id = await _session_track_id(db, session)

    question_result = await db.execute(select(Question).where(Question.id == question_id))
    question = question_result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    if track_id is None:
        # First answer of the session — derive the track from this question.
        module_result = await db.execute(
            select(Module.track_id).join(Skill, Skill.module_id == Module.id).where(
                Skill.id == question.skill_id
            )
        )
        track_id = module_result.scalar_one()

    correct = selected_index is not None and selected_index == question.correct_index

    db.add(
        Response(
            session_id=session.id,
            question_id=question.id,
            correct=correct,
            grade=4 if correct else 1,
            response_time_ms=response_time_ms,
        )
    )
    await db.flush()

    items = await _track_item_pool(db, track_id)
    engine = PlacementEngine(items=items)
    state = await _rebuild_state(db, engine, session.id)

    finished = engine.should_stop(state)
    next_question_public = None

    if not finished:
        next_item = engine.select_next_item(state)
        if next_item is None:
            finished = True
        else:
            questions = await _questions_by_id(db, [next_item.item_id])
            q = questions.get(next_item.item_id)
            if q:
                next_question_public = QuestionPublic.model_validate(q)

    session.questions_answered = len(state.responses)
    session.correct_count = sum(1 for _, c in state.responses if c)
    if finished and session.ended_at is None:
        session.ended_at = _now()

    await db.commit()

    return PlacementAnswerResponse(
        correct=correct,
        ability_estimate=round(state.ability_estimate, 3),
        ability_se=round(state.ability_se, 3),
        questions_answered=len(state.responses),
        finished=finished,
        next_question=next_question_public,
    )


async def get_placement_result(
    db: AsyncSession, user: User, session_id: uuid.UUID
) -> PlacementResultResponse:
    session = await _get_session_or_404(db, user, session_id)
    track_id = await _session_track_id(db, session)
    if track_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No answers recorded for this session yet")

    items = await _track_item_pool(db, track_id)
    engine = PlacementEngine(items=items)
    state = await _rebuild_state(db, engine, session.id)
    result = engine.get_placement_result(state)

    modules_result = await db.execute(
        select(Module).options(selectinload(Module.skills)).where(Module.track_id == track_id).order_by(Module.order)
    )
    modules = modules_result.scalars().all()

    recommendations: list[ModuleSkipRecommendation] = []
    for module in modules:
        skill_ids = [s.id for s in module.skills]
        relevant = [state.skill_estimates[sid] for sid in skill_ids if sid in state.skill_estimates]
        total = sum(r["total"] for r in relevant)
        correct = sum(r["correct"] for r in relevant)
        accuracy = correct / total if total else 0.0
        can_skip = engine.can_skip_module(state, skill_ids)
        recommendations.append(
            ModuleSkipRecommendation(
                module_id=module.id,
                module_name_es=module.name_es,
                module_name_en=module.name_en,
                accuracy=round(accuracy, 3),
                questions_seen=total,
                can_skip=can_skip,
            )
        )

    return PlacementResultResponse(
        session_id=session.id,
        track_id=track_id,
        ability_estimate=result["ability_estimate"],
        ability_se=result["ability_se"],
        total_questions=result["total_questions"],
        correct=result["correct"],
        accuracy=result["accuracy"],
        reliability=result["reliability"],
        skill_mastery=result["skill_mastery"],
        module_recommendations=recommendations,
    )
