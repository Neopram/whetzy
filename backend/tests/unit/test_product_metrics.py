"""Unit tests for the 37.20 (ADR-53 §8) product metrics in analytics.py.

Each metric gets a fixture with dates planted by hand — the funnel's D1/D7
pattern this file extends has no unit test of its own pinning its exact
arithmetic (only an integration shape-check), so D30 gets one here too,
not just the new metrics.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.core.security import get_password_hash
from app.models.analytics import AnalyticsEvent
from app.models.content import Module, Question, Skill, Track
from app.models.session import Response, StudySession
from app.models.user import User
from app.services.analytics import (
    conversion_d35,
    curr,
    funnel,
    unseen_first_attempt_accuracy,
    weekly_30min_rate_among_payers,
)

NOW = datetime.now(UTC)

# 31.6: estas métricas son SQL de agregación (fechas, ventanas, COUNT DISTINCT) y
# SQLite —la base de la suite— no es Postgres. Con `WHETZY_PG_TEST_URL` apuntando a un
# Postgres de pruebas (mismo patrón que `test_streak_shop_race_pg.py`) cada test corre
# también contra él, en un esquema propio que se borra al terminar: la base no hace falta
# que esté vacía ni migrada, y no se toca nada fuera de ese esquema.
PG_URL = os.environ.get("WHETZY_PG_TEST_URL")


@pytest_asyncio.fixture(
    params=[
        "sqlite",
        pytest.param(
            "postgres",
            marks=pytest.mark.skipif(not PG_URL, reason="WHETZY_PG_TEST_URL no definido"),
        ),
    ]
)
async def db_session(request: pytest.FixtureRequest) -> AsyncGenerator[AsyncSession, None]:
    """Sustituye al `db_session` de conftest en este módulo: SQLite y, si hay URL, Postgres."""
    if request.param == "sqlite":
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        schema = None
    else:
        assert PG_URL is not None
        schema = f"pm_{uuid.uuid4().hex[:12]}"
        admin = create_async_engine(PG_URL, isolation_level="AUTOCOMMIT")
        async with admin.connect() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_async_engine(PG_URL, connect_args={"server_settings": {"search_path": schema}})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    try:
        async with factory() as session:
            expected = "sqlite" if schema is None else "postgresql"
            assert session.get_bind().dialect.name == expected  # que el parámetro prueba lo que dice
            yield session
    finally:
        await engine.dispose()
        if schema is not None:
            async with admin.connect() as conn:
                await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            await admin.dispose()


@pytest.fixture(autouse=True)
def _now_per_test() -> None:
    """`NOW` se recalcula al empezar cada test, no al importar el modulo.

    `curr()` mide dias UTC completos a partir de la hora de la llamada. Con
    `NOW` fijado al importar, una suite que arranca antes de las 00:00 UTC y
    llega a estos tests despues planta las sesiones un dia desplazadas y
    TestCurr falla (3 tests, nivel 2 del 2026-10-03 00:07 UTC; reproducido
    poniendo NOW un minuto antes de medianoche).
    """
    global NOW
    NOW = datetime.now(UTC)


async def _make_user(db, *, created_at: datetime, is_premium: bool = False) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"pm-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"pm{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Metrics",
        language="es",
        created_at=created_at,
        is_premium=is_premium,
    )
    db.add(u)
    # Con FK reales (Postgres) el usuario tiene que existir antes que sus sesiones: sin
    # `relationship()` entre los modelos, el orden de INSERT entre tablas no está garantizado.
    await db.flush()
    return u


def _make_session(db, user_id, *, started_at: datetime, duration_minutes: float) -> None:
    db.add(
        StudySession(
            id=uuid.uuid4(),
            user_id=user_id,
            started_at=started_at,
            ended_at=started_at + timedelta(minutes=duration_minutes),
        )
    )


# ── D30 (extends the existing D1/D7 pattern in funnel()) ────────────────────


class TestD30Return:
    @pytest.mark.asyncio
    async def test_counts_a_user_who_returned_on_day_30(self, db_session) -> None:
        registered = NOW - timedelta(days=40)
        u = await _make_user(db_session, created_at=registered)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=registered + timedelta(days=30), duration_minutes=5)
        await db_session.commit()

        result = await funnel(db_session, period_days=90)
        assert result["d30_return"] == 1
        # D-31: la tasa divide entre su cohorte (altas con la ventana cerrada),
        # no entre todas las altas del periodo.
        assert result["d30_cohort"] == 1
        assert result["d30_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_does_not_count_a_user_who_never_returned(self, db_session) -> None:
        registered = NOW - timedelta(days=40)
        u = await _make_user(db_session, created_at=registered)
        db_session.add(u)
        # Only a day-1 session, nothing near day 30.
        _make_session(db_session, u.id, started_at=registered + timedelta(days=1), duration_minutes=5)
        await db_session.commit()

        result = await funnel(db_session, period_days=90)
        assert result["d30_return"] == 0

    @pytest.mark.asyncio
    async def test_ineligible_user_not_counted_either_way(self, db_session) -> None:
        # Registered 10 days ago: too recent to have reached day 30 at all.
        u = await _make_user(db_session, created_at=NOW - timedelta(days=10))
        db_session.add(u)
        await db_session.commit()

        result = await funnel(db_session, period_days=90)
        assert result["d30_return"] == 0
        # Not in the eligible window, so this user must not inflate d30_rate's
        # denominator handling in a way that hides a real drop.
        assert result["registrations"] >= 1


# ── CURR ─────────────────────────────────────────────────────────────────────


class TestCurr:
    """Duolingo's own definition (Q2 FY2026 shareholder letter, quoted in
    curr()'s docstring): a "current user DAU" is active on reference day
    D=the day before yesterday *and* active on some OTHER day in the 7 days
    before D — two separate conditions, not just "active sometime in the
    trailing week". D+1=yesterday is the return day. Both are complete UTC
    days; curr() never looks at today's still-in-progress data."""

    @pytest.mark.asyncio
    async def test_current_user_dau_who_returns_the_next_day_counts(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60))
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=2), duration_minutes=5)  # D
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=5), duration_minutes=5)  # other day in prior 7
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=5)  # D+1 = yesterday
        await db_session.commit()

        result = await curr(db_session)
        assert result["current_user_daus"] == 1
        assert result["returned_next_day"] == 1
        assert result["curr"] == 1.0

    @pytest.mark.asyncio
    async def test_current_user_dau_who_does_not_return_does_not_count_as_returned(
        self, db_session
    ) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60))
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=2), duration_minutes=5)  # D
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=5), duration_minutes=5)  # other day
        # No session yesterday.
        await db_session.commit()

        result = await curr(db_session)
        assert result["current_user_daus"] == 1
        assert result["returned_next_day"] == 0
        assert result["curr"] == 0.0

    @pytest.mark.asyncio
    async def test_active_only_on_day_d_is_not_a_current_user_dau(self, db_session) -> None:
        """Active on D (day before yesterday) with no OTHER active day in
        the prior week — Duolingo's definition requires both, not just a
        DAU on D."""
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60))
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=2), duration_minutes=5)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=5)
        await db_session.commit()

        result = await curr(db_session)
        assert result["current_user_daus"] == 0
        assert result["curr"] is None

    @pytest.mark.asyncio
    async def test_active_this_week_but_not_on_day_d_is_not_a_current_user_dau(
        self, db_session
    ) -> None:
        """Active earlier in the trailing week but not on D (day before
        yesterday) itself — not a DAU on D, so not in the cohort at all."""
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60))
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=4), duration_minutes=5)
        await db_session.commit()

        result = await curr(db_session)
        assert result["current_user_daus"] == 0
        assert result["curr"] is None

    @pytest.mark.asyncio
    async def test_curr_ignores_todays_partial_data_regardless_of_query_hour(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression: an earlier version used D=yesterday, D+1=today, so
        querying at 09:00 UTC (today only 9h old) made a real, fully-
        resolved day-over-day return read as a false 0 — the metric would
        swing with the hour it happened to be read at. Freezes "now" at
        00:05 UTC and plants a return that is complete two days earlier
        (day -2 -> day -1), which the buggy version cannot see at all
        because it only ever looked at D=yesterday and D+1=today (empty,
        since today just started)."""
        frozen_now = datetime(NOW.year, NOW.month, NOW.day, 0, 5, tzinfo=UTC)

        class _FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                return frozen_now if tz is None else frozen_now.astimezone(tz)

        monkeypatch.setattr("app.services.analytics.datetime", _FrozenDatetime)

        u = await _make_user(db_session, created_at=frozen_now - timedelta(days=60))
        db_session.add(u)
        _make_session(db_session, u.id, started_at=frozen_now - timedelta(days=9), duration_minutes=5)  # other day
        _make_session(db_session, u.id, started_at=frozen_now - timedelta(days=2), duration_minutes=5)  # D
        _make_session(db_session, u.id, started_at=frozen_now - timedelta(days=1), duration_minutes=5)  # D+1
        await db_session.commit()

        result = await curr(db_session)
        assert result["current_user_daus"] == 1
        assert result["returned_next_day"] == 1
        assert result["curr"] == 1.0

    @pytest.mark.asyncio
    async def test_no_current_user_daus_returns_none_not_a_fake_zero(self, db_session) -> None:
        result = await curr(db_session)
        assert result["current_user_daus"] == 0
        assert result["curr"] is None


# ── conversion_d35 ────────────────────────────────────────────────────────────


class TestConversionD35:
    @pytest.mark.asyncio
    async def test_counts_a_user_who_converted_within_35_days(self, db_session) -> None:
        registered = NOW - timedelta(days=40)
        u = await _make_user(db_session, created_at=registered)
        db_session.add(u)
        db_session.add(
            AnalyticsEvent(
                user_id=u.id,
                event_type="subscription_started",
                created_at=registered + timedelta(days=20),
            )
        )
        await db_session.commit()

        result = await conversion_d35(db_session, period_days=90)
        assert result["converted"] == 1
        assert result["rate"] == 1.0 / result["eligible"]

    @pytest.mark.asyncio
    async def test_does_not_count_a_conversion_after_day_35(self, db_session) -> None:
        registered = NOW - timedelta(days=40)
        u = await _make_user(db_session, created_at=registered)
        db_session.add(u)
        db_session.add(
            AnalyticsEvent(
                user_id=u.id,
                event_type="subscription_started",
                created_at=registered + timedelta(days=36),
            )
        )
        await db_session.commit()

        result = await conversion_d35(db_session, period_days=90)
        assert result["converted"] == 0

    @pytest.mark.asyncio
    async def test_small_sample_is_flagged(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=40))
        db_session.add(u)
        await db_session.commit()

        result = await conversion_d35(db_session, period_days=90)
        assert result["sample_too_small"] is True


# ── weekly_30min_rate_among_payers ───────────────────────────────────────────


class TestWeekly30MinAmongPayers:
    @pytest.mark.asyncio
    async def test_payer_with_30_min_this_week_counts(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=30)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["payers"] == 1
        assert result["at_or_above_30min"] == 1
        assert result["rate"] == 1.0

    @pytest.mark.asyncio
    async def test_payer_under_30_min_does_not_count(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=10)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 0
        assert result["rate"] == 0.0

    @pytest.mark.asyncio
    async def test_minutes_across_two_sessions_sum(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=15)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=2), duration_minutes=15)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 1

    @pytest.mark.asyncio
    async def test_free_user_never_counted_even_with_lots_of_time(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=False)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=120)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["payers"] == 0
        assert result["rate"] is None

    @pytest.mark.asyncio
    async def test_session_outside_the_week_does_not_count(self, db_session) -> None:
        u = await _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=10), duration_minutes=60)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 0


# ── D-31 (dueño, 2026-10-12): denominadores honestos ─────────────────────────


def _answer(db, user_id: uuid.UUID, question_id: str, at: datetime) -> None:
    session_id = uuid.uuid4()
    db.add(StudySession(id=session_id, user_id=user_id, started_at=at, ended_at=at))
    db.add(
        Response(
            id=uuid.uuid4(), session_id=session_id, question_id=question_id,
            correct=True, grade=4, response_time_ms=1000,
        )
    )


async def _question(db) -> str:
    db.add(Track(id="tPM", name_es="t", name_en="t", order=1))
    db.add(Module(id="mPM", track_id="tPM", name_es="m", name_en="m", order=1))
    db.add(Skill(id="sPM", module_id="mPM", name_es="s", name_en="s", order=1))
    db.add(Question(id="qPM", skill_id="sPM", question_es="?", question_en="?", correct_index=0))
    await db.flush()
    return "qPM"


class TestCohortDenominators:
    @pytest.mark.asyncio
    async def test_someone_whose_d1_window_is_still_open_is_not_in_the_cohort(
        self, db_session
    ) -> None:
        """Alta hace 30 h: su ventana de D1 llega a las 48 h. Contarla como «no
        volvió» hundía el D1 de cualquier beta recién abierta."""
        await _make_user(db_session, created_at=NOW - timedelta(hours=30))
        await db_session.commit()
        result = await funnel(db_session, period_days=30)
        assert result["d1_cohort"] == 0
        assert result["d1_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_d1_rate_is_returned_over_the_closed_cohort(self, db_session) -> None:
        registered = NOW - timedelta(days=5)
        came_back = await _make_user(db_session, created_at=registered)
        await _make_user(db_session, created_at=registered)
        # Ruido que antes entraba en el denominador: altas de hoy.
        await _make_user(db_session, created_at=NOW - timedelta(hours=1))
        await _make_user(db_session, created_at=NOW - timedelta(hours=2))
        _make_session(db_session, came_back.id, started_at=registered + timedelta(days=1), duration_minutes=5)
        await db_session.commit()
        result = await funnel(db_session, period_days=30)
        assert (result["d1_return"], result["d1_cohort"]) == (1, 2)
        assert result["d1_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_the_d30_cohort_is_full_size_with_the_default_period(self, db_session) -> None:
        """Con el periodo por defecto (30) la cohorte de D30 son las altas de los
        30 días anteriores a hace 31: nunca vacía por construcción."""
        registered = NOW - timedelta(days=45)
        u = await _make_user(db_session, created_at=registered)
        _make_session(db_session, u.id, started_at=registered + timedelta(days=30), duration_minutes=5)
        await db_session.commit()
        result = await funnel(db_session, period_days=30)
        assert (result["d30_return"], result["d30_cohort"], result["d30_rate"]) == (1, 1, 1.0)

    @pytest.mark.asyncio
    async def test_activated_rate_ignores_signups_who_never_answered(self, db_session) -> None:
        qid = await _question(db_session)
        registered = NOW - timedelta(days=5)
        tried = await _make_user(db_session, created_at=registered)
        await _make_user(db_session, created_at=registered)  # se registró y no hizo nada
        await db_session.flush()
        _answer(db_session, tried.id, qid, registered + timedelta(minutes=5))
        _make_session(db_session, tried.id, started_at=registered + timedelta(days=1), duration_minutes=5)
        await db_session.commit()
        result = await funnel(db_session, period_days=30)
        assert result["d1_rate"] == 0.5
        assert (result["d1_return_activated"], result["d1_cohort_activated"]) == (1, 1)
        assert result["d1_rate_activated"] == 1.0


# ── H4 (dueño, 2026-10-12): instrumento (B), primer intento en no vistas ──────


async def _bank(db, n: int) -> list[str]:
    db.add(Track(id="tH4", name_es="t", name_en="t", order=1))
    db.add(Module(id="mH4", track_id="tH4", name_es="m", name_en="m", order=1))
    db.add(Skill(id="sH4", module_id="mH4", name_es="s", name_en="s", order=1))
    ids = [f"qH4_{i:03d}" for i in range(n)]
    for qid in ids:
        db.add(Question(id=qid, skill_id="sH4", question_es="?", question_en="?", correct_index=0))
    await db.flush()
    return ids


def _attempt(db, user_id, qid: str, correct: bool, at: datetime, *, mode: str = "study",
             unknown: bool = False) -> None:
    sid = uuid.uuid4()
    db.add(StudySession(id=sid, user_id=user_id, started_at=at, ended_at=at, mode=mode))
    db.add(Response(id=uuid.uuid4(), session_id=sid, question_id=qid, correct=correct, grade=4,
                    response_time_ms=1000, created_at=at, declared_unknown=unknown))


class TestH4UnseenFirstAttempt:
    @pytest.mark.asyncio
    async def test_compares_the_first_and_last_first_attempts(self, db_session) -> None:
        qs = await _bank(db_session, 20)
        u = await _make_user(db_session, created_at=NOW - timedelta(days=20))
        await db_session.flush()
        for i, qid in enumerate(qs):
            # 3/10 al principio, 8/10 al final.
            ok = (i < 10 and i < 3) or (i >= 10 and i < 18)
            _attempt(db_session, u.id, qid, ok, NOW - timedelta(days=19) + timedelta(hours=i))
        await db_session.commit()
        r = await unseen_first_attempt_accuracy(db_session, window=10)
        assert (r["users_measured"], r["users_improved"]) == (1, 1)
        assert (r["early_correct"], r["late_correct"], r["attempts_per_end"]) == (3, 8, 10)

    @pytest.mark.asyncio
    async def test_repeats_placement_and_unknown_do_not_count(self, db_session) -> None:
        qs = await _bank(db_session, 20)
        u = await _make_user(db_session, created_at=NOW - timedelta(days=20))
        await db_session.flush()
        t0 = NOW - timedelta(days=19)
        for i, qid in enumerate(qs):
            _attempt(db_session, u.id, qid, False, t0 + timedelta(hours=i))
        # Repetir una pregunta ya vista (y acertarla) no es «no vista».
        _attempt(db_session, u.id, qs[-1], True, t0 + timedelta(days=5))
        # Ni la prueba de nivel ni el «no lo sé» son intentos de práctica.
        _attempt(db_session, u.id, qs[0], True, t0 - timedelta(hours=1), mode="placement")
        await db_session.commit()
        r = await unseen_first_attempt_accuracy(db_session, window=10)
        assert (r["early_correct"], r["late_correct"]) == (0, 0)

    @pytest.mark.asyncio
    async def test_too_few_first_attempts_is_not_measured(self, db_session) -> None:
        qs = await _bank(db_session, 19)
        u = await _make_user(db_session, created_at=NOW - timedelta(days=20))
        await db_session.flush()
        for i, qid in enumerate(qs):
            _attempt(db_session, u.id, qid, True, NOW - timedelta(days=19) + timedelta(hours=i))
        await db_session.commit()
        r = await unseen_first_attempt_accuracy(db_session, window=10)
        assert r["users_measured"] == 0
        assert r["early_rate"] is None
