"""Integration tests for quiz endpoints.

Covers: start session, submit answer, end session, unauthenticated access.
Uses content_seed fixture so the DB has a real Track→Module→Skill→Question.

Each test sends a unique X-Forwarded-For header so the in-memory rate limiter
does not spill over between tests.
"""

from __future__ import annotations

import itertools
import uuid

import pytest

from app.models.lesson_completion import LessonCompletion

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


async def _see_lesson(db_session, user, *skill_ids: str) -> None:
    """32.4: el estudio de un skill exige haber visto su lección primero.

    Idempotente a propósito: varias llamadas para el mismo (user, skill) —
    p. ej. `_start` llamado varias veces en el mismo test — no deben chocar
    con la restricción `unique(user_id, skill_id)`.
    """
    from sqlalchemy import select as _select

    for skill_id in skill_ids:
        existing = (
            await db_session.execute(
                _select(LessonCompletion).where(
                    LessonCompletion.user_id == user.id, LessonCompletion.skill_id == skill_id
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            db_session.add(LessonCompletion(user_id=user.id, skill_id=skill_id))
    await db_session.commit()


# ── start ─────────────────────────────────────────────────────────────────────


async def test_quiz_start_with_skill_id_returns_question(client, auth_headers, user, db_session, content_seed):
    await _see_lesson(db_session, user, content_seed["skill_id"])
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


async def _start_quiz(client, auth_headers: dict, skill_id: str, db_session=None, user=None) -> tuple[str, str]:
    """Helper: start a session and return (session_id, question_id).

    32.4: el estudio de `skill_id` exige haber visto su lección primero.
    """
    if db_session is not None and user is not None:
        await _see_lesson(db_session, user, skill_id)
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": skill_id, "mode": "study"},
        headers=_h(auth_headers),
    )
    data = r.json()
    return data["session_id"], data["question"]["id"]


async def test_quiz_answer_correct_returns_true(client, auth_headers, user, db_session, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

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


async def test_quiz_answer_wrong_returns_false(client, auth_headers, user, db_session, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

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


async def test_quiz_answer_no_auth_returns_401(client, auth_headers, user, db_session, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

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


async def test_quiz_answer_rejects_a_question_never_served_in_this_session(
    client, auth_headers, user, db_session, content_seed
):
    """S.4: antes de esto, cualquier `question_id` que existiera en la base
    se podía mandar a `/quiz/answer`, aunque esta sesión nunca lo hubiera
    servido — sin pasar por la selección, el anti-repetición ni el filtro de
    `pool != "simulacro"`."""
    from app.models.content import Module, Question, Skill, Track

    session_id, _served_question_id = await _start_quiz(
        client, auth_headers, content_seed["skill_id"], db_session, user
    )

    other_track = Track(id="track_other", name_es="T", name_en="T", order=96, icon="x", color="#000", total_questions=1)
    other_mod = Module(id="m_other", track_id="track_other", name_es="M", name_en="M", order=1, description_es="", description_en="")
    other_skill = Skill(id="sk_other", module_id="m_other", name_es="S", name_en="S", order=1)
    other_question = Question(
        id="q_never_served",
        skill_id="sk_other",
        type="mcq",
        difficulty_tier="easy",
        question_es="¿Otra pregunta?",
        question_en="Another question?",
        options_es=["A", "B"],
        options_en=["A", "B"],
        correct_index=0,
        explanation_es="",
        explanation_en="",
        source="test",
        elo_rating=1200.0,
    )
    db_session.add_all([other_track, other_mod, other_skill, other_question])
    await db_session.commit()

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": "q_never_served",
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 409


async def test_quiz_answer_rejects_answering_the_same_question_twice(
    client, auth_headers, user, db_session, content_seed
):
    """S.4: sin esto, el mismo `question_id` se podía mandar una y otra vez
    en la misma sesión — cada envío sumaba XP y maestría de nuevo."""
    session_id, question_id = await _start_quiz(
        client, auth_headers, content_seed["skill_id"], db_session, user
    )

    first = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=_h(auth_headers),
    )
    assert first.status_code == 200

    second = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 500,
        },
        headers=_h(auth_headers),
    )
    assert second.status_code == 409


async def test_quiz_answer_missing_required_fields_returns_422(client, auth_headers):
    # Missing session_id and question_id
    r = await client.post(
        f"{QUIZ}/answer",
        json={"selected_index": 0},
        headers=_h(auth_headers),
    )
    assert r.status_code == 422


# ── end ───────────────────────────────────────────────────────────────────────


async def test_quiz_end_happy_path(client, auth_headers, user, db_session, content_seed):
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

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


async def test_quiz_end_no_auth_returns_401(client, auth_headers, user, db_session, content_seed):
    session_id, _ = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

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


async def test_exec_without_output_is_wrong_even_if_the_client_says_correct(client, auth_headers, db_session):
    """El agujero que había en producción (2026-10-01, q130103_fbe001).

    La web no mandaba exec_output y el servidor creía a `selected_index == 1`:
    cualquiera marcaba un ejecutable como resuelto desde la API. Sin la salida,
    la respuesta cuenta como incorrecta.
    """
    session_id, question_id = await _start_exec_quiz(client, auth_headers, db_session)

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 1,
            "response_time_ms": 1500,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is False


async def _start_fill_blank_quiz(client, auth_headers: dict, db_session) -> tuple[str, str]:
    """`fill_blank`: el alumno escribe la salida y el servidor la compara."""
    from app.models.content import Module, Question, Skill, Track

    track = Track(id="track_fb", name_es="T", name_en="T", order=98, icon="x", color="#000", total_questions=1)
    mod = Module(id="m_fb", track_id="track_fb", name_es="M", name_en="M", order=1, description_es="", description_en="")
    skill = Skill(id="sk_fb", module_id="m_fb", name_es="S", name_en="S", order=1)
    question = Question(
        id="q_fb01",
        skill_id="sk_fb",
        type="fill_blank",
        difficulty_tier="easy",
        question_es="¿Qué imprime este código?\n```python\nprint('True' if 1 else 'False')\n```",
        question_en="What does this code print?\n```python\nprint('True' if 1 else 'False')\n```",
        correct_answer_es="True",
        correct_answer_en="True",
        explanation_es="1 es verdadero.",
        explanation_en="1 is truthy.",
        source="test",
        elo_rating=1200.0,
    )
    db_session.add_all([track, mod, skill, question])
    await db_session.commit()
    r = await client.post(f"{QUIZ}/start", json={"force_question_id": "q_fb01"}, headers=_h(auth_headers))
    data = r.json()
    return data["session_id"], data["question"]["id"]


@pytest.mark.parametrize(
    ("payload", "correct"),
    [
        ({"answer_text": "  true "}, True),  # misma regla que el cliente: recorta y sin mayúsculas
        ({"answer_text": "False"}, False),
        ({"selected_index": 1}, False),  # sin texto no hay nada que corregir
    ],
)
async def test_fill_blank_is_graded_by_the_server_from_the_typed_text(
    client, auth_headers, db_session, payload, correct
):
    session_id, question_id = await _start_fill_blank_quiz(client, auth_headers, db_session)
    r = await client.post(
        f"{QUIZ}/answer",
        json={"session_id": session_id, "question_id": question_id, "response_time_ms": 900, **payload},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200, r.text
    assert r.json()["correct"] is correct


# ── "I don't know" ────────────────────────────────────────────────────────────


async def _start(client, auth_headers, content_seed, db_session, user):
    # S.4: /quiz/answer ya exige que la pregunta sea la que esta sesión acaba
    # de servir — sin haber "visto la lección" (32.4) /quiz/start no serviría
    # ninguna, y el `question_id` fijo de abajo dejaría de coincidir.
    await _see_lesson(db_session, user, content_seed["skill_id"])
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    return r.json()["session_id"]


async def test_declared_unknown_is_not_correct(client, auth_headers, content_seed, db_session, user):
    session_id = await _start(client, auth_headers, content_seed, db_session, user)
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


async def test_declared_unknown_ignores_a_sent_index(client, auth_headers, content_seed, db_session, user):
    """Even with the right index attached, an admission is an admission.

    The client should not be able to claim ignorance and credit at once.
    """
    session_id = await _start(client, auth_headers, content_seed, db_session, user)
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

    session_id = await _start(client, auth_headers, content_seed, db_session, user)
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
    client, auth_headers, plus_auth_headers, content_seed, db_session, user, plus_user
):
    """The whole point of the button: honesty must inform the model better.

    Two learners meet the same question. One guesses wrong, the other admits
    ignorance. The admission has to move p_known further down, because it is
    the observation with no guessing and no slip hidden inside it.
    """
    wrong_session = await _start(client, auth_headers, content_seed, db_session, user)
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
    wrong_session = await _start(client, auth_headers, content_seed, db_session, user)
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

    unknown_session = await _start(client, plus_auth_headers, content_seed, db_session, plus_user)
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
    client, auth_headers, content_seed, db_session, user
):
    """Nobody attempted the question, so it learned nothing about its own difficulty."""
    from sqlalchemy import select

    from app.models.content import Question

    before = (
        await db_session.execute(
            select(Question.elo_rating).where(Question.id == content_seed["question_id"])
        )
    ).scalar_one()

    session_id = await _start(client, auth_headers, content_seed, db_session, user)
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


async def test_declared_unknown_is_never_punished_on_xp(client, auth_headers, content_seed, db_session, user):
    """Honesty must never cost more than being wrong, or nobody presses it."""
    wrong_session = await _start(client, auth_headers, content_seed, db_session, user)
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

    wrong_session = await _start(client, auth_headers, content_seed, db_session, user)
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

    unknown_session = await _start(client, auth_headers, content_seed, db_session, user)
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


async def test_declared_unknown_defaults_to_false(client, auth_headers, content_seed, db_session, user):
    """Old clients that never send the field must keep working unchanged."""
    session_id = await _start(client, auth_headers, content_seed, db_session, user)
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
    client, auth_headers, content_seed, db_session, user
):
    """The language switch is a reading aid, never an input to the engine.

    Options are stored in the same order in both languages, and the answer
    travels as an index, so reading a question in English and answering it must
    land on exactly the same verdict as reading it in Spanish. This test pins
    that: the API has no language parameter on /answer at all, and if one is
    ever added, this is where it should hurt.
    """
    await _see_lesson(db_session, user, content_seed["skill_id"])
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


