"""Integration tests for duel endpoints.

Routes under test:
  POST /api/v1/duels/challenge
  GET  /api/v1/duels/my
  GET  /api/v1/duels/{duel_id}/join
  POST /api/v1/duels/{duel_id}/answer
  GET  /api/v1/duels/{duel_id}/result

Key schema contracts verified here:
  - /challenge returns ``questions[]`` not ``question_ids[]``
  - /answer requires ``selected_index`` + ``response_time_ms`` (NOT ``answer_index``)
  - Two separate user accounts are needed: challenger (from conftest) + opponent
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.content import Module, Question, Skill, Track
from app.models.lesson_completion import LessonCompletion
from app.models.user import User

BASE = "/api/v1/duels"
_SKILL_ID = "sk_duel_test01"
_DUEL_Q_COUNT = 5  # must match _DUEL_QUESTIONS in duels.py


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def duel_seed(db_session: AsyncSession, user: User) -> dict:
    """Minimal content hierarchy with exactly _DUEL_Q_COUNT MCQ questions + an opponent user.

    The challenger user comes from the conftest ``user`` fixture (shared db_session).
    """
    track = Track(
        id="duel_track01",
        name_es="Duel Track",
        name_en="Duel Track",
        order=99,
        icon="⚔",
        color="#FF0000",
        total_questions=_DUEL_Q_COUNT,
    )
    mod = Module(
        id="duel_mod01",
        track_id="duel_track01",
        name_es="Duel Module",
        name_en="Duel Module",
        order=1,
        description_es="",
        description_en="",
    )
    skill = Skill(
        id=_SKILL_ID,
        module_id="duel_mod01",
        name_es="Duel Skill",
        name_en="Duel Skill",
        order=1,
    )
    db_session.add_all([track, mod, skill])
    await db_session.flush()

    questions = [
        Question(
            id=f"duel_q{i:03d}",
            skill_id=_SKILL_ID,
            type="mcq",
            difficulty_tier="easy",
            question_es=f"Pregunta de duelo {i}?",
            question_en=f"Duel question {i}?",
            options_es=["A", "B", "C"],
            options_en=["A", "B", "C"],
            correct_index=0,
            explanation_es="La respuesta es A.",
            explanation_en="The answer is A.",
            source="test",
            elo_rating=1200.0,
        )
        for i in range(_DUEL_Q_COUNT)
    ]
    db_session.add_all(questions)

    opponent = User(
        id=uuid.uuid4(),
        email=f"opponent-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"opp{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Opponent User",
        language="es",
    )
    db_session.add(opponent)
    # 43.5 (ADR-65 D7): un duelo solo va sobre una skill con la lección vista
    # por los dos.
    db_session.add_all([
        LessonCompletion(user_id=user.id, skill_id=_SKILL_ID),
        LessonCompletion(user_id=opponent.id, skill_id=_SKILL_ID),
    ])
    await db_session.commit()

    return {
        "skill_id": _SKILL_ID,
        "question_ids": [f"duel_q{i:03d}" for i in range(_DUEL_Q_COUNT)],
        "opponent": opponent,
    }


@pytest.fixture
def opponent_headers(duel_seed: dict) -> dict[str, str]:
    token = create_access_token(duel_seed["opponent"].id)
    return {"Authorization": f"Bearer {token}"}


# ── Auth guards ───────────────────────────────────────────────────────────────


async def test_challenge_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{BASE}/challenge", json={"opponent_username": "anyone"})
    assert resp.status_code == 401


async def test_my_duels_requires_auth(client: AsyncClient) -> None:
    resp = await client.get(f"{BASE}/my")
    assert resp.status_code == 401


async def test_answer_requires_auth(client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"{BASE}/{fake_id}/answer",
        json={"question_id": "x", "selected_index": 0, "response_time_ms": 100},
    )
    assert resp.status_code == 401


async def test_result_requires_auth(client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"{BASE}/{fake_id}/result")
    assert resp.status_code == 401


# ── POST /challenge ───────────────────────────────────────────────────────────


async def test_challenge_success(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """Happy path: challenger creates a duel; response shape is correct."""
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "duel_id" in data
    assert data["skill_id"] == _SKILL_ID
    # response contains questions[], NOT question_ids[]
    assert "questions" in data
    assert "question_ids" not in data
    assert len(data["questions"]) == _DUEL_Q_COUNT
    assert data["opponent_username"] == duel_seed["opponent"].username


async def test_challenge_blocked_opponent_rejected(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """19.11: un usuario bloqueado no se puede retar, en ningún sentido."""
    block = await client.post(
        "/api/v1/moderation/block",
        json={"user_id": str(duel_seed["opponent"].id)},
        headers=auth_headers,
    )
    assert block.status_code == 201, block.text

    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 403


async def test_challenge_returns_question_objects(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """Each entry in questions[] must have at least id, type, options fields."""
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    for q in resp.json()["questions"]:
        assert "id" in q
        assert "type" in q


async def test_challenge_never_picks_legacy_fill_blank(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
    db_session: AsyncSession,
) -> None:
    """Regression: legacy `fill_blank` questions have no options and no
    correct_index (see quiz.py's _select_question comment) — DuelScreen has
    no UI to answer them and the backend has no way to score them. Found via
    Playwright E2E (8.1): a duel drew one and the player got stuck on
    "Pregunta 5 de 5" with zero buttons to click and no way to finish.
    """
    db_session.add(
        Question(
            id="duel_q_legacy_fill_blank",
            skill_id=_SKILL_ID,
            type="fill_blank",
            difficulty_tier="easy",
            question_es="Legacy fill-blank: ___",
            question_en="Legacy fill-blank: ___",
            options_es=None,
            options_en=None,
            correct_index=None,
            explanation_es="n/a",
            explanation_en="n/a",
            source="test",
            elo_rating=1200.0,
        )
    )
    await db_session.commit()

    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    picked_ids = {q["id"] for q in resp.json()["questions"]}
    assert "duel_q_legacy_fill_blank" not in picked_ids
    assert picked_ids == set(duel_seed["question_ids"])


async def test_challenge_never_picks_a_reserved_mock_exam_question(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
    db_session: AsyncSession,
) -> None:
    """37.18/ADR-53 §4: a duel is not the certification mock exam, so a
    question reserved for it (`pool == "simulacro"`) must never be drawn here
    — unconditionally, not just when MOCK_EXAM_RESERVED_POOL_ENABLED is on.

    Drops the valid pool to _DUEL_Q_COUNT - 1 and adds one reserved question,
    so the assertion is deterministic rather than a probabilistic sample: if
    the reserved question were still eligible, the candidate pool would be
    exactly _DUEL_Q_COUNT again and the challenge would succeed by drawing
    all of it (reserved question included); with the exclusion in place,
    only _DUEL_Q_COUNT - 1 valid questions remain and the endpoint must
    refuse with 422, the same "not enough MCQ questions" path as elsewhere
    in this file.
    """
    leftover_id = duel_seed["question_ids"][0]
    await db_session.delete(await db_session.get(Question, leftover_id))
    reservada = Question(
        id="duel_q_reservada",
        skill_id=_SKILL_ID,
        type="mcq",
        difficulty_tier="easy",
        question_es="Reservada para el simulacro",
        question_en="Reserved for the mock exam",
        options_es=["A", "B", "C"],
        options_en=["A", "B", "C"],
        correct_index=0,
        explanation_es="n/a",
        explanation_en="n/a",
        source="test",
        elo_rating=1200.0,
        pool="simulacro",
    )
    db_session.add(reservada)
    await db_session.commit()

    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text
    assert "fewer than" in resp.json()["detail"]


async def test_challenge_self_fails(
    client: AsyncClient,
    auth_headers: dict,
    user: User,
    duel_seed: dict,  # ensure content exists in db
) -> None:
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": user.username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_challenge_unknown_opponent(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": "ghost_user_xyz", "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_challenge_missing_payload(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    resp = await client.post(f"{BASE}/challenge", json={}, headers=auth_headers)
    assert resp.status_code == 422


# ── GET /my ───────────────────────────────────────────────────────────────────


async def test_my_duels_empty(client: AsyncClient, auth_headers: dict) -> None:
    """No duels created yet — must return an empty list, not 404."""
    resp = await client.get(f"{BASE}/my", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_my_duels_after_challenge(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """After creating one duel, /my returns exactly one entry."""
    await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    resp = await client.get(f"{BASE}/my", headers=auth_headers)
    assert resp.status_code == 200
    duels = resp.json()
    assert len(duels) == 1
    assert duels[0]["skill_id"] == _SKILL_ID
    assert duels[0]["is_your_turn"] is True


async def test_my_duels_hides_a_duel_with_a_blocked_user(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """19.11 ([COORD]/[S5] 2026-10-03): un duelo pendiente creado antes de un
    bloqueo no debe seguir saliendo en /my — antes solo /challenge miraba
    is_blocked_pair, así que este duelo ya existente seguía visible."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert challenge.status_code == 201

    block = await client.post(
        "/api/v1/moderation/block",
        json={"user_id": str(duel_seed["opponent"].id)},
        headers=auth_headers,
    )
    assert block.status_code == 201, block.text

    resp = await client.get(f"{BASE}/my", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── POST /{id}/answer ─────────────────────────────────────────────────────────


async def test_answer_field_name_selected_index(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """Regression: the field must be ``selected_index``, not ``answer_index``."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    q_id = challenge.json()["questions"][0]["id"]

    # Wrong field name → 422
    bad = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "answer_index": 0, "response_time_ms": 100},
        headers=auth_headers,
    )
    assert bad.status_code == 422

    # Correct field name → 200
    good = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 100},
        headers=auth_headers,
    )
    assert good.status_code == 200


async def test_answer_success_increments_count(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert challenge.status_code == 201
    duel_id = challenge.json()["duel_id"]
    q_id = challenge.json()["questions"][0]["id"]

    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 1500},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["duel_id"] == duel_id
    assert data["answers_so_far"] == 1
    assert data["completed"] is False
    assert data["opponent_completed"] is False


async def test_answer_wrong_question_id(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """question_id not in the duel → 422."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]

    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": "not_in_this_duel", "selected_index": 0, "response_time_ms": 100},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_answer_already_answered_is_conflict(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """Answering the same question twice → 409 Conflict."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    q_id = challenge.json()["questions"][0]["id"]

    await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 100},
        headers=auth_headers,
    )
    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 1, "response_time_ms": 100},
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_answer_non_participant_is_forbidden(
    client: AsyncClient,
    duel_seed: dict,
    auth_headers: dict,
) -> None:
    """A third user who is not part of the duel gets 403."""
    # Create duel between challenger (auth_headers) and opponent
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    q_id = challenge.json()["questions"][0]["id"]

    # Create a third user with their own token
    third_user_id = uuid.uuid4()
    third_token = create_access_token(third_user_id)
    third_headers = {"Authorization": f"Bearer {third_token}"}

    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 100},
        headers=third_headers,
    )
    # get_current_user will fail to find the user → 401 or 403
    assert resp.status_code in (401, 403)


