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
async def test_curriculum_lesson_seen_reflects_lesson_completions(
    client, user, auth_headers, db_session, content_seed
):
    """32.4: el frontend usa esto para avisar antes de mandar a un quiz que el
    backend va a bloquear igual."""
    resp = await client.get(
        f"{BASE}/curriculum",
        params={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.json()["modules"][0]["skills"][0]["lesson_seen"] is False

    from app.models.lesson_completion import LessonCompletion

    db_session.add(LessonCompletion(user_id=user.id, skill_id=content_seed["skill_id"]))
    await db_session.commit()

    resp = await client.get(
        f"{BASE}/curriculum",
        params={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.json()["modules"][0]["skills"][0]["lesson_seen"] is True


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


# ── /decaying (14.3) ───────────────────────────────────────────────────────────


async def _seed_skill_with_due(db_session, user, *, skill_id: str, due_in_days: float, attempts: int = 3):
    """Give the user a started skill whose FSRS review falls due at an offset."""
    from datetime import UTC, datetime, timedelta

    from app.models.content import Module, Skill, Track
    from app.models.user import UserSkillState

    track_id = f"track_dec_{skill_id}"
    module_id = f"mod_dec_{skill_id}"
    db_session.add_all([
        Track(id=track_id, name_es="T", name_en="T", order=90, icon="x", color="#000", total_questions=0),
        Module(id=module_id, track_id=track_id, name_es="M", name_en="M", order=1,
               description_es="", description_en=""),
        Skill(id=skill_id, module_id=module_id, name_es=f"ES {skill_id}", name_en=f"EN {skill_id}", order=1),
        UserSkillState(
            user_id=user.id,
            skill_id=skill_id,
            p_known=0.8,
            attempts=attempts,
            correct_count=attempts,
            fsrs_due=datetime.now(UTC) + timedelta(days=due_in_days),
        ),
    ])
    await db_session.commit()


@pytest.mark.asyncio
async def test_decaying_requires_auth(client):
    resp = await client.get(f"{BASE}/decaying")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_decaying_is_empty_for_a_fresh_user(client, user, auth_headers):
    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_decaying_lists_skills_due_inside_the_window(client, user, auth_headers, db_session):
    await _seed_skill_with_due(db_session, user, skill_id="sk_soon", due_in_days=2)

    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["skill_id"] == "sk_soon"
    # The real name, in both languages — the card has to be able to say what
    # you are about to lose, not "skill 12".
    assert rows[0]["name_es"] == "ES sk_soon"
    assert rows[0]["name_en"] == "EN sk_soon"
    assert rows[0]["days_until_due"] == 1  # 2 days minus a few micro-seconds


@pytest.mark.asyncio
async def test_decaying_excludes_skills_due_beyond_the_window(client, user, auth_headers, db_session):
    await _seed_skill_with_due(db_session, user, skill_id="sk_far", due_in_days=30)

    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    assert resp.json() == []

    # ...but a wider window finds it, so the exclusion is the window, not a bug.
    wide = await client.get(f"{BASE}/decaying?within_days=60", headers=auth_headers)
    assert [r["skill_id"] for r in wide.json()] == ["sk_far"]


@pytest.mark.asyncio
async def test_decaying_includes_overdue_and_sorts_it_first(client, user, auth_headers, db_session):
    """Hiding what is already overdue would be the dishonest half of the feature."""
    await _seed_skill_with_due(db_session, user, skill_id="sk_late", due_in_days=-3)
    await _seed_skill_with_due(db_session, user, skill_id="sk_next", due_in_days=5)

    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    rows = resp.json()
    assert [r["skill_id"] for r in rows] == ["sk_late", "sk_next"]
    assert rows[0]["days_until_due"] < 0


@pytest.mark.asyncio
async def test_decaying_ignores_skills_never_practised(client, user, auth_headers, db_session):
    """A skill you never started has nothing to decay; listing it would be a
    to-do dressed up as a warning."""
    await _seed_skill_with_due(db_session, user, skill_id="sk_untouched", due_in_days=1, attempts=0)

    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_decaying_respects_the_limit(client, user, auth_headers, db_session):
    for i in range(7):
        await _seed_skill_with_due(db_session, user, skill_id=f"sk_many{i}", due_in_days=i + 1)

    resp = await client.get(f"{BASE}/decaying", headers=auth_headers)
    assert len(resp.json()) == 5  # default cap

    capped = await client.get(f"{BASE}/decaying?limit=2", headers=auth_headers)
    assert len(capped.json()) == 2