# ── el alcance de la sesión se mantiene tras la primera pregunta ──────────────


async def _seed_two_tracks(db_session) -> None:
    """Dos tracks con una skill y dos preguntas cada uno, todo desbloqueado."""
    from app.models.content import Module, Question, Skill, Track

    rows = []
    for n in ("a", "b"):
        rows.append(Track(id=f"track_scope_{n}", name_es="T", name_en="T", order=90, icon="x", color="#000", total_questions=2))
        rows.append(Module(id=f"m_scope_{n}", track_id=f"track_scope_{n}", name_es="M", name_en="M", order=1, description_es="", description_en=""))
        rows.append(Skill(id=f"sk_scope_{n}", module_id=f"m_scope_{n}", name_es="S", name_en="S", order=1))
        for i in (1, 2):
            rows.append(Question(
                id=f"q_scope_{n}{i}",
                skill_id=f"sk_scope_{n}",
                type="mcq",
                difficulty_tier="easy",
                question_es=f"P{n}{i}", question_en=f"Q{n}{i}",
                options_es=["a", "b"], options_en=["a", "b"],
                correct_index=0,
                explanation_es="e", explanation_en="e",
                source="test",
                elo_rating=1200.0,
            ))
    db_session.add_all(rows)
    await db_session.commit()


