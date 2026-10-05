"""Integration tests for GET /ml/ab-stats (task 4.6).

Admin-only since S.2 (2026-10-04): this endpoint discloses aggregate data
about every user's BKT/DKT cohort, performance and session counts, which is
not something a plain learner should be able to read about the whole user
base. `owner` (role="owner") is the fixture `require_admin` accepts, same
pattern as backend/tests/integration/test_admin*.py."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.security import create_access_token
from app.models.session import StudySession

ML = "/api/v1/ml"


def _h(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ab_stats_requires_auth(client) -> None:
    resp = await client.get(f"{ML}/ab-stats")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ab_stats_rejects_a_non_admin_user(client, auth_headers) -> None:
    """A plain authenticated learner must NOT see aggregate stats about
    every user's A/B cohort."""
    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ab_stats_returns_both_cohorts(client, owner) -> None:
    resp = await client.get(f"{ML}/ab-stats", headers=_h(owner))
    assert resp.status_code == 200
    data = resp.json()
    assert "bkt" in data
    assert "dkt" in data


@pytest.mark.asyncio
async def test_ab_stats_shape(client, owner) -> None:
    resp = await client.get(f"{ML}/ab-stats", headers=_h(owner))
    assert resp.status_code == 200
    data = resp.json()
    for cohort in ("bkt", "dkt"):
        entry = data[cohort]
        assert "users" in entry
        assert "sessions" in entry
        assert "questions_answered" in entry
        assert "accuracy" in entry
        assert entry["users"] >= 0
        assert entry["sessions"] >= 0
        assert entry["questions_answered"] >= 0


@pytest.mark.asyncio
async def test_ab_stats_accuracy_none_when_no_questions(client, owner) -> None:
    # Fresh DB: no ended sessions → accuracy must be None for both cohorts
    resp = await client.get(f"{ML}/ab-stats", headers=_h(owner))
    assert resp.status_code == 200
    data = resp.json()
    total_questions = data["bkt"]["questions_answered"] + data["dkt"]["questions_answered"]
    if total_questions == 0:
        assert data["bkt"]["accuracy"] is None
        assert data["dkt"]["accuracy"] is None


@pytest.mark.asyncio
async def test_ab_stats_counts_one_registered_user(
    client, owner, user
) -> None:
    # The `user` fixture already created one non-admin user; `owner` is a
    # second, distinct user, so totals must equal 2.
    resp = await client.get(f"{ML}/ab-stats", headers=_h(owner))
    assert resp.status_code == 200
    data = resp.json()
    total_users = data["bkt"]["users"] + data["dkt"]["users"]
    assert total_users == 2


@pytest.mark.asyncio
async def test_ab_stats_counts_ended_sessions(
    client, owner, user, db_session
) -> None:
    # Add one ended session for the (non-admin) test user
    sess = StudySession(
        user_id=user.id,
        mode="study",
        questions_answered=10,
        correct_count=7,
        ended_at=datetime.now(UTC),
    )
    db_session.add(sess)
    await db_session.commit()

    resp = await client.get(f"{ML}/ab-stats", headers=_h(owner))
    assert resp.status_code == 200
    data = resp.json()
    total_sessions = data["bkt"]["sessions"] + data["dkt"]["sessions"]
    assert total_sessions == 1
    total_questions = data["bkt"]["questions_answered"] + data["dkt"]["questions_answered"]
    assert total_questions == 10
