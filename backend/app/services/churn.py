"""Churn-risk scorer (task 4.5).

Uses a calibrated logistic formula over four behavioural features extracted
from the live DB.  No training data required — the feature weights encode
domain knowledge about what predicts disengagement in a study app.

Formula (log-odds):
    raw = 0.50 * log1p(days_inactive)
        - 0.15 * current_streak
        - 0.40 * sessions_last_7d
        + 0.30 * (1 - accuracy_overall)
        - 1.50                          # bias (shifts mid-point to ~30-day inactive)
    risk_score = sigmoid(raw)           # 0 = low risk, 1 = high risk

Feature definitions:
    days_inactive      — calendar days since last_active (very large if never active)
    current_streak     — consecutive study days (from user row)
    sessions_last_7d   — count of study sessions started in the last 7 days
    accuracy_overall   — correct / total answers across all sessions (0 if no data)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import StudySession
from app.models.user import User


@dataclass(frozen=True)
class ChurnRiskResult:
    score: float                  # 0.0 – 1.0 (higher = more at risk)
    factors: list[str]            # top contributing risk signals (human-readable, ES)
    days_inactive: int
    current_streak: int
    sessions_last_7d: int
    accuracy_overall: float


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


async def _fetch_session_stats(
    db: AsyncSession, user_id: object, since: datetime
) -> tuple[int, int, int]:
    """Return (session_count_7d, total_questions, total_correct) since `since`."""
    row = await db.execute(
        select(
            func.count(StudySession.id),
            func.coalesce(func.sum(StudySession.questions_answered), 0),
            func.coalesce(func.sum(StudySession.correct_count), 0),
        ).where(
            StudySession.user_id == user_id,
            StudySession.started_at >= since,
        )
    )
    cnt, qs, corr = row.one()
    return int(cnt), int(qs), int(corr)


async def compute_risk(db: AsyncSession, user: User) -> ChurnRiskResult:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    # days_inactive
    if user.last_active is None:
        # Never studied — treat as inactive since account creation
        days_inactive = (now - user.created_at).days
    else:
        days_inactive = max(0, (now - user.last_active).days)

    # sessions in last 7 days + overall accuracy
    sessions_7d, total_qs, total_corr = await _fetch_session_stats(db, user.id, week_ago)
    accuracy = (total_corr / total_qs) if total_qs > 0 else 0.0

    streak = user.current_streak

    raw = (
        0.50 * math.log1p(days_inactive)
        - 0.15 * streak
        - 0.40 * sessions_7d
        + 0.30 * (1.0 - accuracy)
        - 1.50
    )
    score = _sigmoid(raw)

    # Build top-3 factor labels ordered by contribution (most impactful first)
    all_factors: list[tuple[float, str]] = [
        (0.50 * math.log1p(days_inactive), f"Sin actividad: {days_inactive} día(s)"),
        (0.15 * max(0.0, 7.0 - float(streak)), "Racha perdida" if streak == 0 else f"Racha corta ({streak} días)"),
        (0.40 * max(0.0, 3.0 - float(sessions_7d)), "Sin sesiones esta semana" if sessions_7d == 0 else f"Pocas sesiones ({sessions_7d}/semana)"),
    ]
    if accuracy < 0.5:
        all_factors.append((0.30 * (0.5 - accuracy), f"Precisión baja ({accuracy:.0%})"))
    factors = [label for _, label in sorted(all_factors, key=lambda t: t[0], reverse=True)][:3]

    return ChurnRiskResult(
        score=round(score, 4),
        factors=factors,
        days_inactive=days_inactive,
        current_streak=streak,
        sessions_last_7d=sessions_7d,
        accuracy_overall=round(accuracy, 4),
    )
