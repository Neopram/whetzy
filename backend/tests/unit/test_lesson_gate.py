"""Unit tests for `app.services.lesson_gate` (32.4).

Separate from `lesson_views` (39.4's Free-quota counter) on purpose: that
table only gets written when the quota flag is on and applies to the user,
so it is empty for Pro/Pro Max/owner/admin or with the flag off -- useless
as a universal "has this user ever opened this lesson" signal.
"""

from __future__ import annotations

import uuid

import pytest

from app.services import lesson_gate


@pytest.mark.asyncio
async def test_viewed_skill_ids_empty_for_unseen_skills(db_session, user) -> None:
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1", "sk2"])
    assert got == set()


@pytest.mark.asyncio
async def test_viewed_skill_ids_empty_input_short_circuits(db_session, user) -> None:
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, [])
    assert got == set()


@pytest.mark.asyncio
async def test_record_lesson_seen_then_viewed(db_session, user) -> None:
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1", "sk2"])
    assert got == {"sk1"}


@pytest.mark.asyncio
async def test_record_lesson_seen_is_idempotent(db_session, user) -> None:
    """Reabrir una lección ya vista no debe reventar por la PK duplicada."""
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1"])
    assert got == {"sk1"}


@pytest.mark.asyncio
async def test_viewed_skill_ids_is_scoped_per_user(db_session, user) -> None:
    other_user_id = uuid.uuid4()
    await lesson_gate.record_lesson_seen(db_session, other_user_id, "sk1")
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()


@pytest.mark.asyncio
async def test_lesson_views_flag_off_does_not_gate(db_session, user) -> None:
    """`lesson_views` (39.4) y `lesson_completions` (32.4) son tablas distintas:
    una fila en la primera nunca cuenta para el bloqueo del quiz."""
    from datetime import date

    from app.models.lesson_view import LessonView

    db_session.add(LessonView(user_id=user.id, skill_id="sk1", day=date.today()))
    await db_session.commit()
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()


# ── Historial previo al bloqueo (2026-09-30) ────────────────────────────────
# `lesson_completions` nació vacía el 2026-09-27 y hasta 43.5 un skill
# practicado contaba como lección vista. Desde 43.5 (ADR-65 D7) ya no: ese
# historial lo rellena la migración `20261017_lesson_backfill`, y practicar no
# desbloquea nada por sí solo (antes la prueba de nivel desbloqueaba así lo que
# salía en ella).


async def _practiced(db_session, user_id, skill_id: str, attempts: int) -> None:
    from app.models.user import UserSkillState

    db_session.add(UserSkillState(user_id=user_id, skill_id=skill_id, attempts=attempts))
    await db_session.commit()


@pytest.mark.asyncio
async def test_a_practiced_skill_no_longer_counts_as_seen(db_session, user) -> None:
    await _practiced(db_session, user.id, "sk1", attempts=3)
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1", "sk2"])
    assert got == set()


@pytest.mark.asyncio
async def test_a_state_row_without_attempts_does_not_count(db_session, user) -> None:
    """El selector crea el estado con attempts=0 antes de responder nada."""
    await _practiced(db_session, user.id, "sk1", attempts=0)
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()


@pytest.mark.asyncio
async def test_another_users_practice_does_not_count(db_session, user) -> None:
    await _practiced(db_session, uuid.uuid4(), "sk1", attempts=5)
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()


@pytest.mark.asyncio
async def test_only_the_seen_lesson_unlocks_not_the_practice(db_session, user) -> None:
    """43.5 (D7): antes salía {"sk1", "sk2"}; practicar ya no cuenta."""
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    await _practiced(db_session, user.id, "sk2", attempts=1)
    got = await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, ["sk1", "sk2", "sk3"])
    assert got == {"sk1"}
