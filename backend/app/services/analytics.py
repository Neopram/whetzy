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
from datetime import UTC, datetime, timedelta
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
    "curr": "medirla desde el dia 1, sin suelo publicado todavia",
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


async def _sessions_by_user(db: AsyncSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, list[datetime]]:
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(StudySession.user_id, StudySession.started_at).where(
                StudySession.user_id.in_(user_ids)
            )
        )
    ).all()
    by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
    for user_id, started_at in rows:
        by_user[user_id].append(_aware(started_at))
    return by_user


def _count_returned_in_window(
    eligible: Sequence[Row[tuple[uuid.UUID, datetime]]],
    sessions_by_user: dict[uuid.UUID, list[datetime]],
    window_start_offset: timedelta,
    window_end_offset: timedelta,
) -> int:
    """Count eligible users with >=1 session inside [created_at+start, created_at+end).

    Done in Python, not SQL: `DateTime_column +/- timedelta` is typed as
    DATETIME (not Interval) by SQLAlchemy's SQLite-dialect compiler, so the
    comparison silently matches nothing under SQLite (confirmed via
    `.compile(compile_kwargs={"literal_binds": True})`, which raises
    `CompileError` trying to literal-render the timedelta). Postgres has no
    such gap, but that only means this was untested, not correct-by-luck —
    fetching raw rows and comparing in Python is dialect-agnostic by
    construction, so the same code path is now actually exercised by tests.
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
    sessions_by_user = await _sessions_by_user(db, all_eligible_ids)

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
    """Of users active at any point in the 7 days ending yesterday (the
    reference week), what fraction were also active today.

    "Today" is used as the return day (not "tomorrow" from the reference
    week literally) because that is the freshest day fully observable right
    now — waiting for tomorrow to compute today's CURR would make the
    metric always a day stale for no reason. No floor is published for this
    one yet (ADR-53 §8): "medirla desde el día 1" is the instruction, not a
    number to compare against.
    """
    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    week_start = today_start - timedelta(days=7)

    # `.distinct()` as a query modifier, never `func.distinct(col)`: wrapping
    # the column in the SQL function loses its Python-side Uuid type, and
    # the driver value comes back as a plain string that a later `.in_()`
    # bind against the same Uuid column then rejects.
    weekly_active_q = (
        select(StudySession.user_id)
        .where(StudySession.started_at >= week_start, StudySession.started_at < today_start)
        .distinct()
    )
    weekly_active_ids = set((await db.scalars(weekly_active_q)).all())

    if not weekly_active_ids:
        return {"weekly_active": 0, "returned_today": 0, "curr": None}

    returned_today_q = (
        select(StudySession.user_id)
        .where(
            StudySession.started_at >= today_start,
            StudySession.user_id.in_(weekly_active_ids),
        )
        .distinct()
    )
    returned_today_ids = set((await db.scalars(returned_today_q)).all())

    return {
        "weekly_active": len(weekly_active_ids),
        "returned_today": len(returned_today_ids),
        "curr": round(len(returned_today_ids) / len(weekly_active_ids), 4),
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
                )
            )
        ).all()
        for user_id, created_at in rows:
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
