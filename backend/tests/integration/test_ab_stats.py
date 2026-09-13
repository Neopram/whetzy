"""Integration tests for GET /ml/ab-stats (task 4.6)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.session import StudySession

ML = "/api/v1/ml"


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ab_stats_requires_auth(client) -> None:
    resp = await client.get(f"{ML}/ab-stats")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ab_stats_returns_both_cohorts(client, auth_headers) -> None:
    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "bkt" in data
    assert "dkt" in data


@pytest.mark.asyncio
async def test_ab_stats_shape(client, auth_headers) -> None:
    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
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
async def test_ab_stats_accuracy_none_when_no_questions(client, auth_headers) -> None:
    # Fresh DB: no ended sessions → accuracy must be None for both cohorts
    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    total_questions = data["bkt"]["questions_answered"] + data["dkt"]["questions_answered"]
    if total_questions == 0:
        assert data["bkt"]["accuracy"] is None
        assert data["dkt"]["accuracy"] is None


@pytest.mark.asyncio
async def test_ab_stats_counts_one_registered_user(
    client, auth_headers, user
) -> None:
    # The `user` fixture already created one user; totals["bkt"]["users"] +
    # totals["dkt"]["users"] must equal 1 (only that user in this test DB).
    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    total_users = data["bkt"]["users"] + data["dkt"]["users"]
    assert total_users == 1


@pytest.mark.asyncio
async def test_ab_stats_counts_ended_sessions(
    client, auth_headers, user, db_session
) -> None:
    # Add one ended session for the test user
    sess = StudySession(
        user_id=user.id,
        mode="study",
        questions_answered=10,
        correct_count=7,
        ended_at=datetime.now(UTC),
    )
    db_session.add(sess)
    await db_session.commit()

    resp = await client.get(f"{ML}/ab-stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    total_sessions = data["bkt"]["sessions"] + data["dkt"]["sessions"]
    assert total_sessions == 1
    total_questions = data["bkt"]["questions_answered"] + data["dkt"]["questions_answered"]
    assert total_questions == 10
