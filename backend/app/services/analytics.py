"""Analytics service (5.4 / 5.5).

Provides fire-and-forget event tracking and dashboard query helpers.

Events are inserted in the same DB transaction as the action that fired them
(i.e. db.add + caller's db.commit).  We intentionally keep it simple:
no queue, no async worker, no external service.  For high traffic, swap
the body of `track()` to emit to a queue while keeping the same API.

Funnel query (D0→D1→D7) uses the existing users + study_sessions tables
directly — no need to fire separate D-day events since the data is there.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent
from app.models.session import StudySession
from app.models.user import User, UserSkillState

# ADR-53 §8: the floor, not the aspiration — ADR-32's 12-month targets
# (D30 > 10%, conversion > 4%, completion > 50%) stay above these. Every
# metric here is meant to ship with its number, never silently.
PRODUCT_METRIC_TARGETS: dict[str, str] = {
    "d1_rate": ">= 0.15",
    "d7_rate": ">= 0.07",
    "d30_rate": ">= 0.04",
    "conversion_d35_rate": ">= 0.021 (meta 0.03)",
    "completion_rate_among_payers": "0.40-0.55",
    "weekly_30min_rate_among_payers": ">= 0.25 (hipotesis)",
    "curr": "medirla desde el dia 1, sin suelo publicado todavia (referencia: Duolingo 84%, Q2 FY2026, misma definicion — ver docstring de curr()); dias UTC completos, nunca el dia en curso",
    "mock_exam_calibration": "publicarla siempre con n, sin suelo (nadie en el mercado publica una auditada)",
}


async def track(
    db: AsyncSession,
    event_type: str,
    user_id: uuid.UUID | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """Append a typed event row to analytics_events.

    Call before `db.commit()` so the event is included in the same transaction.
    """
    db.add(AnalyticsEvent(user_id=user_id, event_type=event_type, properties=properties))


# ---------------------------------------------------------------------------
# Funnel query
# ---------------------------------------------------------------------------


def _day_bucket(ts: datetime, origin: datetime) -> int:
    """Return how many whole days elapsed between `origin` (UTC) and `ts`."""
    return (ts.date() - origin.date()).days


def _aware(ts: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip; Postgres keeps it. Normalize both."""
    return ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)


async def _sessions_by_user(
    db: AsyncSession, user_ids: set[uuid.UUID], *, since: datetime, until: datetime
) -> dict[uuid.UUID, list[datetime]]:
    """Sessions for `user_ids` within `[since, until]`.

    Bounded, not "all history for these users": a user who registered years
    ago and has thousands of sessions would otherwise have every one of them
    fetched just to check a handful of day-N windows. Callers pass the
    already-known earliest eligible `created_at` and `now` — cheap to widen
    a little (this can over-include, just never under-include the windows
    actually checked) rather than recomputing a tight bound per window.
    """
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(StudySession.user_id, StudySession.started_at).where(
                StudySession.user_id.in_(user_ids),
                StudySession.started_at >= since,
                StudySession.started_at <= until,
            )
        )
    ).all()
    by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
    for user_id, started_at in rows:
        by_user[user_id].append(_aware(started_at))
    return by_user


def _count_returned_in_window(
    eligible: Sequence[Row[uuid.UUID, datetime]],
    sessions_by_user: dict[uuid.UUID, list[datetime]],
    window_start_offset: timedelta,
    window_end_offset: timedelta,
) -> int:
    """Count eligible users with >=1 session inside [created_at+start, created_at+end).

    Done in Python, not SQL. This is a test-environment fix, not a production
    one: Postgres (what Whetzy actually runs) supports `timestamp +/- interval`
    natively and correctly — D1/D7 never returned a wrong number in
    production. The bug was that SQLAlchemy's SQLite-dialect compiler types
    `DateTime_column +/- timedelta` as DATETIME instead of Interval, so under
    the SQLite-backed test suite the comparison silently matched nothing
    (confirmed via `.compile(compile_kwargs={"literal_binds": True})`, which
    raises `CompileError` trying to literal-render the timedelta as that
    wrong type). Because D1/D7 had no unit test pinning their exact
    arithmetic — only an integration shape-check that never planted a precise
    boundary date — this silent SQLite failure went undetected until D30's
    tests (this file) tried to and failed. Fetching raw rows and comparing in
    Python is dialect-agnostic by construction, so the same code path is now
    actually exercised, correctly, under both SQLite (tests) and Postgres
    (production).
    """
    count = 0
    for user_id, created_at in eligible:
        created_at = _aware(created_at)
        window_start = created_at + window_start_offset
        window_end = created_at + window_end_offset
        if any(window_start <= s < window_end for s in sessions_by_user.get(user_id, ())):
            count += 1
    return count


