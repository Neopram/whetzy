"""Integration tests for /api/v1/progress endpoints.

Endpoints under test:
  GET /api/v1/progress/dashboard     — DashboardResponse
  GET /api/v1/progress/skills        — list[SkillMasteryDetail]  (query: track_id, module_id)
  GET /api/v1/progress/curriculum    — CurriculumResponse        (required query: track_id)
  GET /api/v1/progress/predictions   — PredictionResponse        (required query: track_id)
"""

from __future__ import annotations

import pytest


BASE = "/api/v1/progress"


# ── /dashboard ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dashboard_ok(client, user, auth_headers):
    resp = await client.get(f"{BASE}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # DashboardResponse schema
    assert "level" in data
    assert "total_xp" in data
    assert "current_streak" in data
    assert "max_streak" in data
    assert "reviews_due" in data
    assert isinstance(data["tracks"], list)
    assert "total_sessions" in data
    assert "total_questions_answered" in data
    assert "overall_accuracy" in data


@pytest.mark.asyncio
async def test_dashboard_401(client):
    resp = await client.get(f"{BASE}/dashboard")
    assert resp.status_code == 401


# ── /skills ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skills_empty_list(client, user, auth_headers):
    """No skills in DB yet — endpoint returns [] with 200, not an error."""
    resp = await client.get(f"{BASE}/skills", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_skills_returns_list_with_content(client, user, auth_headers, content_seed):
    """After seeding, /skills returns the seeded skill with correct shape."""
    resp = await client.get(f"{BASE}/skills", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["skill_id"] == content_seed["skill_id"]
    assert "p_known" in item
    assert "elo_rating" in item
    assert "attempts" in item
    assert "correct_count" in item
    assert "accuracy" in item
    assert "mastered" in item


@pytest.mark.asyncio
async def test_skills_filter_by_track(client, user, auth_headers, content_seed):
    resp = await client.get(
        f"{BASE}/skills",
        params={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["skill_id"] == content_seed["skill_id"]


@pytest.mark.asyncio
async def test_skills_filter_unknown_track(client, user, auth_headers):
    """Unknown track_id → empty list, not 404."""
    resp = await client.get(
        f"{BASE}/skills",
        params={"track_id": "no-such-track"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_skills_401(client):
    resp = await client.get(f"{BASE}/skills")
    assert resp.status_code == 401


# ── /curriculum ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_curriculum_ok(client, user, auth_headers, content_seed):
    resp = await client.get(
        f"{BASE}/curriculum",
        params={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["track_id"] == content_seed["track_id"]
    assert "modules" in data
    assert isinstance(data["modules"], list)
    assert len(data["modules"]) == 1
    mod = data["modules"][0]
    assert "skills" in mod
    assert len(mod["skills"]) == 1


@pytest.mark.asyncio
async def test_curriculum_unknown_track_returns_empty(client, user, auth_headers):
    """Service returns an empty CurriculumResponse for unknown tracks (no 404)."""
    resp = await client.get(
        f"{BASE}/curriculum",
        params={"track_id": "no-such-track"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["track_id"] == "no-such-track"
    assert data["modules"] == []


@pytest.mark.asyncio
async def test_curriculum_missing_track_id_422(client, user, auth_headers):
    """track_id is a required query param — omitting it yields 422."""
    resp = await client.get(f"{BASE}/curriculum", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_curriculum_401(client, content_seed):
    resp = await client.get(
        f"{BASE}/curriculum",
        params={"track_id": content_seed["track_id"]},
    )
    assert resp.status_code == 401


# ── /predictions ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_predictions_ok(client, user, auth_headers, content_seed):
    resp = await client.get(
        f"{BASE}/predictions",
        params={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["track_id"] == content_seed["track_id"]
    assert "skills_remaining" in data
    assert "avg_xp_per_day" in data
    assert "estimated_xp_needed" in data
    assert "confidence" in data
    # No sessions → low confidence, no days estimate
    assert data["confidence"] == "low"
    assert data["estimated_days_to_completion"] is None


@pytest.mark.asyncio
async def test_predictions_missing_track_id_422(client, user, auth_headers):
    resp = await client.get(f"{BASE}/predictions", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_predictions_401(client, content_seed):
    resp = await client.get(
        f"{BASE}/predictions",
        params={"track_id": content_seed["track_id"]},
    )
    assert resp.status_code == 401
