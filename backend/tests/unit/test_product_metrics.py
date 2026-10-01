"""Unit tests for the 37.20 (ADR-53 §8) product metrics in analytics.py.

Each metric gets a fixture with dates planted by hand — the funnel's D1/D7
pattern this file extends has no unit test of its own pinning its exact
arithmetic (only an integration shape-check), so D30 gets one here too,
not just the new metrics.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import get_password_hash
from app.models.analytics import AnalyticsEvent
from app.models.session import StudySession
from app.models.user import User
from app.services.analytics import (
    conversion_d35,
    curr,
    funnel,
    weekly_30min_rate_among_payers,
)

NOW = datetime.now(UTC)


def _make_user(db, *, created_at: datetime, is_premium: bool = False) -> User:
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
        u = _make_user(db_session, created_at=registered)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=registered + timedelta(days=30), duration_minutes=5)
        await db_session.commit()

        result = await funnel(db_session, period_days=90)
        assert result["d30_return"] == 1
        assert result["d30_rate"] == 1.0 / result["registrations"]

    @pytest.mark.asyncio
    async def test_does_not_count_a_user_who_never_returned(self, db_session) -> None:
        registered = NOW - timedelta(days=40)
        u = _make_user(db_session, created_at=registered)
        db_session.add(u)
        # Only a day-1 session, nothing near day 30.
        _make_session(db_session, u.id, started_at=registered + timedelta(days=1), duration_minutes=5)
        await db_session.commit()

        result = await funnel(db_session, period_days=90)
        assert result["d30_return"] == 0

    @pytest.mark.asyncio
    async def test_ineligible_user_not_counted_either_way(self, db_session) -> None:
        # Registered 10 days ago: too recent to have reached day 30 at all.
        u = _make_user(db_session, created_at=NOW - timedelta(days=10))
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
        u = _make_user(db_session, created_at=NOW - timedelta(days=60))
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
        u = _make_user(db_session, created_at=NOW - timedelta(days=60))
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
        u = _make_user(db_session, created_at=NOW - timedelta(days=60))
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
        u = _make_user(db_session, created_at=NOW - timedelta(days=60))
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

        u = _make_user(db_session, created_at=frozen_now - timedelta(days=60))
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
        u = _make_user(db_session, created_at=registered)
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
        u = _make_user(db_session, created_at=registered)
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
        u = _make_user(db_session, created_at=NOW - timedelta(days=40))
        db_session.add(u)
        await db_session.commit()

        result = await conversion_d35(db_session, period_days=90)
        assert result["sample_too_small"] is True


# ── weekly_30min_rate_among_payers ───────────────────────────────────────────


class TestWeekly30MinAmongPayers:
    @pytest.mark.asyncio
    async def test_payer_with_30_min_this_week_counts(self, db_session) -> None:
        u = _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=30)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["payers"] == 1
        assert result["at_or_above_30min"] == 1
        assert result["rate"] == 1.0

    @pytest.mark.asyncio
    async def test_payer_under_30_min_does_not_count(self, db_session) -> None:
        u = _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=10)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 0
        assert result["rate"] == 0.0

    @pytest.mark.asyncio
    async def test_minutes_across_two_sessions_sum(self, db_session) -> None:
        u = _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=15)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=2), duration_minutes=15)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 1

    @pytest.mark.asyncio
    async def test_free_user_never_counted_even_with_lots_of_time(self, db_session) -> None:
        u = _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=False)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=1), duration_minutes=120)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["payers"] == 0
        assert result["rate"] is None

    @pytest.mark.asyncio
    async def test_session_outside_the_week_does_not_count(self, db_session) -> None:
        u = _make_user(db_session, created_at=NOW - timedelta(days=60), is_premium=True)
        db_session.add(u)
        _make_session(db_session, u.id, started_at=NOW - timedelta(days=10), duration_minutes=60)
        await db_session.commit()

        result = await weekly_30min_rate_among_payers(db_session)
        assert result["at_or_above_30min"] == 0
