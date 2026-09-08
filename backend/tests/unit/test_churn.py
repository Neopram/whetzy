"""Unit tests for the churn-risk scorer (4.5).

Verifies:
1. Score increases with days_inactive and decreases with streak/sessions.
2. AUC > 0.7 on 100 synthetic labelled users.
3. Factors list is non-empty and relevant.
"""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.churn import ChurnRiskResult, _sigmoid, compute_risk


# ── unit: sigmoid ────────────────────────────────────────────────────────────


def test_sigmoid_zero():
    assert abs(_sigmoid(0.0) - 0.5) < 1e-9


def test_sigmoid_large_positive():
    assert _sigmoid(100.0) > 0.999


def test_sigmoid_large_negative():
    assert _sigmoid(-100.0) < 0.001


# ── unit: compute_risk via mocks ─────────────────────────────────────────────


def _mock_user(
    *,
    days_inactive: int = 0,
    current_streak: int = 7,
    days_since_created: int = 30,
) -> MagicMock:
    now = datetime.now(UTC)
    user = MagicMock()
    user.id = "user-001"
    user.current_streak = current_streak
    user.last_active = now - timedelta(days=days_inactive) if days_inactive >= 0 else None
    user.created_at = now - timedelta(days=days_since_created)
    return user


async def _run(
    user: MagicMock,
    sessions_7d: int = 3,
    total_qs: int = 60,
    total_corr: int = 45,
) -> ChurnRiskResult:
    """Run compute_risk with mocked DB session."""
    db = AsyncMock()
    # mock db.execute to return session stats
    mock_result = MagicMock()
    mock_result.one.return_value = (sessions_7d, total_qs, total_corr)
    db.execute = AsyncMock(return_value=mock_result)
    return await compute_risk(db, user)


@pytest.mark.asyncio
async def test_active_user_low_risk():
    user = _mock_user(days_inactive=0, current_streak=30)
    result = await _run(user, sessions_7d=5, total_qs=100, total_corr=80)
    assert result.score < 0.3, f"Expected low risk, got {result.score}"


@pytest.mark.asyncio
async def test_inactive_user_high_risk():
    user = _mock_user(days_inactive=21, current_streak=0)
    result = await _run(user, sessions_7d=0, total_qs=0, total_corr=0)
    assert result.score > 0.55, f"Expected high risk, got {result.score}"


@pytest.mark.asyncio
async def test_streak_reduces_risk():
    user_no_streak = _mock_user(days_inactive=5, current_streak=0)
    user_long_streak = _mock_user(days_inactive=5, current_streak=30)
    r_no = await _run(user_no_streak, sessions_7d=1, total_qs=20, total_corr=15)
    r_streak = await _run(user_long_streak, sessions_7d=1, total_qs=20, total_corr=15)
    assert r_streak.score < r_no.score


@pytest.mark.asyncio
async def test_sessions_reduce_risk():
    user = _mock_user(days_inactive=3, current_streak=0)
    r_low = await _run(user, sessions_7d=0, total_qs=0, total_corr=0)
    r_high = await _run(user, sessions_7d=7, total_qs=100, total_corr=80)
    assert r_high.score < r_low.score


@pytest.mark.asyncio
async def test_result_fields():
    user = _mock_user(days_inactive=7, current_streak=3)
    result = await _run(user, sessions_7d=2, total_qs=40, total_corr=30)
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.factors, list)
    assert len(result.factors) >= 1
    assert result.days_inactive == 7
    assert result.current_streak == 3
    assert result.sessions_last_7d == 2
    assert abs(result.accuracy_overall - 0.75) < 0.01


@pytest.mark.asyncio
async def test_never_active_user_uses_created_at():
    now = datetime.now(UTC)
    user = MagicMock()
    user.id = "u-never"
    user.current_streak = 0
    user.last_active = None
    user.created_at = now - timedelta(days=14)

    result = await _run(user, sessions_7d=0, total_qs=0, total_corr=0)
    assert result.days_inactive == 14
    assert result.score > 0.5


# ── AUC test ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auc_over_synthetic_population():
    """Scorer must achieve AUC > 0.7 on 100 synthetic users.

    Ground truth: churned = days_inactive > 7 (a common industry threshold).
    """
    rng = random.Random(42)
    labels: list[int] = []
    scores: list[float] = []

    for _ in range(100):
        # Churned users: inactive 8–30 days, low streak, few sessions
        churned = rng.random() < 0.5
        if churned:
            days_inactive = rng.randint(8, 30)
            streak = rng.randint(0, 3)
            sessions_7d = rng.randint(0, 1)
            qs = rng.randint(0, 20)
            corr = int(qs * rng.random())
        else:
            days_inactive = rng.randint(0, 5)
            streak = rng.randint(5, 30)
            sessions_7d = rng.randint(3, 7)
            qs = rng.randint(30, 100)
            corr = int(qs * (0.5 + 0.5 * rng.random()))

        user = _mock_user(days_inactive=days_inactive, current_streak=streak)
        result = await _run(user, sessions_7d=sessions_7d, total_qs=qs, total_corr=corr)
        labels.append(1 if churned else 0)
        scores.append(result.score)

    # Compute AUC (trapezoidal rule via sort trick — no sklearn needed)
    pairs = sorted(zip(scores, labels), reverse=True)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        pytest.skip("Degenerate split — adjust seed")
    tp = fp = 0
    auc = 0.0
    prev_fp = 0
    for _, lbl in pairs:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
            auc += tp  # area under ROC = #(pos ranked above neg)
    auc /= n_pos * n_neg

    assert auc > 0.70, f"AUC {auc:.3f} below 0.70 threshold"