async def funnel(db: AsyncSession, period_days: int = 30) -> dict[str, object]:
    """Compute registration→first-quiz→D1→D7→D30 funnel for the last `period_days`."""
    now = datetime.now(UTC)
    since = now - timedelta(days=period_days)

    # Registrations in window
    reg_count: int = (
        await db.scalar(
            select(func.count(User.id)).where(User.created_at >= since)
        )
    ) or 0

    # First-quiz events in window (from analytics_events table)
    fq_count: int = (
        await db.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == "first_quiz_answer",
                AnalyticsEvent.created_at >= since,
            )
        )
    ) or 0

    # D1 return: users who registered ≥2 days ago and had a session on day 1
    d1_eligible_since = now - timedelta(days=max(period_days, 2))
    d1_eligible = (
        await db.execute(
            select(User.id, User.created_at).where(
                User.created_at.between(d1_eligible_since, now - timedelta(days=1))
            )
        )
    ).all()

    # D7 return: users who registered ≥8 days ago and had a session on day 7
    d7_eligible_since = now - timedelta(days=max(period_days, 8))
    d7_eligible = (
        await db.execute(
            select(User.id, User.created_at).where(
                User.created_at.between(d7_eligible_since, now - timedelta(days=7))
            )
        )
    ).all()

    # D30 return (ADR-53 §8 floor: >= 4%): users who registered >= 31 days
    # ago and had a session on day 30. Same +/- half-day window as D1/D7 so
    # a session fired a few hours either side of the exact 30x24h mark still
    # counts as "day 30" rather than falling through the gap between windows.
    d30_eligible_since = now - timedelta(days=max(period_days, 31))
    d30_eligible = (
        await db.execute(
            select(User.id, User.created_at).where(
                User.created_at.between(d30_eligible_since, now - timedelta(days=30))
            )
        )
    ).all()

    all_eligible_ids = {r[0] for r in d1_eligible} | {r[0] for r in d7_eligible} | {r[0] for r in d30_eligible}
    # d30_eligible_since is always the earliest of the three (it looks back
    # at least 31 days, d7 at least 8, d1 at least 2), so it bounds every
    # window's start; `now` bounds every window's end — no session exists
    # after it anyway.
    sessions_by_user = await _sessions_by_user(db, all_eligible_ids, since=d30_eligible_since, until=now)

    d1_count = _count_returned_in_window(d1_eligible, sessions_by_user, timedelta(hours=12), timedelta(days=2))
    d7_count = _count_returned_in_window(
        d7_eligible, sessions_by_user, timedelta(days=6, hours=12), timedelta(days=8)
    )
    d30_count = _count_returned_in_window(
        d30_eligible, sessions_by_user, timedelta(days=29, hours=12), timedelta(days=31)
    )

    def _rate(num: int, denom: int) -> float:
        return round(num / denom, 4) if denom else 0.0

    return {
        "period_days": period_days,
        "registrations": reg_count,
        "first_quiz": fq_count,
        "d1_return": d1_count,
        "d7_return": d7_count,
        "d30_return": d30_count,
        "first_quiz_rate": _rate(fq_count, reg_count),
        "d1_rate": _rate(d1_count, reg_count),
        "d7_rate": _rate(d7_count, reg_count),
        "d30_rate": _rate(d30_count, reg_count),
        "targets": PRODUCT_METRIC_TARGETS,
    }


# ---------------------------------------------------------------------------
# CURR — "vuelven mañana los activos de la semana" (37.20, ADR-53 §8)
# ---------------------------------------------------------------------------


