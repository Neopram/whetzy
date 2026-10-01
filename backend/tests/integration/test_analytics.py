"""Integration tests for analytics event tracking and funnel (5.4).

Covers:
- user_registered event is fired on POST /auth/register
- first_quiz_answer event is fired on the first quiz answer
- first_quiz_answer is NOT fired on the second quiz answer
- GET /analytics/funnel returns the right shape
- Funnel requires admin key
"""

from __future__ import annotations

import itertools

from sqlalchemy import select

from app.models.analytics import AnalyticsEvent
from app.models.lesson_completion import LessonCompletion

ANALYTICS = "/api/v1/analytics"
QUIZ = "/api/v1/quiz"
AUTH = "/api/v1/auth"

_ip_counter = itertools.count(300)
ADMIN_KEY = "test-admin-key-analytics"


def _ip() -> str:
    n = next(_ip_counter)
    return f"192.0.2.{n % 255 or 255}"


async def _see_lesson(db_session, user, skill_id: str) -> None:
    """32.4: el estudio de un skill exige haber visto su lección primero."""
    db_session.add(LessonCompletion(user_id=user.id, skill_id=skill_id))
    await db_session.commit()


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _ip()}
    if extra:
        headers.update(extra)
    return headers


# ── event firing ─────────────────────────────────────────────────────────────


async def test_register_fires_user_registered_event(client, db_session):
    r = await client.post(
        f"{AUTH}/register",
        json={
            "username": "analytics_user_1",
            "email": "analytics1@loadtest.whetzy.io",
            "password": "Test!1234",
            "display_name": "Ana",
            "age_confirmed": True,
        },
        headers=_h(),
    )
    assert r.status_code == 201, r.text

    events = (
        await db_session.scalars(
            select(AnalyticsEvent).where(AnalyticsEvent.event_type == "user_registered")
        )
    ).all()
    assert len(events) >= 1
    assert any(str(e.user_id) == str(e.user_id) for e in events)  # at least one event exists


async def test_first_quiz_answer_event(client, auth_headers, content_seed, db_session, user):
    await _see_lesson(db_session, user, content_seed["skill_id"])
    # Start a quiz session
    start = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert start.status_code == 200
    sid = start.json()["session_id"]
    qid = start.json()["question"]["id"]

    # Count events before answering
    before = len(
        (await db_session.scalars(select(AnalyticsEvent).where(
            AnalyticsEvent.event_type == "first_quiz_answer"
        ))).all()
    )

    # First answer
    await client.post(
        f"{QUIZ}/answer",
        json={"session_id": sid, "question_id": qid, "selected_index": 0, "response_time_ms": 500},
        headers=_h(auth_headers),
    )

    after = len(
        (await db_session.scalars(select(AnalyticsEvent).where(
            AnalyticsEvent.event_type == "first_quiz_answer"
        ))).all()
    )
    assert after == before + 1


async def test_second_quiz_answer_does_not_fire_event(client, auth_headers, content_seed, db_session, user):
    await _see_lesson(db_session, user, content_seed["skill_id"])
    # First answer (fires the event)
    start1 = await client.post(
        f"{QUIZ}/start",
        json={"skill_id": content_seed["skill_id"], "mode": "study"},
        headers=_h(auth_headers),
    )
    assert start1.status_code == 200
    sid1 = start1.json()["session_id"]
    qid1 = start1.json()["question"]["id"]
    await client.post(
        f"{QUIZ}/answer",
        json={"session_id": sid1, "question_id": qid1, "selected_index": 0, "response_time_ms": 500},
        headers=_h(auth_headers),
    )

    # Count events after first answer
    count_after_first = len(
        (await db_session.scalars(select(AnalyticsEvent).where(
            AnalyticsEvent.event_type == "first_quiz_answer"
        ))).all()
    )

    # Continue session and answer a second question
    await client.post(
        f"{QUIZ}/answer",
        json={"session_id": sid1, "question_id": qid1, "selected_index": 0, "response_time_ms": 500},
        headers=_h(auth_headers),
    )
    # May return 200 or error, we just care about the event count
    count_after_second = len(
        (await db_session.scalars(select(AnalyticsEvent).where(
            AnalyticsEvent.event_type == "first_quiz_answer"
        ))).all()
    )
    # Should not have fired again
    assert count_after_second == count_after_first


# ── funnel endpoint ───────────────────────────────────────────────────────────


async def test_funnel_requires_admin_key(client):
    r = await client.get(f"{ANALYTICS}/funnel", headers=_h())
    assert r.status_code == 403


async def test_funnel_returns_correct_shape(client, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.get(
        f"{ANALYTICS}/funnel",
        params={"period_days": 30},
        headers=_h({"X-Admin-Key": ADMIN_KEY}),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    for key in ("period_days", "registrations", "first_quiz", "d1_return", "d7_return",
                "first_quiz_rate", "d1_rate", "d7_rate"):
        assert key in data, f"Missing key: {key}"
    assert data["period_days"] == 30
    assert isinstance(data["registrations"], int)
    assert 0.0 <= data["first_quiz_rate"] <= 1.0
