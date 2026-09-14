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


# ── "I don't know" ────────────────────────────────────────────────────────────


async def _start(client, auth_headers, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    return r.json()["session_id"]


async def test_declared_unknown_is_not_correct(client, auth_headers, content_seed):
    session_id = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": content_seed["question_id"],
            "declared_unknown": True,
            "response_time_ms": 1500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is False


async def test_declared_unknown_ignores_a_sent_index(client, auth_headers, content_seed):
    """Even with the right index attached, an admission is an admission.

    The client should not be able to claim ignorance and credit at once.
    """
    session_id = await _start(client, auth_headers, content_seed)
    first = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    correct_index = first.json()["correct_index"]

    session_id = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": content_seed["question_id"],
            "declared_unknown": True,
            "selected_index": correct_index,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is False


async def test_declared_unknown_lowers_mastery_more_than_a_wrong_answer(
    client, auth_headers, plus_auth_headers, content_seed
):
    """The whole point of the button: honesty must inform the model better.

    Two learners meet the same question. One guesses wrong, the other admits
    ignorance. The admission has to move p_known further down, because it is
    the observation with no guessing and no slip hidden inside it.
    """
    wrong_session = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": wrong_session,
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    correct_index = r.json()["correct_index"]
    wrong_index = 0 if correct_index != 0 else 1

    # Re-run so the first learner is definitely wrong, not accidentally right.
    wrong_session = await _start(client, auth_headers, content_seed)
    r_wrong = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": wrong_session,
            "question_id": content_seed["question_id"],
            "selected_index": wrong_index,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r_wrong.json()["correct"] is False
    mastery_after_wrong = r_wrong.json()["skill_mastery"][content_seed["skill_id"]]

    unknown_session = await _start(client, plus_auth_headers, content_seed)
    r_unknown = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": unknown_session,
            "question_id": content_seed["question_id"],
            "declared_unknown": True,
            "response_time_ms": 1000,
        },
        headers=_h(plus_auth_headers),
    )
    mastery_after_unknown = r_unknown.json()["skill_mastery"][content_seed["skill_id"]]

    assert mastery_after_unknown < mastery_after_wrong


async def test_declared_unknown_leaves_item_difficulty_alone(
    client, auth_headers, content_seed, db_session
):
    """Nobody attempted the question, so it learned nothing about its own difficulty."""
    from sqlalchemy import select

    from app.models.content import Question

    before = (
        await db_session.execute(
            select(Question.elo_rating).where(Question.id == content_seed["question_id"])
        )
    ).scalar_one()

    session_id = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": content_seed["question_id"],
            "declared_unknown": True,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200

    db_session.expire_all()
    after = (
        await db_session.execute(
            select(Question.elo_rating).where(Question.id == content_seed["question_id"])
        )
    ).scalar_one()

    assert after == before


async def test_declared_unknown_is_never_punished_on_xp(client, auth_headers, content_seed):
    """Honesty must never cost more than being wrong, or nobody presses it."""
    wrong_session = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": wrong_session,
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    correct_index = r.json()["correct_index"]
    wrong_index = 0 if correct_index != 0 else 1

    wrong_session = await _start(client, auth_headers, content_seed)
    xp_wrong = (
        await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": wrong_session,
                "question_id": content_seed["question_id"],
                "selected_index": wrong_index,
                "response_time_ms": 1000,
            },
            headers=_h(auth_headers),
        )
    ).json()["xp_earned"]

    unknown_session = await _start(client, auth_headers, content_seed)
    xp_unknown = (
        await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": unknown_session,
                "question_id": content_seed["question_id"],
                "declared_unknown": True,
                "response_time_ms": 1000,
            },
            headers=_h(auth_headers),
        )
    ).json()["xp_earned"]

    assert xp_unknown >= xp_wrong


async def test_declared_unknown_defaults_to_false(client, auth_headers, content_seed):
    """Old clients that never send the field must keep working unchanged."""
    session_id = await _start(client, auth_headers, content_seed)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200


# ── exec grading honours the learner's language (13.8) ────────────────────────