async def test_next_question_stays_inside_the_session_track(client, auth_headers, user, db_session):
    """«Practicar» en un track no puede servir el siguiente ítem de otro.

    Antes la primera pregunta respetaba `track_id` y la segunda salía de
    cualquier track, porque el alcance no se guardaba en la sesión.
    """
    await _seed_two_tracks(db_session)
    await _see_lesson(db_session, user, "sk_scope_a")

    for _ in range(6):
        r = await client.post(
            f"{QUIZ}/start",
            json={"track_id": "track_scope_a", "mode": "study"},
            headers=_h(auth_headers),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["question"]["skill_id"] == "sk_scope_a"

        r = await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": data["session_id"],
                "question_id": data["question"]["id"],
                "selected_index": 0,
                "response_time_ms": 1000,
            },
            headers=_h(auth_headers),
        )
        assert r.status_code == 200, r.text
        nxt = r.json()["next_question"]
        assert nxt is not None
        assert nxt["skill_id"] == "sk_scope_a", nxt


async def test_next_question_stays_on_the_session_skill(client, auth_headers, user, db_session):
    await _seed_two_tracks(db_session)
    await _see_lesson(db_session, user, "sk_scope_b")

    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": "sk_scope_b", "mode": "study"},
        headers=_h(auth_headers),
    )
    data = r.json()
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": data["session_id"],
            "question_id": data["question"]["id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200, r.text
    assert r.json()["next_question"]["skill_id"] == "sk_scope_b"


# ── offline queue idempotency (33.2) ────────────────────────────────────────


async def test_answer_idempotency_same_event_id_returns_cached(client, auth_headers, user, db_session, content_seed):
    """Submitting the same answer twice with the same event_id must be idempotent.

    The second call returns the same verdict without creating a duplicate Response row.
    """
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)
    event_id = str(uuid.uuid4())

    payload = {
        "session_id": session_id,
        "question_id": question_id,
        "selected_index": 0,
        "response_time_ms": 1500,
        "event_id": event_id,
    }

    r1 = await client.post(f"{QUIZ}/answer", json=payload, headers=_h(auth_headers))
    assert r1.status_code == 200
    d1 = r1.json()

    r2 = await client.post(f"{QUIZ}/answer", json=payload, headers=_h(auth_headers))
    assert r2.status_code == 200
    d2 = r2.json()

    assert d1["correct"] == d2["correct"]
    assert d1["grade"] == d2["grade"]
    assert d1["correct_index"] == d2["correct_index"]


