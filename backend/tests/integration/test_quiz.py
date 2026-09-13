"""Integration tests for quiz endpoints.

Covers: start session, submit answer, end session, unauthenticated access.
Uses content_seed fixture so the DB has a real Track→Module→Skill→Question.

Each test sends a unique X-Forwarded-For header so the in-memory rate limiter
does not spill over between tests.
"""

from __future__ import annotations

import itertools
import uuid

QUIZ = "/api/v1/quiz"

_ip_counter = itertools.count(100)  # offset from auth tests


def _unique_ip() -> str:
    n = next(_ip_counter)
    return f"198.51.100.{n % 255 or 255}"


def _h(auth_headers: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _unique_ip()}
    if auth_headers:
        headers.update(auth_headers)
    return headers


# ── start ─────────────────────────────────────────────────────────────────────


async def test_quiz_start_with_skill_id_returns_question(client, auth_headers, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["question"] is not None
    assert "id" in data["question"]
    assert data["question"]["id"] == content_seed["question_id"]


async def test_quiz_start_force_question_id_serves_that_question(client, auth_headers, db_session):
    """Dev/E2E override (2.1): serves an exact question, bypassing skill
    selection entirely — used to deterministically reach exec-type questions
    in Playwright without depending on which one the adaptive picker draws.
    """
    from app.models.content import Module, Question, Skill, Track

    track = Track(id="track_force01", name_es="T", name_en="T", order=1, icon="x", color="#000", total_questions=1)
    mod = Module(id="m_force01", track_id="track_force01", name_es="M", name_en="M", order=1, description_es="", description_en="")
    skill = Skill(id="sk_force01", module_id="m_force01", name_es="S", name_en="S", order=1)
    question = Question(
        id="q_force_exec01",
        skill_id="sk_force01",
        type="fill_blank_exec",
        difficulty_tier="easy",
        question_es="```\nx = ___\nprint(x + 1)\n```",
        question_en="```\nx = ___\nprint(x + 1)\n```",
        correct_answer_es="2",
        correct_answer_en="2",
        explanation_es="1 + 1 = 2.",
        explanation_en="1 + 1 = 2.",
        source="test",
        elo_rating=1200.0,
    )
    db_session.add_all([track, mod, skill, question])
    await db_session.commit()

    r = await client.post(
        f"{QUIZ}/start",
        json={"force_question_id": "q_force_exec01"},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["question"]["id"] == "q_force_exec01"
    assert data["question"]["type"] == "fill_blank_exec"


async def test_quiz_start_force_question_id_rejected_in_production(client, auth_headers, content_seed, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENVIRONMENT", "production")
    r = await client.post(
        f"{QUIZ}/start",
        json={"force_question_id": content_seed["question_id"]},
        headers=_h(auth_headers),
    )
    assert r.status_code == 403


async def test_quiz_start_force_question_id_404_for_unknown_id(client, auth_headers):
    r = await client.post(
        f"{QUIZ}/start",
        json={"force_question_id": "does-not-exist"},
        headers=_h(auth_headers),
    )
    assert r.status_code == 404


async def test_quiz_start_returns_session_id(client, auth_headers, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"]},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"]
    assert isinstance(data["session_id"], str)


async def test_quiz_start_no_auth_returns_401(client, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"]},
        headers=_h(),
    )
    assert r.status_code == 401


async def test_quiz_start_no_seed_returns_no_question(client, auth_headers):
    """Without any content in DB the question field should be None."""
    r = await client.post(f"{QUIZ}/start", json={}, headers=_h(auth_headers))
    assert r.status_code == 200
    assert r.json()["question"] is None


# ── answer ────────────────────────────────────────────────────────────────────


async def _start_quiz(client, auth_headers: dict, skill_id: str) -> tuple[str, str]:
    """Helper: start a session and return (session_id, question_id)."""
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": skill_id, "mode": "study"},
        headers=_h(auth_headers),
    )
    data = r.json()
    return data["session_id"], data["question"]["id"]


async def test_quiz_answer_correct_returns_true(client, auth_headers, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"])

    # correct_index for the seed question is 0
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True
    assert "explanation_es" in data
    assert "explanation_en" in data


async def test_quiz_answer_wrong_returns_false(client, auth_headers, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"])

    # correct_index is 0; send 1 → wrong
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 1,
            "response_time_ms": 2000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is False


async def test_quiz_answer_no_auth_returns_401(client, auth_headers, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"])

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=_h(),  # no auth
    )
    assert r.status_code == 401


async def test_quiz_answer_invalid_session_returns_404(client, auth_headers, content_seed):
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": str(uuid.uuid4()),
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 404


async def test_quiz_answer_missing_required_fields_returns_422(client, auth_headers):
    # Missing session_id and question_id
    r = await client.post(
        f"{QUIZ}/answer",
        json={"selected_index": 0},
        headers=_h(auth_headers),
    )
    assert r.status_code == 422


# ── end ───────────────────────────────────────────────────────────────────────


async def test_quiz_end_happy_path(client, auth_headers, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"])

    await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )

    r = await client.post(
        f"{QUIZ}/end",
        json={"session_id": session_id},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    data = r.json()
    assert "total_questions" in data
    assert "accuracy" in data
    assert data["total_questions"] >= 1


async def test_quiz_end_no_auth_returns_401(client, auth_headers, content_seed):
    session_id, _ = await _start_quiz(client, auth_headers, content_seed["skill_id"])

    r = await client.post(
        f"{QUIZ}/end",
        json={"session_id": session_id},
        headers=_h(),  # no auth
    )
    assert r.status_code == 401


# ── exec_output server-side validation (2.3) ──────────────────────────────────


async def _start_exec_quiz(client, auth_headers: dict, db_session) -> tuple[str, str]:
    """Seed an exec question and start a session on it."""
    from app.models.content import Module, Question, Skill, Track

    track = Track(id="track_exec23", name_es="T", name_en="T", order=99, icon="x", color="#000", total_questions=1)
    mod = Module(id="m_exec23", track_id="track_exec23", name_es="M", name_en="M", order=1, description_es="", description_en="")
    skill = Skill(id="sk_exec23", module_id="m_exec23", name_es="S", name_en="S", order=1)
    question = Question(
        id="q_exec23",
        skill_id="sk_exec23",
        type="fill_blank_exec",
        difficulty_tier="easy",
        question_es="```\nprint(2 + 2)\n```",
        question_en="```\nprint(2 + 2)\n```",
        correct_answer_es="4",
        correct_answer_en="4",
        explanation_es="2 + 2 = 4.",
        explanation_en="2 + 2 = 4.",
        source="test",
        elo_rating=1200.0,
    )
    db_session.add_all([track, mod, skill, question])
    await db_session.commit()

    r = await client.post(
        f"{QUIZ}/start",
        json={"force_question_id": "q_exec23"},
        headers=_h(auth_headers),
    )
    data = r.json()
    return data["session_id"], data["question"]["id"]


async def test_exec_output_correct_is_graded_correct(client, auth_headers, db_session):
    session_id, question_id = await _start_exec_quiz(client, auth_headers, db_session)

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "exec_output": "4",
            "response_time_ms": 1500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is True


async def test_exec_output_wrong_cannot_be_falsified(client, auth_headers, db_session):
    session_id, question_id = await _start_exec_quiz(client, auth_headers, db_session)

    # Client sends the right selected_index=1 but the wrong exec_output.
    # Server should use exec_output and mark as incorrect.
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 1,
            "exec_output": "99",
            "response_time_ms": 1500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is False


async def test_exec_output_with_whitespace_is_accepted(client, auth_headers, db_session):
    session_id, question_id = await _start_exec_quiz(client, auth_headers, db_session)

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "exec_output": "4\n",  # trailing newline from print()
            "response_time_ms": 800,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is True
