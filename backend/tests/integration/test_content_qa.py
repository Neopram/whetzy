"""Integration tests for POST /content/qa and POST /content/qa/batch (task 5.2)."""

from __future__ import annotations

import uuid

import pytest

from app.models.content import Module, Question, Skill, Track

CONTENT = "/api/v1/content"
ADMIN_KEY = "test-admin-key-5-2"


def _admin(key: str = ADMIN_KEY) -> dict:
    return {"X-Admin-Key": key}


async def _make_question(db_session, *, defective: bool = False, **overrides) -> Question:
    uid = uuid.uuid4().hex[:8]
    track = Track(id=f"tr_{uid}", name_es="T", name_en="T", order=1, icon="x", color="#000", total_questions=0)
    mod = Module(id=f"m_{uid}", track_id=f"tr_{uid}", name_es="M", name_en="M", order=1, description_es="", description_en="")
    skill = Skill(id=f"sk_{uid}", module_id=f"m_{uid}", name_es="S", name_en="S", order=1)
    db_session.add_all([track, mod, skill])

    defaults: dict = dict(
        id=f"q_qa_{uid}",
        skill_id=f"sk_{uid}",
        type="mcq",
        difficulty_tier="medium",
        question_es="¿Qué es el fotón?",
        question_en="What is a photon?",
        options_es=["Partícula de luz", "Átomo de hidrógeno", "Molécula de agua", "Electrón libre"],
        options_en=["Light particle", "Hydrogen atom", "Water molecule", "Free electron"],
        correct_index=0,
        explanation_es="Un fotón es una partícula de luz.",
        explanation_en="A photon is a particle of light.",
        source="Physics 101, chapter 3",
    )
    if defective:
        # Inject: too few options (CRITICAL) + no source (MEDIUM)
        defaults["options_es"] = ["A", "B"]
        defaults["options_en"] = ["A", "B"]
        defaults["source"] = ""
    defaults.update(overrides)

    q = Question(**defaults)
    db_session.add(q)
    await db_session.commit()
    await db_session.refresh(q)
    return q


# ── Single QA endpoint ────────────────────────────────────────────────────────


async def test_qa_valid_question_passes(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    q = await _make_question(db_session)

    r = await client.post(
        f"{CONTENT}/qa",
        json={"question_id": q.id},
        headers=_admin(),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["question_id"] == q.id
    assert body["passed"] is True
    assert body["score"] == 1.0
    assert body["issues"] == []


async def test_qa_defective_question_fails(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    q = await _make_question(db_session, defective=True)

    r = await client.post(
        f"{CONTENT}/qa",
        json={"question_id": q.id},
        headers=_admin(),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["passed"] is False
    assert body["score"] < 1.0
    codes = {i["code"] for i in body["issues"]}
    assert "OPT_COUNT_ES" in codes or "OPT_COUNT_EN" in codes


async def test_qa_requires_admin_key(client, db_session):
    r = await client.post(f"{CONTENT}/qa", json={"question_id": "q_anything"})
    assert r.status_code == 403


async def test_qa_unknown_question_returns_404(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(
        f"{CONTENT}/qa",
        json={"question_id": "q_does_not_exist"},
        headers=_admin(),
    )
    assert r.status_code == 404


async def test_qa_includes_severity_in_issues(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    q = await _make_question(db_session, defective=True)

    r = await client.post(f"{CONTENT}/qa", json={"question_id": q.id}, headers=_admin())
    assert r.status_code == 200
    severities = {i["severity"] for i in r.json()["issues"]}
    assert severities & {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


# ── Batch QA endpoint ─────────────────────────────────────────────────────────


async def test_qa_batch_mixed(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    good = await _make_question(db_session)
    bad = await _make_question(db_session, defective=True)

    r = await client.post(
        f"{CONTENT}/qa/batch",
        json={"question_ids": [good.id, bad.id]},
        headers=_admin(),
    )
    assert r.status_code == 200, r.text
    results = r.json()
    assert len(results) == 2
    by_id = {item["question_id"]: item for item in results}
    assert by_id[good.id]["passed"] is True
    assert by_id[bad.id]["passed"] is False


async def test_qa_batch_requires_admin_key(client, db_session):
    r = await client.post(f"{CONTENT}/qa/batch", json={"question_ids": ["q_x"]})
    assert r.status_code == 403


async def test_qa_batch_missing_question_returns_404(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(
        f"{CONTENT}/qa/batch",
        json={"question_ids": ["q_does_not_exist_1", "q_does_not_exist_2"]},
        headers=_admin(),
    )
    assert r.status_code == 404


async def test_qa_batch_empty_list_rejected(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(
        f"{CONTENT}/qa/batch",
        json={"question_ids": []},
        headers=_admin(),
    )
    assert r.status_code == 422
