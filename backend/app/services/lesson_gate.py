"""Bloqueo del quiz hasta ver la lección del skill (32.4, decisión del dueño 2026-09-27).

Independiente del cupo Free (`content_quota.py`): se registra siempre que
haya sesión, sin mirar `FREE_DAILY_QUOTA_ENABLED` ni el tier del usuario --
gatear el quiz y limitar el cupo son dos reglas de negocio distintas que
comparten el mismo evento (abrir una lección) pero no la misma tabla.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Skill
from app.models.exam import MockExamAttempt
from app.models.lesson_completion import LessonCompletion


async def record_lesson_seen(db: AsyncSession, user_id: uuid.UUID, skill_id: str) -> None:
    """Idempotente: reabrir una lección ya vista no hace nada."""
    try:
        async with db.begin_nested():
            db.add(LessonCompletion(user_id=user_id, skill_id=skill_id))
            await db.flush()
    except IntegrityError:
        return
    await db.commit()


async def lesson_viewed_skill_ids(
    db: AsyncSession, user_id: uuid.UUID, skill_ids: list[str]
) -> set[str]:
    """De `skill_ids`, los que tienen la lección abierta alguna vez (32.4). Es lo
    que la interfaz enseña como «lección vista»: ni la prueba de nivel ni el
    test-out la marcan (ADR-65 D4, H.60)."""
    if not skill_ids:
        return set()
    seen = await db.execute(
        select(LessonCompletion.skill_id).where(
            LessonCompletion.user_id == user_id, LessonCompletion.skill_id.in_(skill_ids)
        )
    )
    return set(seen.scalars())


async def _passed_test_out_module_ids(db: AsyncSession, user_id: uuid.UUID) -> set[str]:
    rows = await db.execute(
        select(MockExamAttempt.module_id, MockExamAttempt.report).where(
            MockExamAttempt.user_id == user_id,
            MockExamAttempt.kind == "test_out",
            MockExamAttempt.module_id.is_not(None),
            MockExamAttempt.report.is_not(None),
        )
    )
    return {
        module_id
        for module_id, report in rows.all()
        if module_id and isinstance(report, dict) and report.get("passed") is True
    }


async def practice_unlocked_skill_ids(
    db: AsyncSession, user_id: uuid.UUID, skill_ids: list[str]
) -> set[str]:
    """De `skill_ids`, los que se pueden practicar (43.5, ADR-65 D7 y H.60).

    Hace falta la lección vista, salvo que el módulo de la skill se haya
    superado por test-out o haya empezado con ventaja en una prueba de nivel
    terminada (la regla de 43.3: ≥ 70 % de ≥ 2 preguntas). Antes también contaba
    `UserSkillState.attempts > 0`, y contestar la prueba de nivel ya
    desbloqueaba lo que salía en ella; el historial de antes del 2026-09-27, que
    era lo que esa regla cubría, lo rellena la migración `20261017_lesson_backfill`.
    """
    if not skill_ids:
        return set()
    unlocked = await lesson_viewed_skill_ids(db, user_id, skill_ids)
    pending = [sid for sid in skill_ids if sid not in unlocked]
    if not pending:
        return unlocked
    from app.services.placement import strong_module_ids

    modules = await _passed_test_out_module_ids(db, user_id) | await strong_module_ids(db, user_id)
    if not modules:
        return unlocked
    rows = await db.execute(
        select(Skill.id).where(Skill.id.in_(pending), Skill.module_id.in_(modules))
    )
    return unlocked | set(rows.scalars())