async def curr(db: AsyncSession) -> dict[str, object]:
    """Current User Retention Rate, Duolingo's own definition, quoted verbatim
    from their Q2 FY2026 shareholder letter (SEC 8-K, filed 2026-08-06):
    https://www.sec.gov/Archives/edgar/data/0001562088/000162828026053299/q2fy26duolingo6-30x26share.htm

        "The main metric we use to evaluate the stickiness of our product is
        Current User Retention Rate (CURR), which is the proportion of
        'current user DAUs' who come back the next day. A 'current user DAU'
        is one who was also active another time in the previous seven days."
        — CURR reported there: 84%, an all-time high (+~1pp YoY).

    Reference day D = the day before yesterday, D+1 = yesterday — both full,
    already-elapsed UTC days. Using "today" as D+1 (an earlier version of
    this function did) makes CURR measure a day that has not finished yet:
    queried at 09:00 UTC, almost nobody has "returned today" simply because
    today is 9 hours old, so the number would silently swing with the hour
    it happens to be read at rather than with actual behavior — a real
    day-over-day return that already fully happened (D -> D+1, both
    complete) would read as a false 0 if D+1 were still "today" in progress.
    This function never looks at today's (partial) data; everything it
    counts is measured in complete UTC days.

    A "current user DAU" is a user active ON DAY D *and* active on some
    OTHER day in the 7 days before D — two separate conditions, not just
    "active sometime in the past week": a user who only ever showed up
    once, on day D itself, does not count, and neither does one who was
    active in the trailing week but not on D itself. `curr` is the fraction
    of that cohort also active on D+1. Comparing this number to Duolingo's
    84% is only honest because the cohort definition now matches theirs
    term for term — an earlier version of this function used a looser
    "active anytime in the trailing week, then active today" cohort, which
    is a materially larger and differently-composed group and would not
    have been a fair comparison.
    """
    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    reference_day_start = today_start - timedelta(days=2)  # D
    return_day_start = today_start - timedelta(days=1)  # D+1 = yesterday
    window_start = reference_day_start - timedelta(days=7)

    rows = (
        await db.execute(
            select(StudySession.user_id, StudySession.started_at).where(
                StudySession.started_at >= window_start,
                StudySession.started_at < today_start,
            )
        )
    ).all()

    active_days_by_user: dict[uuid.UUID, set[date]] = defaultdict(set)
    for user_id, started_at in rows:
        active_days_by_user[user_id].add(_aware(started_at).date())

    reference_date = reference_day_start.date()
    return_date = return_day_start.date()
    prior_week_dates = {(reference_day_start - timedelta(days=d)).date() for d in range(1, 8)}

    current_user_daus = {
        user_id
        for user_id, days in active_days_by_user.items()
        if reference_date in days and (days & prior_week_dates)
    }

    if not current_user_daus:
        return {"current_user_daus": 0, "returned_next_day": 0, "curr": None}

    returned_next_day = {
        user_id
        for user_id in current_user_daus
        if return_date in active_days_by_user.get(user_id, set())
    }

    return {
        "current_user_daus": len(current_user_daus),
        "returned_next_day": len(returned_next_day),
        "curr": round(len(returned_next_day) / len(current_user_daus), 4),
    }


# ---------------------------------------------------------------------------
# Conversion to paid at D35 (37.20, ADR-53 §8)
# ---------------------------------------------------------------------------


async def conversion_d35(db: AsyncSession, period_days: int = 90) -> dict[str, object]:
    """% of users registered >=35 days ago who converted (`subscription_started`
    event, billing.py) within 35 days of registration.

    Deliberately NOT approximated from `User.is_premium`/`subscription_status`:
    those are current state, and a user who converted on day 20 and churned
    by today would be invisible to a snapshot query — undercounting real
    conversions is the same kind of invented-looking number this codebase
    already refuses elsewhere (mock_exam.py's no-predicted-score rule). The
    `subscription_started` event (added alongside this function) is fired
    once, at the real conversion moment, in `billing.py`'s two webhooks — so
    this only ever answers accurately for users who registered after that
    instrumentation shipped. `sample_too_small` says so rather than a rate
    computed on a handful of users looking any more solid than it is.
    """
    now = datetime.now(UTC)
    eligible_since = now - timedelta(days=max(period_days, 35))
    eligible_rows = (
        await db.execute(
            select(User.id, User.created_at).where(
                User.created_at.between(eligible_since, now - timedelta(days=35))
            )
        )
    ).all()
    eligible = len(eligible_rows)

    # Python-side comparison, not `AnalyticsEvent.created_at < User.created_at
    # + timedelta(...)` in SQL — see `_count_returned_in_window`'s docstring
    # for why that silently matches nothing under SQLite.
    events_by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
    if eligible_rows:
        rows = (
            await db.execute(
                select(AnalyticsEvent.user_id, AnalyticsEvent.created_at).where(
                    AnalyticsEvent.event_type == "subscription_started",
                    AnalyticsEvent.user_id.in_([r[0] for r in eligible_rows]),
                    # Bounded, not "every subscription_started this user ever
                    # fired": a conversion can't predate the eligible window
                    # (nobody converts before registering) or postdate `now`.
                    AnalyticsEvent.created_at >= eligible_since,
                    AnalyticsEvent.created_at <= now,
                )
            )
        ).all()
        for user_id, created_at in rows:
            if user_id is not None:  # `in_` ya excluye NULL; mypy no lo sabe
                events_by_user[user_id].append(_aware(created_at))

    converted = 0
    for user_id, created_at in eligible_rows:
        deadline = _aware(created_at) + timedelta(days=35)
        if any(e < deadline for e in events_by_user.get(user_id, ())):
            converted += 1

    return {
        "eligible": eligible,
        "converted": converted,
        "rate": round(converted / eligible, 4) if eligible else None,
        "sample_too_small": eligible < 50,
    }


# ---------------------------------------------------------------------------
# Engagement (5.5)
# ---------------------------------------------------------------------------


