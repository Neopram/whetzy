"""Computer-Adaptive Testing (CAT) placement flow.

Because HTTP is stateless, the `PlacementEngine`/`PlacementState` from
`app.services.engine.placement` are rebuilt on every request from the
`Response` rows already persisted for the placement `StudySession`. This
keeps the engine module itself pure/stateless while the API stays
horizontally scalable (no in-memory session affinity required).
"""

from __future__ import annotations

import random
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Module, Question, Skill, Track
from app.models.session import Response, StudySession
from app.models.user import User, UserSkillState
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


#: 43.3 (ADR-65 D3): 20 preguntas exactas. Las 15 primeras van estratificadas,
#: 5 por banda y en orden (básica, intermedia, avanzada), repartidas por
#: módulos; las 5 últimas son adaptativas en la banda frontera.
PLACEMENT_LENGTH = 20
PER_BAND = 5
BANDS = ("basic", "intermediate", "advanced")
_STRATIFIED = PER_BAND * len(BANDS)
_TIER_BAND = {"easy": "basic", "medium": "intermediate", "hard": "advanced", "expert": "advanced"}
#: Una banda «se supera» con 3 de 5 o más.
_BAND_PASS = 0.6


@dataclass(frozen=True)
class PoolItem:
    item: IRTItem
    band: str
    module_id: str


