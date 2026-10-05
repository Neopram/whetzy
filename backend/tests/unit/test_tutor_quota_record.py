"""tutor_quota.record bajo llamadas concurrentes al tutor (S.17).

Dos peticiones a /tutor/explain a la vez (dos pestañas, o un script) podían
leer la misma fila de `tutor_usage` antes de que ninguna hiciera commit: la
que comiteara segunda pisaba el incremento de la primera con un lee-suma-
escribe hecho en Python, y dos explicaciones servidas (dos llamadas reales
al LLM) contaban como una sola en el cupo.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.tutor_usage import TutorUsage
from app.models.user import User
from app.services import tutor_quota

DAY = date(2026, 1, 15)


async def _user(db: AsyncSession) -> User:
    tag = uuid.uuid4().hex[:8]
    u = User(
        id=uuid.uuid4(),
        email=f"tutorq-{tag}@whetzy.test",
        username=f"tutorq{tag}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Tutor Quota",
        language="es",
    )
    db.add(u)
    await db.commit()
    return u


@pytest.mark.asyncio
async def test_record_creates_the_first_row_of_the_day(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    assert await tutor_quota.record(db_session, user.id, DAY) == 1


@pytest.mark.asyncio
async def test_record_increments_an_existing_row(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    assert await tutor_quota.record(db_session, user.id, DAY) == 1
    assert await tutor_quota.record(db_session, user.id, DAY) == 2
    assert await tutor_quota.record(db_session, user.id, DAY) == 3


@pytest.mark.asyncio
async def test_record_keeps_separate_users_and_days_apart(db_session: AsyncSession) -> None:
    alice = await _user(db_session)
    bob = await _user(db_session)
    assert await tutor_quota.record(db_session, alice.id, DAY) == 1
    assert await tutor_quota.record(db_session, bob.id, DAY) == 1
    other_day = date(2026, 1, 16)
    assert await tutor_quota.record(db_session, alice.id, other_day) == 1
    assert await tutor_quota.used_on(db_session, alice.id, DAY) == 1


@pytest.mark.asyncio
async def test_record_survives_a_row_created_between_its_update_and_its_insert(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simula la carrera: otra petición ya creó la fila de hoy justo entre
    el `UPDATE` que no encontró nada y el `INSERT` de esta llamada."""
    user = await _user(db_session)

    winner = TutorUsage(user_id=user.id, day=DAY, explanations=1)
    db_session.add(winner)
    await db_session.commit()

    real_increment = tutor_quota._increment_if_exists
    calls = {"n": 0}

    async def lying_once(db: AsyncSession, user_id: uuid.UUID, day: date) -> int | None:
        calls["n"] += 1
        if calls["n"] == 1:
            return None  # simula el UPDATE que no ve todavía la fila ganadora
        return await real_increment(db, user_id, day)

    monkeypatch.setattr(tutor_quota, "_increment_if_exists", lying_once)

    result = await tutor_quota.record(db_session, user.id, DAY)

    assert result == 2  # el reintento encontró la fila real y la incrementó
    assert await tutor_quota.used_on(db_session, user.id, DAY) == 2