async def test_exec_output_graded_against_the_learners_language(
    client, auth_headers, db_session
):
    """An English learner printing the English message must be graded correct.

    Four questions in the bank ask for a message string that legitimately
    differs per language ("Cannot divide by zero" vs "No se puede dividir
    entre cero"). Grading everyone against the Spanish string marked correct
    English work as wrong — while the client, which compares against the
    learner's own language, told them it was right.
    """
    from sqlalchemy import select

    from app.models.content import Module, Question, Skill, Track
    from app.models.user import User

    track = Track(
        id="track_lang", name_es="T", name_en="T", order=98,
        icon="x", color="#000", total_questions=1,
    )
    mod = Module(
        id="m_lang", track_id="track_lang", name_es="M", name_en="M",
        order=1, description_es="", description_en="",
    )
    skill = Skill(id="sk_lang", module_id="m_lang", name_es="S", name_en="S", order=1)
    question = Question(
        id="q_lang",
        skill_id="sk_lang",
        type="fill_blank_exec",
        difficulty_tier="easy",
        question_es="```\nprint(___)\n```",
        question_en="```\nprint(___)\n```",
        correct_answer_es="No se puede dividir entre cero",
        correct_answer_en="Cannot divide by zero",
        explanation_es="x", explanation_en="x",
        source="test", elo_rating=1200.0,
    )
    db_session.add_all([track, mod, skill, question])
    await db_session.commit()

    async def answer(output: str) -> bool:
        started = await client.post(
            f"{QUIZ}/start",
            json={"force_question_id": "q_lang"},
            headers=_h(auth_headers),
        )
        r = await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": started.json()["session_id"],
                "question_id": "q_lang",
                "exec_output": output,
                "response_time_ms": 1200,
            },
            headers=_h(auth_headers),
        )
        assert r.status_code == 200
        return bool(r.json()["correct"])

    # Default learner is Spanish: the Spanish string is the right one.
    assert await answer("No se puede dividir entre cero") is True
    assert await answer("Cannot divide by zero") is False

    # Switch the learner to English and the expectation follows them.
    me = (await db_session.execute(select(User).limit(1))).scalars().first()
    assert me is not None
    me.language = "en"
    await db_session.commit()

    assert await answer("Cannot divide by zero") is True


async def test_viewing_a_question_in_the_other_language_cannot_change_grading(
    client, auth_headers, content_seed
):
    """The language switch is a reading aid, never an input to the engine.

    Options are stored in the same order in both languages, and the answer
    travels as an index, so reading a question in English and answering it must
    land on exactly the same verdict as reading it in Spanish. This test pins
    that: the API has no language parameter on /answer at all, and if one is
    ever added, this is where it should hurt.
    """
    verdicts = set()
    correct_indices = set()

    for _ in range(2):
        started = await client.post(
            f"{QUIZ}/start",
            json={"skill_id": content_seed["skill_id"], "mode": "study"},
            headers=_h(auth_headers),
        )
        r = await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": started.json()["session_id"],
                "question_id": content_seed["question_id"],
                "selected_index": 0,
                "response_time_ms": 1000,
            },
            headers=_h(auth_headers),
        )
        assert r.status_code == 200
        verdicts.add(r.json()["correct"])
        correct_indices.add(r.json()["correct_index"])

    assert len(verdicts) == 1, "the same index must always get the same verdict"
    assert len(correct_indices) == 1, "the correct index must not depend on presentation"


async def test_skill_state_creation_recovers_from_a_lost_race(user, db_session):
    """The loser of a create race must get the winner's row, not a 500.

    Check-then-insert had no guard: two callers both saw no row, both inserted,
    and the loser hit `uq_user_skill_state` and took the request down. A double
    tap on "Practicar" is enough — React's development double-render produced it
    on the first real click, as an HTTP 500 in the browser.

    True concurrency cannot be staged here: the fixtures hand every request the
    same SQLAlchemy Session, and one Session used from two tasks raises
    "Session is already flushing" before any race can happen. So this drives the
    recovery branch directly — the row exists, the SELECT is made to miss it,
    and the insert therefore collides exactly as the loser's would.
    """
    from sqlalchemy import select

    from app.models.user import UserSkillState
    from app.services.quiz import _get_or_create_skill_state

    skill_id = "sk_race"
    db_session.add(UserSkillState(user_id=user.id, skill_id=skill_id))
    await db_session.flush()

    real_execute = db_session.execute
    calls = {"n": 0}

    async def execute_missing_once(statement, *args, **kwargs):
        # Only the function's own first lookup is blinded; everything after,
        # including its re-read, sees the truth.
        calls["n"] += 1
        if calls["n"] == 1:
            return await real_execute(
                select(UserSkillState).where(UserSkillState.skill_id == "sk_does_not_exist"),
                *args,
                **kwargs,
            )
        return await real_execute(statement, *args, **kwargs)

    db_session.execute = execute_missing_once  # type: ignore[method-assign]
    try:
        state = await _get_or_create_skill_state(db_session, user.id, skill_id)
    finally:
        db_session.execute = real_execute  # type: ignore[method-assign]

    assert state.skill_id == skill_id
    assert state.user_id == user.id