async def _track_pool(db: AsyncSession, track_id: str) -> list[PoolItem]:
    """Preguntas respondibles del track con su banda y su módulo.

    La banda es el `difficulty_tier` si el track tiene preguntas de las tres
    bandas, al menos `PER_BAND` de cada una. Si no, es el tercio del módulo
    dentro del track: 16 tracks del banco no traen tier y el loader les pone
    «medium» a todas, así que el tier no distingue nada.
    """
    result = await db.execute(
        select(Question, Module.id, Module.order)
        .join(Skill, Skill.id == Question.skill_id)
        .join(Module, Module.id == Skill.module_id)
        .where(Module.track_id == track_id)
        .where(Question.type.in_(_TIPOS_RESPONDIBLES))
        # El tipo no basta: 83 preguntas `true_false` llegaron al banco sin
        # opciones y sin `correct_index`, con la respuesta como texto. El quiz
        # y los duelos ya exigian el indice por esto mismo; filtrar solo por
        # tipo las dejaba entrar aqui, y sin indice no hay nada que pulsar ni
        # con que corregir. El contenido esta arreglado, pero la guarda se
        # queda: es una linea contra una clase entera de fallo.
        .where(Question.correct_index.is_not(None))
        # `pool != "simulacro"`: la colocacion no es el simulacro de
        # certificacion, asi que una pregunta reservada no puede aparecer
        # aqui (37.18/ADR-53 §4) — misma exclusion incondicional que
        # quiz.py/_select_question y duels.py/_pick_questions.
        .where(Question.pool != "simulacro")
    )
    rows = result.all()
    module_order = sorted({(order, mid) for _, mid, order in rows})
    third = {mid: BANDS[i * len(BANDS) // len(module_order)] for i, (_, mid) in enumerate(module_order)}
    tier_counts = Counter(_TIER_BAND.get(q.difficulty_tier, "intermediate") for q, _, _ in rows)
    by_tier = all(tier_counts[b] >= PER_BAND for b in BANDS)
    return [
        PoolItem(
            item=IRTItem(
                item_id=q.id,
                difficulty=_elo_to_irt_difficulty(q.elo_rating),
                discrimination=q.discrimination,
                guessing=q.guessing,
                skill_ids=[q.skill_id],
            ),
            band=_TIER_BAND.get(q.difficulty_tier, "intermediate") if by_tier else third[mid],
            module_id=mid,
        )
        for q, mid, _ in rows
    ]


async def _track_item_pool(db: AsyncSession, track_id: str) -> list[IRTItem]:
    return [p.item for p in await _track_pool(db, track_id)]


def _frontier_band(pool: dict[str, PoolItem], responses: list[tuple[str, bool]]) -> str:
    """La primera banda que no se supera en las estratificadas; si se superan
    todas, la avanzada."""
    for band in BANDS:
        seen = [ok for qid, ok in responses[:_STRATIFIED] if qid in pool and pool[qid].band == band]
        if seen and sum(seen) / len(seen) < _BAND_PASS:
            return band
    return BANDS[-1]


def _by_band_distance(available: list[PoolItem], band: str) -> list[PoolItem]:
    """Las disponibles de la banda pedida o, si no queda ninguna, de la más cercana."""
    target = BANDS.index(band)
    for distance in range(len(BANDS)):
        near = [p for p in available if abs(BANDS.index(p.band) - target) == distance]
        if near:
            return near
    return []


def _next_item(
    pool: list[PoolItem], engine: PlacementEngine, state: PlacementState
) -> IRTItem | None:
    n = len(state.responses)
    available = [p for p in pool if p.item.item_id not in state.administered_ids]
    if n >= PLACEMENT_LENGTH or not available:
        return None
    by_id = {p.item.item_id: p for p in pool}
    if n < _STRATIFIED:
        candidates = _by_band_distance(available, BANDS[n // PER_BAND])
        # Repartidas por módulos: el que menos preguntas lleva en la prueba.
        used = Counter(by_id[qid].module_id for qid, _ in state.responses if qid in by_id)
        fewest = min(used[p.module_id] for p in candidates)
        return random.choice([p for p in candidates if used[p.module_id] == fewest]).item
    candidates = _by_band_distance(available, _frontier_band(by_id, state.responses))
    # Adaptativas: la más informativa para la theta de ahora, dentro de la banda.
    return max(
        candidates, key=lambda p: engine.fisher_information(state.ability_estimate, p.item)
    ).item


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

    pool = await _track_pool(db, track_id)
    if not pool:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Track {track_id} has no questions that can be answered by choosing "
            f"an option, so no placement test can be built from it",
        )
    # Un pool mas corto que `min_questions` NO es un error: el motor se queda
    # sin items, da la prueba por terminada y lo refleja en `reliability`. La
    # interfaz enseña esa fiabilidad; inventarse aqui un minimo rechazaba
    # sesiones que funcionan.

    engine = PlacementEngine(items=[p.item for p in pool])
    state = PlacementState()
    first_item = _next_item(pool, engine, state)

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


#: 43.3 (ADR-65 D4): siembra por módulo, no por pregunta suelta. Un módulo con
#: al menos `MODULE_STRONG_MIN` preguntas y `MODULE_STRONG_ACCURACY` de acierto
#: deja todas sus skills en `SEED_STRONG`: practicables, no «dominadas». El
#: resto se encoge hacia el prior con `SEED_SHRINK` respuestas ficticias.
MODULE_STRONG_ACCURACY = 0.70
MODULE_STRONG_MIN = 2
SEED_STRONG = 0.60
SEED_PRIOR = 0.10
SEED_SHRINK = 2


def _module_seed(correct: int, total: int) -> float:
    if total >= MODULE_STRONG_MIN and correct / total >= MODULE_STRONG_ACCURACY:
        return SEED_STRONG
    return min((correct + SEED_SHRINK * SEED_PRIOR) / (total + SEED_SHRINK), SEED_STRONG)


def _is_strong(correct: int, total: int) -> bool:
    return _module_seed(correct, total) == SEED_STRONG and total >= MODULE_STRONG_MIN


async def _seed_by_module(
    db: AsyncSession,
    user_id: uuid.UUID,
    modules: dict[str, list[str]],
    answers: dict[str, tuple[int, int]],
) -> None:
    """Siembra `p_known` de todas las skills de cada módulo con preguntas en la prueba.

    `modules` va de módulo a sus skills; `answers`, de skill a (aciertos, total)
    en la prueba. Un módulo sin preguntas no se toca. Una skill con historial
    se queda con el mayor de los dos valores (D-18): la prueba añade evidencia,
    nunca borra dominio ganado. Los intentos solo suman en las skills que
    salieron. La prueba no marca lecciones como vistas.
    """
    all_skills = [sid for skills in modules.values() for sid in skills]
    if not all_skills:
        return
    existing = {
        row.skill_id: row
        for row in (
            await db.scalars(
                select(UserSkillState).where(
                    UserSkillState.user_id == user_id,
                    UserSkillState.skill_id.in_(all_skills),
                )
            )
        ).all()
    }
    for skills in modules.values():
        correct = sum(answers.get(sid, (0, 0))[0] for sid in skills)
        total = sum(answers.get(sid, (0, 0))[1] for sid in skills)
        if total == 0:
            continue
        new_p = _module_seed(correct, total)
        for sid in skills:
            ok, n = answers.get(sid, (0, 0))
            row = existing.get(sid)
            if row is None:
                db.add(
                    UserSkillState(
                        user_id=user_id, skill_id=sid, p_known=new_p,
                        attempts=n, correct_count=ok,
                    )
                )
                continue
            # D-18 (dueño, 2026-10-12): una fila sin intentos es solo el prior,
            # ahí manda la prueba; con historial, nunca baja.
            row.p_known = max(row.p_known, new_p) if row.attempts > 0 else new_p
            row.attempts += n
            row.correct_count += ok


async def _track_modules(db: AsyncSession, track_id: str) -> list[Module]:
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.skills))
        .where(Module.track_id == track_id)
        .order_by(Module.order)
    )
    return list(result.scalars().all())


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

    pool = await _track_pool(db, track_id)
    engine = PlacementEngine(items=[p.item for p in pool])
    state = await _rebuild_state(db, engine, session.id)

    next_item = _next_item(pool, engine, state)
    finished = next_item is None
    next_question_public = None
    if next_item is not None:
        q = (await _questions_by_id(db, [next_item.item_id])).get(next_item.item_id)
        if q:
            next_question_public = QuestionPublic.model_validate(q)

    session.questions_answered = len(state.responses)
    session.correct_count = sum(1 for _, c in state.responses if c)
    if finished and session.ended_at is None:
        session.ended_at = _now()
        modules = await _track_modules(db, track_id)
        await _seed_by_module(
            db,
            user.id,
            modules={m.id: [sk.id for sk in m.skills] for m in modules},
            answers={
                sid: (c["correct"], c["total"]) for sid, c in state.skill_estimates.items()
            },
        )

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

    pool = await _track_pool(db, track_id)
    engine = PlacementEngine(items=[p.item for p in pool])
    state = await _rebuild_state(db, engine, session.id)
    result = engine.get_placement_result(state)

    modules = await _track_modules(db, track_id)

    recommendations: list[ModuleSkipRecommendation] = []
    for module in modules:
        skill_ids = [s.id for s in module.skills]
        relevant = [state.skill_estimates[sid] for sid in skill_ids if sid in state.skill_estimates]
        total = sum(r["total"] for r in relevant)
        correct = sum(r["correct"] for r in relevant)
        accuracy = correct / total if total else 0.0
        recommendations.append(
            ModuleSkipRecommendation(
                module_id=module.id,
                module_name_es=module.name_es,
                module_name_en=module.name_en,
                accuracy=round(accuracy, 3),
                questions_seen=total,
                # D4: el módulo arranca con ventaja (skills en SEED_STRONG).
                can_skip=_is_strong(correct, total),
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