async def engagement(db: AsyncSession, period_days: int = 7) -> dict[str, object]:
    """DAU trend, sessions/user, avg session duration for the last `period_days`."""
    now = datetime.now(UTC)
    since = now - timedelta(days=period_days)

    rows = (
        await db.execute(
            select(
                StudySession.user_id,
                StudySession.started_at,
                StudySession.ended_at,
                StudySession.questions_answered,
            ).where(StudySession.started_at >= since)
        )
    ).all()

    dau_map: dict[str, set[str]] = defaultdict(set)
    total_sessions = 0
    user_session_counts: dict[str, int] = defaultdict(int)
    duration_samples: list[float] = []

    for row in rows:
        day_key = row.started_at.date().isoformat()
        uid = str(row.user_id)
        dau_map[day_key].add(uid)
        total_sessions += 1
        user_session_counts[uid] += 1
        if row.ended_at is not None and row.started_at is not None:
            ended = row.ended_at
            started = row.started_at
            if ended.tzinfo is None:
                ended = ended.replace(tzinfo=UTC)
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)
            duration_samples.append((ended - started).total_seconds())

    dau_series: list[dict[str, object]] = []
    for i in range(period_days):
        day = (now - timedelta(days=period_days - 1 - i)).date().isoformat()
        dau_series.append({"date": day, "dau": len(dau_map.get(day, set()))})

    distinct_users = len(user_session_counts)
    avg_sessions = round(total_sessions / distinct_users, 2) if distinct_users else 0.0
    avg_duration = round(sum(duration_samples) / len(duration_samples), 1) if duration_samples else None

    return {
        "period_days": period_days,
        "dau_series": dau_series,
        "avg_sessions_per_user": avg_sessions,
        "avg_session_duration_s": avg_duration,
        "total_sessions": total_sessions,
        "distinct_active_users": distinct_users,
    }


# ---------------------------------------------------------------------------
# Weekly engagement among payers (37.20, ADR-53 §8)
# ---------------------------------------------------------------------------


async def weekly_30min_rate_among_payers(db: AsyncSession) -> dict[str, object]:
    """% of currently-premium users whose summed session duration over the
    trailing 7 days is >= 30 minutes.

    Snapshot of *current* payers, not a cohort — a payer who churned mid-week
    drops out of the denominator entirely rather than counting as a payer
    who fell short, which would double-penalize the same event this metric
    isn't trying to measure (churn has its own metric).
    """
    now = datetime.now(UTC)
    since = now - timedelta(days=7)

    payer_ids: set[uuid.UUID] = set(
        (await db.scalars(select(User.id).where(User.is_premium.is_(True)))).all()
    )
    if not payer_ids:
        return {"payers": 0, "at_or_above_30min": 0, "rate": None}

    rows = (
        await db.execute(
            select(StudySession.user_id, StudySession.started_at, StudySession.ended_at).where(
                StudySession.user_id.in_(payer_ids),
                StudySession.started_at >= since,
            )
        )
    ).all()

    seconds_by_user: dict[uuid.UUID, float] = defaultdict(float)
    for user_id, started_at, ended_at in rows:
        if ended_at is None:
            continue
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=UTC)
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        seconds_by_user[user_id] += (ended_at - started_at).total_seconds()

    at_or_above = sum(1 for secs in seconds_by_user.values() if secs >= 1800)

    return {
        "payers": len(payer_ids),
        "at_or_above_30min": at_or_above,
        "rate": round(at_or_above / len(payer_ids), 4),
    }


# ---------------------------------------------------------------------------
# Skill mastery (5.5)
# ---------------------------------------------------------------------------


async def skill_mastery_stats(db: AsyncSession) -> dict[str, object]:
    """Average BKT p_known per skill across all users, plus top/bottom 5."""
    rows = (
        await db.execute(
            select(
                UserSkillState.skill_id,
                func.avg(UserSkillState.p_known).label("avg_p_known"),
                func.count(UserSkillState.user_id).label("user_count"),
            ).group_by(UserSkillState.skill_id)
        )
    ).all()

    if not rows:
        return {"avg_overall": None, "top_5": [], "bottom_5": [], "total_skills": 0}

    ranked = sorted(rows, key=lambda r: float(r.avg_p_known), reverse=True)

    def _fmt(row: Any) -> dict[str, object]:
        return {
            "skill_id": row.skill_id,
            "avg_p_known": round(float(row.avg_p_known), 4),
            "user_count": int(row.user_count),
        }

    all_avgs = [float(r.avg_p_known) for r in rows]
    overall = round(sum(all_avgs) / len(all_avgs), 4) if all_avgs else None

    return {
        "avg_overall": overall,
        "top_5": [_fmt(r) for r in ranked[:5]],
        "bottom_5": [_fmt(r) for r in ranked[-5:][::-1]],
        "total_skills": len(rows),
    }
