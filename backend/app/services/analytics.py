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
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent
from app.models.session import StudySession
from app.models.user import User, UserSkillState


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


async def funnel(db: AsyncSession, period_days: int = 30) -> dict[str, object]:
    """Compute registration→first-quiz→D1→D7 funnel for the last `period_days`."""
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
    d1_count: int = (
        await db.scalar(
            select(func.count()).select_from(
                select(User.id)
                .where(User.created_at.between(d1_eligible_since, now - timedelta(days=1)))
                .where(
                    select(StudySession.id)
                    .where(
                        StudySession.user_id == User.id,
                        StudySession.started_at >= User.created_at + timedelta(hours=12),
                        StudySession.started_at < User.created_at + timedelta(days=2),
                    )
                    .correlate(User)
                    .exists()
                )
                .subquery()
            )
        )
    ) or 0

    # D7 return: users who registered ≥8 days ago and had a session on day 7
    d7_eligible_since = now - timedelta(days=max(period_days, 8))
    d7_count: int = (
        await db.scalar(
            select(func.count()).select_from(
                select(User.id)
                .where(User.created_at.between(d7_eligible_since, now - timedelta(days=7)))
                .where(
                    select(StudySession.id)
                    .where(
                        StudySession.user_id == User.id,
                        StudySession.started_at >= User.created_at + timedelta(days=6, hours=12),
                        StudySession.started_at < User.created_at + timedelta(days=8),
                    )
                    .correlate(User)
                    .exists()
                )
                .subquery()
            )
        )
    ) or 0

    def _rate(num: int, denom: int) -> float:
        return round(num / denom, 4) if denom else 0.0

    return {
        "period_days": period_days,
        "registrations": reg_count,
        "first_quiz": fq_count,
        "d1_return": d1_count,
        "d7_return": d7_count,
        "first_quiz_rate": _rate(fq_count, reg_count),
        "d1_rate": _rate(d1_count, reg_count),
        "d7_rate": _rate(d7_count, reg_count),
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