async def test_answer_rejected_after_a_block(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """19.11: un duelo pendiente bloqueado a medias ya no se puede jugar,
    ni por el bloqueador ni por el bloqueado."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    q_id = challenge.json()["questions"][0]["id"]

    block = await client.post(
        "/api/v1/moderation/block",
        json={"user_id": str(duel_seed["opponent"].id)},
        headers=auth_headers,
    )
    assert block.status_code == 201, block.text

    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 100},
        headers=auth_headers,
    )
    assert resp.status_code == 403

    resp_opponent = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": q_id, "selected_index": 0, "response_time_ms": 100},
        headers=opponent_headers,
    )
    assert resp_opponent.status_code == 403


# ── GET /{id}/result ──────────────────────────────────────────────────────────


async def test_result_before_completion_returns_202(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """Result endpoint returns 202 while the duel is still in progress."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    resp = await client.get(f"{BASE}/{duel_id}/result", headers=auth_headers)
    assert resp.status_code == 202


async def test_result_invalid_duel_id(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    resp = await client.get(f"{BASE}/not-a-uuid/result", headers=auth_headers)
    assert resp.status_code == 404


async def test_result_rejected_after_a_block(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """19.11: el bloqueo gana al estado del duelo — 403, no 202."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]

    block = await client.post(
        "/api/v1/moderation/block",
        json={"user_id": str(duel_seed["opponent"].id)},
        headers=auth_headers,
    )
    assert block.status_code == 201, block.text

    resp = await client.get(f"{BASE}/{duel_id}/result", headers=auth_headers)
    assert resp.status_code == 403


# ── Full flow ─────────────────────────────────────────────────────────────────


async def test_full_duel_flow(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """Challenger and opponent each answer all 5 questions; winner is resolved."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert challenge.status_code == 201
    duel_id = challenge.json()["duel_id"]
    question_ids = [q["id"] for q in challenge.json()["questions"]]
    assert len(question_ids) == _DUEL_Q_COUNT

    # Challenger answers all questions correctly (correct_index=0 for all seed questions)
    for q_id in question_ids:
        resp = await client.post(
            f"{BASE}/{duel_id}/answer",
            json={"question_id": q_id, "selected_index": 0, "response_time_ms": 1000},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Challenger answer failed for {q_id}: {resp.text}"

    # Last challenger answer: completed=True, opponent_completed still False
    assert resp.json()["completed"] is True
    assert resp.json()["opponent_completed"] is False

    # Duel result not yet available (opponent hasn't finished)
    mid_result = await client.get(f"{BASE}/{duel_id}/result", headers=auth_headers)
    assert mid_result.status_code == 202

    # Opponent answers all questions incorrectly (index=1, correct_index=0)
    for q_id in question_ids:
        resp = await client.post(
            f"{BASE}/{duel_id}/answer",
            json={"question_id": q_id, "selected_index": 1, "response_time_ms": 2000},
            headers=opponent_headers,
        )
        assert resp.status_code == 200, f"Opponent answer failed for {q_id}: {resp.text}"

    # Last opponent answer: both sides done
    assert resp.json()["completed"] is True
    assert resp.json()["opponent_completed"] is True

    # Result is now available
    result = await client.get(f"{BASE}/{duel_id}/result", headers=auth_headers)
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["status"] == "completed"
    assert data["skill_id"] == _SKILL_ID
    assert data["challenger"]["correct"] == _DUEL_Q_COUNT
    assert data["opponent"]["correct"] == 0
    assert data["is_draw"] is False
    assert data["winner_id"] is not None
    # challenger_id should be winner
    assert data["winner_id"] == data["challenger"]["user_id"]


async def test_answer_shows_the_rivals_recorded_answer_only_once_they_finished(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """Partida grabada: quien juega segundo ve, tras contestar cada pregunta,
    cómo le fue al rival en ESA pregunta (acierto y tiempo). Quien juega primero
    no ve nada mientras el rival no haya terminado, aunque ya haya contestado
    alguna."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    question_ids = [q["id"] for q in challenge.json()["questions"]]

    # El rival contesta la primera pero no termina: su respuesta existe y aun
    # así no se enseña, porque su partida no está grabada entera.
    first = question_ids[0]
    resp = await client.post(
        f"{BASE}/{duel_id}/answer",
        json={"question_id": first, "selected_index": 1, "response_time_ms": 3000},
        headers=opponent_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["rival"] is None

    # El retador acierta las pares (correct_index=0) y tarda distinto en cada una.
    recorded = {}
    for i, q_id in enumerate(question_ids):
        selected, ms = (0 if i % 2 == 0 else 2), 1000 + 250 * i
        recorded[q_id] = {"correct": selected == 0, "response_time_ms": ms}
        resp = await client.post(
            f"{BASE}/{duel_id}/answer",
            json={"question_id": q_id, "selected_index": selected, "response_time_ms": ms},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rival"] is None

    # El rival juega segundo, en otro orden: cada respuesta trae la del retador
    # a esa misma pregunta, no a otra.
    for q_id in reversed(question_ids[1:]):
        resp = await client.post(
            f"{BASE}/{duel_id}/answer",
            json={"question_id": q_id, "selected_index": 1, "response_time_ms": 3000},
            headers=opponent_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rival"] == recorded[q_id]


# ── GET /{id}/join ────────────────────────────────────────────────────────────


async def test_join_requires_auth(client: AsyncClient, duel_seed: dict, auth_headers: dict) -> None:
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    resp = await client.get(f"{BASE}/{duel_id}/join")
    assert resp.status_code == 401


async def test_join_only_opponent_can_join(
    client: AsyncClient,
    auth_headers: dict,
    duel_seed: dict,
) -> None:
    """The challenger calling /join on their own duel gets 403."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    resp = await client.get(f"{BASE}/{duel_id}/join", headers=auth_headers)
    assert resp.status_code == 403


async def test_join_returns_questions(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """Opponent calling /join gets the same 5 questions the challenger received."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert challenge.status_code == 201
    duel_id = challenge.json()["duel_id"]
    challenge_q_ids = {q["id"] for q in challenge.json()["questions"]}

    resp = await client.get(f"{BASE}/{duel_id}/join", headers=opponent_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["duel_id"] == duel_id
    assert data["skill_id"] == _SKILL_ID
    assert len(data["questions"]) == _DUEL_Q_COUNT
    join_q_ids = {q["id"] for q in data["questions"]}
    assert join_q_ids == challenge_q_ids


async def test_join_rejected_after_a_block(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """19.11: el bloqueador no puede unirse a un duelo pendiente propio."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]

    block = await client.post(
        "/api/v1/moderation/block",
        json={"user_id": str(duel_seed["opponent"].id)},
        headers=auth_headers,
    )
    assert block.status_code == 201, block.text

    resp = await client.get(f"{BASE}/{duel_id}/join", headers=opponent_headers)
    assert resp.status_code == 403


async def test_join_after_completion_is_conflict(
    client: AsyncClient,
    auth_headers: dict,
    opponent_headers: dict,
    duel_seed: dict,
) -> None:
    """Once the opponent has answered all questions, /join returns 409."""
    challenge = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    duel_id = challenge.json()["duel_id"]
    question_ids = [q["id"] for q in challenge.json()["questions"]]

    for q_id in question_ids:
        await client.post(
            f"{BASE}/{duel_id}/answer",
            json={"question_id": q_id, "selected_index": 0, "response_time_ms": 500},
            headers=opponent_headers,
        )

    resp = await client.get(f"{BASE}/{duel_id}/join", headers=opponent_headers)
    assert resp.status_code == 409


# ── 43.5 (ADR-65 D7): duelo solo con la lección vista por los dos ────────────


async def test_challenge_needs_the_challengers_lesson(
    client: AsyncClient, auth_headers: dict, duel_seed: dict, db_session: AsyncSession, user: User
) -> None:
    from sqlalchemy import delete

    await db_session.execute(delete(LessonCompletion).where(LessonCompletion.user_id == user.id))
    await db_session.commit()
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "needs_lesson"


async def test_challenge_needs_the_opponents_lesson(
    client: AsyncClient, auth_headers: dict, duel_seed: dict, db_session: AsyncSession
) -> None:
    from sqlalchemy import delete

    await db_session.execute(
        delete(LessonCompletion).where(LessonCompletion.user_id == duel_seed["opponent"].id)
    )
    await db_session.commit()
    resp = await client.post(
        f"{BASE}/challenge",
        json={"opponent_username": duel_seed["opponent"].username, "skill_id": _SKILL_ID},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "opponent_needs_lesson"
