"""Integration tests for /api/v1/placement endpoints.

C2: completing a placement upserts UserSkillState rows (p_known seeded, capped < 0.95).

Endpoints under test:
  POST /api/v1/placement/start            — PlacementStartResponse
  POST /api/v1/placement/answer           — PlacementAnswerResponse
  GET  /api/v1/placement/result           — PlacementResultResponse  (query: session_id)

The placement engine requires at least one question in the track's item pool.
`content_seed` provides exactly one question (q010101001 in track01), so:
  - /start succeeds and returns the single question
  - /answer marks the pool exhausted → finished=True
  - /result is only valid once at least one answer is recorded
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.user import UserSkillState

BASE = "/api/v1/placement"


# ── /start ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_ok(client, user, auth_headers, content_seed):
    resp = await client.post(
        f"{BASE}/start",
        json={"track_id": content_seed["track_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["track_id"] == content_seed["track_id"]
    assert data["questions_answered"] == 0
    # One question in pool → first question should be provided
    assert data["question"] is not None
    q = data["question"]
    assert q["id"] == content_seed["question_id"]
    assert "type" in q
    assert "difficulty_tier" in q
    # correct_index must NOT be present in QuestionPublic (client-facing payload)
    assert "correct_index" not in q


@pytest.mark.asyncio
async def test_start_401(client, content_seed):
    resp = await client.post(
        f"{BASE}/start",
        json={"track_id": content_seed["track_id"]},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_start_unknown_track_404(client, user, auth_headers):
    resp = await client.post(
        f"{BASE}/start",
        json={"track_id": "no-such-track"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_missing_track_id_422(client, user, auth_headers):
    """track_id is required — sending an empty body yields 422."""
    resp = await client.post(f"{BASE}/start", json={}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_start_no_items_in_track(client, user, auth_headers, db_session):
    """A track with no questions raises 422 (no placement items configured)."""
    from app.models.content import Track

    empty_track = Track(
        id="track_empty",
        name_es="Vacío",
        name_en="Empty",
        order=99,
        icon="📭",
        color="#AAAAAA",
        total_questions=0,
    )
    db_session.add(empty_track)
    await db_session.commit()

    resp = await client.post(
        f"{BASE}/start",
        json={"track_id": "track_empty"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── /answer ────────────────────────────────────────────────────────────────────


async def _start_session(client, auth_headers, track_id: str) -> dict:
    """Helper: start placement and return the response dict."""
    resp = await client.post(
        f"{BASE}/start",
        json={"track_id": track_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def test_answer_ok(client, user, auth_headers, content_seed):
    """Answering the only question in the pool: engine exhausts items → finished=True."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    session_id = start["session_id"]
    question_id = start["question"]["id"]

    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1500,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["correct"], bool)
    assert "ability_estimate" in data
    assert "ability_se" in data
    assert data["questions_answered"] == 1
    # Pool exhausted after first answer → finished
    assert data["finished"] is True
    assert data["next_question"] is None


@pytest.mark.asyncio
async def test_answer_correct_flag(client, user, auth_headers, content_seed):
    """correct_index=0 in conftest seed; selecting index 0 should mark correct=True."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 0,   # correct_index is 0
            "response_time_ms": 2000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True


@pytest.mark.asyncio
async def test_answer_wrong_selection(client, user, auth_headers, content_seed):
    """Wrong index → correct=False."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 2,   # incorrect
            "response_time_ms": 3000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is False


@pytest.mark.asyncio
async def test_answer_401(client, content_seed):
    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": str(uuid.uuid4()),
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_answer_invalid_session_404(client, user, auth_headers, content_seed):
    """Non-existent session_id → 404."""
    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": str(uuid.uuid4()),
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_answer_missing_fields_422(client, user, auth_headers):
    """Empty body → 422 (session_id, question_id, response_time_ms all required)."""
    resp = await client.post(f"{BASE}/answer", json={}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_answer_negative_time_422(client, user, auth_headers, content_seed):
    """response_time_ms has ge=0 constraint — negative value → 422."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    resp = await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 0,
            "response_time_ms": -1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── /result ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_result_no_answers_400(client, user, auth_headers, content_seed):
    """Session started but no answer recorded → 400 (no track derivable)."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    session_id = start["session_id"]

    resp = await client.get(
        f"{BASE}/result",
        params={"session_id": session_id},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_result_ok_after_answer(client, user, auth_headers, content_seed):
    """After answering, /result returns a full PlacementResultResponse."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    session_id = start["session_id"]
    question_id = start["question"]["id"]

    await client.post(
        f"{BASE}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=auth_headers,
    )

    resp = await client.get(
        f"{BASE}/result",
        params={"session_id": session_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["track_id"] == content_seed["track_id"]
    assert "ability_estimate" in data
    assert "ability_se" in data
    assert data["total_questions"] == 1
    assert data["correct"] in (0, 1)
    assert "accuracy" in data
    assert "reliability" in data
    assert isinstance(data["skill_mastery"], dict)
    assert isinstance(data["module_recommendations"], list)


@pytest.mark.asyncio
async def test_result_401(client, content_seed):
    resp = await client.get(
        f"{BASE}/result",
        params={"session_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_result_invalid_session_404(client, user, auth_headers):
    """Non-existent session_id → 404."""
    resp = await client.get(
        f"{BASE}/result",
        params={"session_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── C2: placement seeds UserSkillState ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_placement_seeds_user_skill_state_on_finish(
    client, user, auth_headers, db_session, content_seed
):
    """C2: finishing a placement upserts UserSkillState for the tested skill.

    The seed has one question for skill sk010101.  Answering correctly (index=0)
    gives accuracy=1.0; p_known must be capped at < 0.95.
    """
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 0,  # correct
            "response_time_ms": 1000,
        },
        headers=auth_headers,
    )

    state = await db_session.scalar(
        select(UserSkillState).where(
            UserSkillState.user_id == user.id,
            UserSkillState.skill_id == content_seed["skill_id"],
        )
    )
    assert state is not None, "UserSkillState row must exist after placement completes"
    assert 0.0 < state.p_known < 0.95, f"p_known={state.p_known} must be in (0, 0.95)"
    assert state.attempts == 1
    assert state.correct_count == 1


@pytest.mark.asyncio
async def test_placement_p_known_capped_on_perfect_score(
    client, user, auth_headers, db_session, content_seed
):
    """C2 invariant: even 100 % accuracy → p_known < 0.95 (skill stays in practice)."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=auth_headers,
    )

    state = await db_session.scalar(
        select(UserSkillState).where(
            UserSkillState.user_id == user.id,
            UserSkillState.skill_id == content_seed["skill_id"],
        )
    )
    assert state is not None
    assert state.p_known < 0.95, "p_known must be capped below 0.95 (C2 invariant)"


@pytest.mark.asyncio
async def test_placement_wrong_answer_seeds_low_p_known(
    client, user, auth_headers, db_session, content_seed
):
    """C2: a wrong answer seeds p_known near 0 (accuracy 0/1 → p_known = 0.0)."""
    start = await _start_session(client, auth_headers, content_seed["track_id"])
    await client.post(
        f"{BASE}/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "selected_index": 2,  # wrong (correct_index=0)
            "response_time_ms": 800,
        },
        headers=auth_headers,
    )

    state = await db_session.scalar(
        select(UserSkillState).where(
            UserSkillState.user_id == user.id,
            UserSkillState.skill_id == content_seed["skill_id"],
        )
    )
    assert state is not None
    assert state.p_known == 0.0
    assert state.attempts == 1
    assert state.correct_count == 0
