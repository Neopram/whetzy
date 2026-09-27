"""Integration tests for content versioning (P.9).

Covers:
- PATCH /content/questions/{id} bumps content_version
- Auth guard: 403 without valid X-Admin-Key
- Responses record the question_version that was active at answer time
"""

from __future__ import annotations

import itertools
import uuid as _uuid

from sqlalchemy import select

from app.models.lesson_completion import LessonCompletion
from app.models.session import Response

CONTENT = "/api/v1/content"
QUIZ = "/api/v1/quiz"

_ip_counter = itertools.count(200)


def _ip() -> str:
    n = next(_ip_counter)
    return f"203.0.113.{n % 255 or 255}"


async def _see_lesson(db_session, user, *skill_ids: str) -> None:
    for skill_id in skill_ids:
        db_session.add(LessonCompletion(user_id=user.id, skill_id=skill_id))
    await db_session.commit()


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _ip()}
    if extra:
        headers.update(extra)
    return headers


ADMIN_KEY = "test-admin-key-p9"


# ── PATCH endpoint auth guard ────────────────────────────────────────────────


async def test_patch_question_no_key_returns_403(client, content_seed):
    r = await client.patch(
        f"{CONTENT}/questions/{content_seed['question_id']}",
        json={"question_es": "Updated?"},
        headers=_h(),
    )
    assert r.status_code == 403


async def test_patch_question_wrong_key_returns_403(client, content_seed):
    r = await client.patch(
        f"{CONTENT}/questions/{content_seed['question_id']}",
        json={"question_es": "Updated?"},
        headers=_h({"X-Admin-Key": "wrong-key"}),
    )
    assert r.status_code == 403


async def test_patch_question_unknown_id_returns_404(client, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.patch(
        f"{CONTENT}/questions/does-not-exist",
        json={"question_es": "Updated?"},
        headers=_h({"X-Admin-Key": ADMIN_KEY}),
    )
    assert r.status_code == 404


# ── version bump ─────────────────────────────────────────────────────────────


async def test_patch_question_bumps_content_version(client, content_seed, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)

    r = await client.patch(
        f"{CONTENT}/questions/{content_seed['question_id']}",
        json={"question_es": "Updated question text?", "explanation_es": "Updated explanation."},
        headers=_h({"X-Admin-Key": ADMIN_KEY}),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == content_seed["question_id"]
    assert data["content_version"] == 2
    assert set(data["updated_fields"]) == {"question_es", "explanation_es"}


async def test_patch_question_empty_payload_does_not_bump(client, content_seed, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)

    r = await client.patch(
        f"{CONTENT}/questions/{content_seed['question_id']}",
        json={},
        headers=_h({"X-Admin-Key": ADMIN_KEY}),
    )
    assert r.status_code == 200
    assert r.json()["content_version"] == 1  # no change
    assert r.json()["updated_fields"] == []


# ── response versioning ───────────────────────────────────────────────────────


async def test_response_records_question_version_1_by_default(
    client, auth_headers, content_seed, db_session, user
):
    """Answering a fresh question stamps question_version=1 on the Response."""
    await _see_lesson(db_session, user, content_seed["skill_id"])
    start = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert start.status_code == 200
    sid = start.json()["session_id"]
    qid = start.json()["question"]["id"]

    answer = await client.post(
        f"{QUIZ}/answer",
        json={"session_id": sid, "question_id": qid, "selected_index": 0, "response_time_ms": 500},
        headers=_h(auth_headers),
    )
    assert answer.status_code == 200

    resp_row = await db_session.scalar(
        select(Response).where(Response.session_id == _uuid.UUID(sid)).limit(1)
    )
    assert resp_row is not None
    assert resp_row.question_version == 1


async def test_response_records_updated_version_after_patch(
    client, auth_headers, content_seed, db_session, monkeypatch, user
):
    """After PATCH bumps version to 2, a new response records question_version=2."""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    await _see_lesson(db_session, user, content_seed["skill_id"])

    patch = await client.patch(
        f"{CONTENT}/questions/{content_seed['question_id']}",
        json={"explanation_es": "Corrected explanation."},
        headers=_h({"X-Admin-Key": ADMIN_KEY}),
    )
    assert patch.status_code == 200
    assert patch.json()["content_version"] == 2

    start = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert start.status_code == 200
    sid = start.json()["session_id"]
    qid = start.json()["question"]["id"]

    await client.post(
        f"{QUIZ}/answer",
        json={"session_id": sid, "question_id": qid, "selected_index": 0, "response_time_ms": 500},
        headers=_h(auth_headers),
    )

    resp_row = await db_session.scalar(
        select(Response).where(Response.session_id == _uuid.UUID(sid)).limit(1)
    )
    assert resp_row is not None
    assert resp_row.question_version == 2