async def test_answer_without_event_id_still_works(client, auth_headers, user, db_session, content_seed):
    """Old clients that never send event_id must keep working."""
    session_id, question_id = await _start_quiz(client, auth_headers, content_seed["skill_id"], db_session, user)

    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 200
    assert r.json()["correct"] is True


# ── una sesión no repite preguntas mientras queden otras (paso 1, 2026-10-01) ──


async def test_session_does_not_repeat_a_question_while_others_remain(
    client, auth_headers, user, db_session, monkeypatch
):
    """Un alumno nuevo vio la misma pregunta en la 1.ª y la 3.ª de su primera sesión.

    `_select_question` elige al azar entre las 5 más cercanas a su Elo y solo
    excluía la inmediatamente anterior, así que con una sola skill desbloqueada
    la sesión daba vueltas sobre las mismas cinco. Con `random.choice` fijo al
    primer candidato el viejo comportamiento repite de forma determinista.
    """
    from app.models.content import Module, Question, Skill, Track
    from app.services import quiz as quiz_service

    db_session.add_all([
        Track(id="track_rep", name_es="T", name_en="T", order=91, icon="🧪", color="#000", total_questions=6),
        Module(id="m_rep", track_id="track_rep", name_es="M", name_en="M", order=1, description_es="", description_en=""),
        Skill(id="sk_rep", module_id="m_rep", name_es="S", name_en="S", order=1),
        *[
            Question(
                id=f"q_rep_{i}", skill_id="sk_rep", type="mcq", difficulty_tier="easy",
                question_es=f"P{i}", question_en=f"Q{i}", options_es=["a", "b"], options_en=["a", "b"],
                correct_index=0, explanation_es="e", explanation_en="e", source="test", elo_rating=1200.0,
            )
            for i in range(6)
        ],
    ])
    await db_session.commit()
    await _see_lesson(db_session, user, "sk_rep")
    monkeypatch.setattr(quiz_service.random, "choice", lambda seq: seq[0])

    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_rep", "mode": "study"}, headers=_h(auth_headers))
    assert r.status_code == 200, r.text
    data = r.json()
    served = [data["question"]["id"]]
    for i in range(5):
        r = await client.post(
            f"{QUIZ}/answer",
            json={
                "session_id": data["session_id"],
                "question_id": served[-1],
                "selected_index": i % 2,
                "response_time_ms": 1000,
            },
            headers=_h(auth_headers),
        )
        assert r.status_code == 200, r.text
        served.append(r.json()["next_question"]["id"])

    assert len(set(served)) == len(served), f"repetida dentro de la sesión: {served}"


async def test_session_reuses_questions_only_when_the_skill_runs_out(client, auth_headers, user, db_session):
    """Con todas servidas, la sesión sigue (sin repetir la recién respondida) en vez de quedarse sin pregunta."""
    await _seed_two_tracks(db_session)
    await _see_lesson(db_session, user, "sk_scope_a")

    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_scope_a", "mode": "study"}, headers=_h(auth_headers))
    data = r.json()
    current = data["question"]["id"]
    for _ in range(4):
        r = await client.post(
            f"{QUIZ}/answer",
            json={"session_id": data["session_id"], "question_id": current, "selected_index": 0, "response_time_ms": 1000},
            headers=_h(auth_headers),
        )
        assert r.status_code == 200, r.text
        nxt = r.json()["next_question"]
        assert nxt is not None
        assert nxt["id"] != current
        current = nxt["id"]
