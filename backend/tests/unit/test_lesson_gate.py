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
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, ["sk1", "sk2"])
    assert got == set()


@pytest.mark.asyncio
async def test_viewed_skill_ids_empty_input_short_circuits(db_session, user) -> None:
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, [])
    assert got == set()


@pytest.mark.asyncio
async def test_record_lesson_seen_then_viewed(db_session, user) -> None:
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, ["sk1", "sk2"])
    assert got == {"sk1"}


@pytest.mark.asyncio
async def test_record_lesson_seen_is_idempotent(db_session, user) -> None:
    """Reabrir una lección ya vista no debe reventar por la PK duplicada."""
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    await lesson_gate.record_lesson_seen(db_session, user.id, "sk1")
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, ["sk1"])
    assert got == {"sk1"}


@pytest.mark.asyncio
async def test_viewed_skill_ids_is_scoped_per_user(db_session, user) -> None:
    other_user_id = uuid.uuid4()
    await lesson_gate.record_lesson_seen(db_session, other_user_id, "sk1")
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()


@pytest.mark.asyncio
async def test_lesson_views_flag_off_does_not_gate(db_session, user) -> None:
    """`lesson_views` (39.4) y `lesson_completions` (32.4) son tablas distintas:
    una fila en la primera nunca cuenta para el bloqueo del quiz."""
    from datetime import date

    from app.models.lesson_view import LessonView

    db_session.add(LessonView(user_id=user.id, skill_id="sk1", day=date.today()))
    await db_session.commit()
    got = await lesson_gate.viewed_skill_ids(db_session, user.id, ["sk1"])
    assert got == set()
