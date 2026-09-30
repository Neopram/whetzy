"""Cupo diario del plan Free detrás de flag (39.4, ADR-50a).

Con `FREE_DAILY_QUOTA_ENABLED` apagado (el valor de producción hasta que abra el
cobro) nada cambia para nadie. Encendido: un usuario Free recibe como mucho
`FREE_DAILY_NEW_QUESTIONS` preguntas nuevas en modo estudio y
`FREE_DAILY_LESSONS` lecciones distintas por día UTC; el repaso FSRS, el
placement y los exámenes quedan fuera, y Pro, el dueño y los admins no tienen cupo.
Los límites se bajan a 2 en los tests para no responder 30 preguntas.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import settings
from app.models.content import Lesson, Module, Question, Skill, Track
from app.models.lesson_completion import LessonCompletion
from app.models.lesson_view import LessonView
from app.models.session import Response, StudySession
from app.services import content_quota


async def _see(db_session, user_id, *skill_ids: str) -> None:
    """32.4: el estudio de un skill exige haber visto su lección primero."""
    for skill_id in skill_ids:
        db_session.add(LessonCompletion(user_id=user_id, skill_id=skill_id))
    await db_session.commit()


@pytest.fixture
def quota_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "FREE_DAILY_QUOTA_ENABLED", True)
    monkeypatch.setattr(settings, "FREE_DAILY_NEW_QUESTIONS", 2)
    monkeypatch.setattr(settings, "FREE_DAILY_LESSONS", 2)


@pytest_asyncio.fixture
async def bank(db_session) -> dict:
    """Un skill con 6 preguntas y tres skills con una lección cada uno."""
    db_session.add(Track(id="trackq", name_es="Cupo", name_en="Quota", order=1, icon="x",
                         color="#000000", total_questions=6))
    db_session.add(Module(id="mq01", track_id="trackq", name_es="M", name_en="M", order=1,
                          description_es="", description_en=""))
    skills = ["skq1", "skq2", "skq3"]
    for i, sid in enumerate(skills):
        db_session.add(Skill(id=sid, module_id="mq01", name_es=sid, name_en=sid, order=i + 1))
        db_session.add(Lesson(id=f"l_{sid}", skill_id=sid, title_es="t", title_en="t",
                              body_es="b", body_en="b", source="https://docs.python.org/3/"))
    for n in range(6):
        db_session.add(Question(
            id=f"qq{n}", skill_id="skq1", type="mcq", difficulty_tier="easy",
            question_es=f"¿{n}?", question_en=f"{n}?", options_es=["a", "b"], options_en=["a", "b"],
            correct_index=0, explanation_es="e", explanation_en="e", source="s", elo_rating=1200.0,
        ))
    await db_session.commit()
    return {"skills": skills}


async def _start(client, headers, mode="study"):
    return await client.post("/api/v1/quiz/start", json={"skill_id": "skq1", "mode": mode}, headers=headers)


async def _answer(client, headers, session_id, question_id):
    return await client.post(
        "/api/v1/quiz/answer",
        json={"session_id": session_id, "question_id": question_id, "selected_index": 0,
              "response_time_ms": 500},
        headers=headers,
    )


async def _answer_n(client, headers, n: int) -> dict:
    start = await _start(client, headers)
    assert start.status_code == 200, start.text
    body = start.json()
    sid, q = body["session_id"], body["question"]["id"]
    last: dict = {}
    for _ in range(n):
        r = await _answer(client, headers, sid, q)
        assert r.status_code == 200, r.text
        last = r.json()
        if last["next_question"] is None:
            break
        q = last["next_question"]["id"]
    return last


# ── Preguntas ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_flag_off_nothing_changes(client, auth_headers, user, db_session, bank, monkeypatch) -> None:
    monkeypatch.setattr(settings, "FREE_DAILY_NEW_QUESTIONS", 2)
    assert settings.FREE_DAILY_QUOTA_ENABLED is False
    await _see(db_session, user.id, "skq1")
    last = await _answer_n(client, auth_headers, 3)
    assert last["next_question"] is not None
    assert last["quota_reached"] is False
    assert (await _start(client, auth_headers)).status_code == 200


@pytest.mark.asyncio
async def test_free_user_stops_after_the_daily_new_questions(client, auth_headers, user, db_session, bank, quota_on) -> None:
    await _see(db_session, user.id, "skq1")
    last = await _answer_n(client, auth_headers, 2)
    assert last["quota_reached"] is True
    assert last["next_question"] is None

    blocked = await _start(client, auth_headers)
    assert blocked.status_code == 429
    detail = blocked.json()["detail"]
    assert detail["code"] == "free_daily_quota"
    assert detail["kind"] == "questions"
    assert detail["limit"] == 2
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    assert detail["resets_at"].startswith(tomorrow.isoformat())


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["review", "placement"])
async def test_review_and_placement_are_exempt(client, auth_headers, user, db_session, bank, quota_on, mode) -> None:
    await _see(db_session, user.id, "skq1")
    await _answer_n(client, auth_headers, 2)
    assert (await _start(client, auth_headers)).status_code == 429
    assert (await _start(client, auth_headers, mode=mode)).status_code == 200


@pytest.mark.asyncio
async def test_exam_mode_is_exempt(client, plus_auth_headers, bank, quota_on) -> None:
    assert content_quota.EXEMPT_MODES >= {"exam"}
    assert (await _start(client, plus_auth_headers, mode="exam")).status_code == 200


@pytest.mark.asyncio
async def test_pro_user_has_no_quota(client, plus_auth_headers, plus_user, db_session, bank, quota_on) -> None:
    await _see(db_session, plus_user.id, "skq1")
    last = await _answer_n(client, plus_auth_headers, 3)
    assert last["quota_reached"] is False
    assert last["next_question"] is not None
    assert (await _start(client, plus_auth_headers)).status_code == 200


@pytest.mark.asyncio
async def test_owner_has_no_quota(client, owner, db_session, bank, quota_on) -> None:
    await _see(db_session, owner.id, "skq1")
    headers = {"Authorization": f"Bearer {owner.token}"}
    last = await _answer_n(client, headers, 3)
    assert last["quota_reached"] is False


@pytest.mark.asyncio
async def test_admin_has_no_quota(db_session, user, quota_on) -> None:
    user.is_admin = True
    await db_session.commit()
    assert content_quota.applies_to(user) is False
    assert await content_quota.new_questions_left(db_session, user, "study") is None


@pytest.mark.asyncio
async def test_a_question_seen_before_today_is_not_new(db_session, user, bank, quota_on) -> None:
    yesterday = datetime.now(UTC) - timedelta(days=1)
    old = StudySession(user_id=user.id, mode="study", skill_id="skq1")
    today = StudySession(user_id=user.id, mode="study", skill_id="skq1")
    db_session.add_all([old, today])
    await db_session.flush()
    db_session.add(Response(session_id=old.id, question_id="qq0", correct=True, grade=3,
                            response_time_ms=1, created_at=yesterday))
    for q in ("qq0", "qq1"):
        db_session.add(Response(session_id=today.id, question_id=q, correct=True, grade=3,
                                response_time_ms=1, created_at=datetime.now(UTC)))
    await db_session.commit()
    assert await content_quota.new_questions_on(db_session, user.id, datetime.now(UTC).date()) == 1


@pytest.mark.asyncio
async def test_review_answers_do_not_spend_the_quota(db_session, user, bank, quota_on) -> None:
    review = StudySession(user_id=user.id, mode="review", skill_id="skq1")
    db_session.add(review)
    await db_session.flush()
    for q in ("qq0", "qq1", "qq2"):
        db_session.add(Response(session_id=review.id, question_id=q, correct=True, grade=3,
                                response_time_ms=1, created_at=datetime.now(UTC)))
    await db_session.commit()
    assert await content_quota.new_questions_left(db_session, user, "study") == 2


# ── Lecciones ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_free_user_gets_the_daily_lessons_then_429(client, auth_headers, bank, quota_on) -> None:
    for sid in ("skq1", "skq2", "skq1"):  # reabrir la misma no gasta
        r = await client.get(f"/api/v1/lessons/{sid}", headers=auth_headers)
        assert r.status_code == 200, r.text
    blocked = await client.get("/api/v1/lessons/skq3", headers=auth_headers)
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["kind"] == "lessons"


@pytest.mark.asyncio
async def test_lessons_stay_public_without_a_session(client, bank, quota_on) -> None:
    for sid in ("skq1", "skq2", "skq3"):
        assert (await client.get(f"/api/v1/lessons/{sid}")).status_code == 200


@pytest.mark.asyncio
async def test_a_lesson_with_a_session_is_never_cached(client, auth_headers, bank) -> None:
    """2026-09-30: servida de la caché del navegador, la visita no llegaría al
    backend y ni se registraría la lección vista ni se contaría el cupo."""
    r = await client.get("/api/v1/lessons/skq1", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers["cache-control"] == "private, no-store"


@pytest.mark.asyncio
async def test_an_anonymous_lesson_is_cached_but_varies_by_session(client, bank) -> None:
    r = await client.get("/api/v1/lessons/skq1")
    assert r.status_code == 200
    assert r.headers["cache-control"].startswith("public, ")
    vary = {v.strip().lower() for v in r.headers["vary"].split(",")}
    assert {"authorization", "cookie"} <= vary


@pytest.mark.asyncio
async def test_a_bad_token_reads_as_anonymous(client, bank, quota_on) -> None:
    r = await client.get("/api/v1/lessons/skq1", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_flag_off_writes_no_lesson_views(client, auth_headers, bank, db_session) -> None:
    for sid in ("skq1", "skq2", "skq3"):
        assert (await client.get(f"/api/v1/lessons/{sid}", headers=auth_headers)).status_code == 200
    rows = (await db_session.execute(select(LessonView))).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_pro_user_has_no_lesson_quota(client, plus_auth_headers, bank, quota_on) -> None:
    for sid in ("skq1", "skq2", "skq3"):
        assert (await client.get(f"/api/v1/lessons/{sid}", headers=plus_auth_headers)).status_code == 200
