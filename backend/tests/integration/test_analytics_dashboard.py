"""Integration tests for GET /analytics/dashboard (task 5.5).

Covers:
- Admin key gate
- All four dashboard sections present in response (funnel/retention/engagement/skill_mastery)
- Correct shape of each section
- DAU series length matches engagement_days param
- Skill mastery returns empty top/bottom when no UserSkillState rows exist
- Skill mastery aggregates correctly when states are present
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.session import StudySession
from app.models.user import UserSkillState

ANALYTICS = "/api/v1/analytics"
ADMIN_KEY = "test-admin-key-5-5"


def _admin(key: str = ADMIN_KEY) -> dict:
    return {"X-Admin-Key": key}


# ── auth gate ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_requires_admin_key(client) -> None:
    resp = await client.get(f"{ANALYTICS}/dashboard")
    assert resp.status_code == 403


# ── top-level shape ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_returns_four_sections(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(f"{ANALYTICS}/dashboard", headers=_admin())
    assert resp.status_code == 200
    data = resp.json()
    for section in ("funnel", "retention", "engagement", "skill_mastery"):
        assert section in data, f"Missing section: {section}"


@pytest.mark.asyncio
async def test_dashboard_funnel_shape(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(f"{ANALYTICS}/dashboard", headers=_admin())
    assert resp.status_code == 200
    funnel = resp.json()["funnel"]
    for key in ("period_days", "registrations", "first_quiz", "d1_return", "d7_return",
                "first_quiz_rate", "d1_rate", "d7_rate"):
        assert key in funnel, f"Missing funnel key: {key}"


@pytest.mark.asyncio
async def test_dashboard_retention_shape(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(f"{ANALYTICS}/dashboard", headers=_admin())
    assert resp.status_code == 200
    ret = resp.json()["retention"]
    for key in ("d1_rate", "d7_rate", "d1_count", "d7_count"):
        assert key in ret, f"Missing retention key: {key}"
    assert 0.0 <= ret["d1_rate"] <= 1.0
    assert 0.0 <= ret["d7_rate"] <= 1.0


@pytest.mark.asyncio
async def test_dashboard_engagement_shape(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(
        f"{ANALYTICS}/dashboard",
        params={"engagement_days": 7},
        headers=_admin(),
    )
    assert resp.status_code == 200
    eng = resp.json()["engagement"]
    for key in ("period_days", "dau_series", "avg_sessions_per_user",
                "avg_session_duration_s", "total_sessions", "distinct_active_users"):
        assert key in eng, f"Missing engagement key: {key}"
    assert isinstance(eng["dau_series"], list)
    assert eng["period_days"] == 7


@pytest.mark.asyncio
async def test_dashboard_dau_series_length(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(
        f"{ANALYTICS}/dashboard",
        params={"engagement_days": 14},
        headers=_admin(),
    )
    assert resp.status_code == 200
    eng = resp.json()["engagement"]
    assert len(eng["dau_series"]) == 14


@pytest.mark.asyncio
async def test_dashboard_skill_mastery_empty(client, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(f"{ANALYTICS}/dashboard", headers=_admin())
    assert resp.status_code == 200
    mastery = resp.json()["skill_mastery"]
    assert "avg_overall" in mastery
    assert "top_5" in mastery
    assert "bottom_5" in mastery
    assert "total_skills" in mastery
    assert isinstance(mastery["top_5"], list)
    assert isinstance(mastery["bottom_5"], list)


@pytest.mark.asyncio
async def test_dashboard_skill_mastery_with_states(
    client, db_session, user, monkeypatch
) -> None:
    # Seed two UserSkillState rows
    s1 = UserSkillState(user_id=user.id, skill_id="skill_a", p_known=0.8)
    s2 = UserSkillState(user_id=user.id, skill_id="skill_b", p_known=0.2)
    db_session.add_all([s1, s2])
    await db_session.commit()

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(f"{ANALYTICS}/dashboard", headers=_admin())
    assert resp.status_code == 200
    mastery = resp.json()["skill_mastery"]
    assert mastery["total_skills"] == 2
    assert mastery["avg_overall"] is not None
    assert abs(mastery["avg_overall"] - 0.5) < 0.01
    # top skill should be skill_a (p_known=0.8)
    assert mastery["top_5"][0]["skill_id"] == "skill_a"
    assert mastery["top_5"][0]["avg_p_known"] == pytest.approx(0.8, abs=0.01)


@pytest.mark.asyncio
async def test_dashboard_engagement_counts_sessions(
    client, db_session, user, monkeypatch
) -> None:
    # Add one ended session in the last 7 days
    sess = StudySession(
        user_id=user.id,
        mode="study",
        questions_answered=5,
        correct_count=3,
        ended_at=datetime.now(UTC),
    )
    db_session.add(sess)
    await db_session.commit()

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.get(
        f"{ANALYTICS}/dashboard",
        params={"engagement_days": 7},
        headers=_admin(),
    )
    assert resp.status_code == 200
    eng = resp.json()["engagement"]
    assert eng["total_sessions"] >= 1
    assert eng["distinct_active_users"] >= 1
