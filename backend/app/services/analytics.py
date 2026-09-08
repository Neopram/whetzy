"""Analytics service (5.4).

Provides fire-and-forget event tracking and funnel query helpers.

Events are inserted in the same DB transaction as the action that fired them
(i.e. db.add + caller's db.commit).  We intentionally keep it simple:
no queue, no async worker, no external service.  For high traffic, swap
the body of `track()` to emit to a queue while keeping the same API.

Funnel query (D0→D1→D7) uses the existing users + study_sessions tables
directly — no need to fire separate D-day events since the data is there.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent
from app.models.session import StudySession
from app.models.user import User


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
