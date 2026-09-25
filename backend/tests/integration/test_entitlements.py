"""Integration tests for server-side feature entitlement gates (7.3).

Verifies:
- Tutor /explain returns 403 for free users, 200 (mocked) for Plus users
- Quiz /start with mode="exam" returns 403 for free users
- Quiz /start with mode="review" is free: spaced review is the engine (ADR-41)
- Quiz /start with mode="study" is always allowed (free tier)
- Plus users can start exam + review sessions
"""

from __future__ import annotations

import itertools
import uuid
from unittest.mock import AsyncMock, patch

from app.core.security import create_access_token
from app.models.user import User

QUIZ = "/api/v1/quiz"
TUTOR = "/api/v1/tutor"

_ip_counter = itertools.count(500)


def _ip() -> str:
    n = next(_ip_counter)
    return f"192.0.3.{n % 255 or 255}"


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _ip()}
    if extra:
        headers.update(extra)
    return headers


def _auth(user: User) -> dict:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


async def _make_plus_user(db_session) -> User:
    from app.core.security import get_password_hash
    u = User(
        id=uuid.uuid4(),
        email=f"plus-{uuid.uuid4().hex[:6]}@whetzy.test",
        username=f"plus{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Plus User",
        language="es",
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ── Tutor gating ─────────────────────────────────────────────────────────────


async def test_tutor_explain_forbidden_for_free_user(client, user, content_seed):
    r = await client.post(
        f"{TUTOR}/explain",
        json={"question_id": content_seed["question_id"]},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 403, r.text
    assert "Plus" in r.json()["detail"]


async def test_tutor_explain_allowed_for_plus_user(client, db_session, content_seed):
    plus_user = await _make_plus_user(db_session)
    with patch("app.services.ai.tutor.explain_question", new_callable=AsyncMock) as mock_explain:
        mock_explain.return_value = {
            "explanation": "Here is the explanation.",
            "provider": "mock",
            "grounded": False,
            "times_missed": 0,
        }
        r = await client.post(
            f"{TUTOR}/explain",
            json={"question_id": content_seed["question_id"]},
            headers=_h(_auth(plus_user)),
        )
    assert r.status_code == 200, r.text
    assert r.json()["explanation"] == "Here is the explanation."


# ── Quiz mode gating ──────────────────────────────────────────────────────────


async def test_quiz_exam_mode_forbidden_for_free_user(client, user, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "exam"},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 403, r.text
    assert "Plus" in r.json()["detail"]


async def test_quiz_review_mode_allowed_for_free_user(client, user, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "review"},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 200, r.text


async def test_quiz_study_mode_allowed_for_free_user(client, user, content_seed):
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 200, r.text


async def test_quiz_exam_mode_allowed_for_plus_user(client, db_session, content_seed):
    plus_user = await _make_plus_user(db_session)
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "exam"},
        headers=_h(_auth(plus_user)),
    )
    assert r.status_code == 200, r.text


async def test_quiz_review_mode_allowed_for_plus_user(client, db_session, content_seed):
    plus_user = await _make_plus_user(db_session)
    r = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "review"},
        headers=_h(_auth(plus_user)),
    )
    assert r.status_code == 200, r.text
