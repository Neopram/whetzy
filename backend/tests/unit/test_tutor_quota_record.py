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

    async def lying_once(
        db: AsyncSession, user_id: uuid.UUID, day: date, *, tokens: int = 0
    ) -> int | None:
        calls["n"] += 1
        if calls["n"] == 1:
            return None  # simula el UPDATE que no ve todavía la fila ganadora
        return await real_increment(db, user_id, day, tokens=tokens)

    monkeypatch.setattr(tutor_quota, "_increment_if_exists", lying_once)

    result = await tutor_quota.record(db_session, user.id, DAY)

    assert result == 2  # el reintento encontró la fila real y la incrementó
    assert await tutor_quota.used_on(db_session, user.id, DAY) == 2


# ── reserve / settle / release (41.17) ─────────────────────────────────────────


async def _usage(db: AsyncSession, user_id: uuid.UUID, day: date) -> TutorUsage:
    row = await db.get(TutorUsage, (user_id, day))
    assert row is not None
    return row


async def test_reserve_creates_the_first_row_of_the_day(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    ok = await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=12_000
    )
    assert ok is True
    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 1
    assert row.tokens_used == 12_000


async def test_reserve_increments_an_existing_row_under_the_limit(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    for _ in range(3):
        assert await tutor_quota.reserve(
            db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=1_000
        )
    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 3
    assert row.tokens_used == 3_000


async def test_reserve_fails_exactly_at_the_explanation_limit_without_leaking_a_slot(
    db_session: AsyncSession,
) -> None:
    """41.17: el chequeo del límite y la reserva son el mismo UPDATE -- una
    petición que llega con el contador ya al límite se rechaza sin tocar la
    fila, en vez de colarse por una ventana entre comprobar y apuntar (el
    bug real: con el límite en 20, Plus podía recibir 21)."""
    user = await _user(db_session)
    db_session.add(TutorUsage(user_id=user.id, day=DAY, explanations=20, tokens_used=1_000))
    await db_session.commit()

    ok = await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=1_000
    )
    assert ok is False
    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 20  # sin cambios: la reserva fallida no deja rastro
    assert row.tokens_used == 1_000


async def test_reserve_fails_exactly_at_the_token_limit(db_session: AsyncSession) -> None:
    user = await _user(db_session)
    db_session.add(TutorUsage(user_id=user.id, day=DAY, explanations=1, tokens_used=150_000))
    await db_session.commit()

    ok = await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=1_000
    )
    assert ok is False
    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 1
    assert row.tokens_used == 150_000


async def test_reserve_never_blocks_when_both_limits_are_none(db_session: AsyncSession) -> None:
    """Pro Max/dueño/admin (ADR-49): daily_limit/daily_token_limit dan None,
    y reserve() nunca debe bloquearlos -- pero sigue contando su uso."""
    user = await _user(db_session)
    db_session.add(TutorUsage(user_id=user.id, day=DAY, explanations=999, tokens_used=999_999))
    await db_session.commit()

    ok = await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=None, token_limit=None, token_estimate=1_000
    )
    assert ok is True
    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 1000
    assert row.tokens_used == 1_000_999


async def test_settle_adjusts_the_reservation_to_the_real_token_count(
    db_session: AsyncSession,
) -> None:
    user = await _user(db_session)
    assert await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=12_000
    )
    await db_session.commit()

    await tutor_quota.settle(db_session, user.id, DAY, token_estimate=12_000, actual_tokens=842)
    await db_session.commit()

    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 1  # la explicación sí se sirvió, eso no cambia
    assert row.tokens_used == 842  # pero el gasto real sustituye a la reserva peor-caso


async def test_release_undoes_a_reservation_after_a_provider_failure(
    db_session: AsyncSession,
) -> None:
    """"Un fallo del proveedor no gasta cupo" -- con la reserva atómica,
    ahora hay que devolverla explícitamente en vez de solo no apuntarla."""
    user = await _user(db_session)
    assert await tutor_quota.reserve(
        db_session, user.id, DAY, explanation_limit=20, token_limit=150_000, token_estimate=12_000
    )
    await db_session.commit()
    assert await tutor_quota.used_on(db_session, user.id, DAY) == 1

    await tutor_quota.release(db_session, user.id, DAY, token_estimate=12_000)
    await db_session.commit()

    row = await _usage(db_session, user.id, DAY)
    assert row.explanations == 0
    assert row.tokens_used == 0
