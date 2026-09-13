"""Integration tests for POST /content/duplicates (task 5.3).

The sentence-transformers model is patched out so tests run without a network
download or GPU.  We control the embeddings directly via the mock.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch  # still used for embed_texts

import numpy as np
import pytest

from app.models.content import Module, Question, Skill, Track

CONTENT = "/api/v1/content"
ADMIN_KEY = "test-admin-key-5-3"


def _admin(key: str = ADMIN_KEY) -> dict:
    return {"X-Admin-Key": key}


async def _make_skill(db_session) -> str:
    uid = uuid.uuid4().hex[:8]
    track = Track(id=f"tr_{uid}", name_es="T", name_en="T", order=1, icon="x", color="#000", total_questions=0)
    mod = Module(id=f"m_{uid}", track_id=f"tr_{uid}", name_es="M", name_en="M", order=1, description_es="", description_en="")
    skill = Skill(id=f"sk_{uid}", module_id=f"m_{uid}", name_es="S", name_en="S", order=1)
    db_session.add_all([track, mod, skill])
    await db_session.flush()
    return f"sk_{uid}"


async def _make_question(db_session, skill_id: str, stem: str, idx: int) -> str:
    qid = f"q_dup_{uuid.uuid4().hex[:8]}"
    q = Question(
        id=qid,
        skill_id=skill_id,
        type="mcq",
        difficulty_tier="medium",
        question_es=stem,
        question_en=stem,
        options_es=["A", "B", "C", "D"],
        options_en=["A", "B", "C", "D"],
        correct_index=0,
        explanation_es="Explanation.",
        explanation_en="Explanation.",
        source="Test source",
    )
    db_session.add(q)
    await db_session.flush()
    return qid


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicates_requires_admin_key(client, db_session) -> None:
    resp = await client.post(f"{CONTENT}/duplicates", json={})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_duplicates_empty_bank_returns_zero_pairs(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    resp = await client.post(
        f"{CONTENT}/duplicates",
        json={"threshold": 0.85},
        headers=_admin(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pairs_found"] == 0
    assert body["pairs"] == []


@pytest.mark.asyncio
async def test_duplicates_detects_near_duplicate(
    client, db_session, monkeypatch
) -> None:
    skill_id = await _make_skill(db_session)
    q1 = await _make_question(db_session, skill_id, "What is a Python list?", 0)
    q2 = await _make_question(db_session, skill_id, "What is a Python list?", 1)
    await _make_question(db_session, skill_id, "Explain the GIL in CPython.", 2)
    await db_session.flush()

    # Provide fixed embeddings: q1 and q2 identical, q3 orthogonal
    def fake_embed(texts: list[str], model_name: str = "unused") -> np.ndarray:
        vecs = np.zeros((len(texts), 4), dtype=np.float32)
        vecs[0, 0] = 1.0   # q1
        vecs[1, 0] = 1.0   # q2 — identical to q1
        if len(texts) > 2:
            vecs[2, 1] = 1.0  # q3 — orthogonal
        return vecs

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    with patch("app.services.duplicate_detector.embed_texts", side_effect=fake_embed):
        resp = await client.post(
            f"{CONTENT}/duplicates",
            json={"threshold": 0.99},
            headers=_admin(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["pairs_found"] >= 1
    assert any(
        {p["q1_id"], p["q2_id"]} == {q1, q2} for p in body["pairs"]
    )


@pytest.mark.asyncio
async def test_duplicates_skill_id_filter(
    client, db_session, monkeypatch
) -> None:
    skill1 = await _make_skill(db_session)
    skill2 = await _make_skill(db_session)
    await _make_question(db_session, skill1, "Python list", 0)
    await _make_question(db_session, skill1, "Python list", 1)
    await _make_question(db_session, skill2, "Different topic here", 2)
    await db_session.flush()

    def fake_embed(texts: list[str], model_name: str = "unused") -> np.ndarray:
        # identical for first 2, distinct for 3rd
        vecs = np.zeros((len(texts), 4), dtype=np.float32)
        for idx in range(min(2, len(texts))):
            vecs[idx, 0] = 1.0
        if len(texts) > 2:
            vecs[2, 1] = 1.0
        return vecs

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    with patch("app.services.duplicate_detector.embed_texts", side_effect=fake_embed):
        resp = await client.post(
            f"{CONTENT}/duplicates",
            json={"skill_id": skill1, "threshold": 0.99},
            headers=_admin(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_questions_scanned"] == 2


@pytest.mark.asyncio
async def test_duplicates_response_shape(
    client, db_session, monkeypatch
) -> None:
    skill_id = await _make_skill(db_session)
    await _make_question(db_session, skill_id, "Q A", 0)
    await _make_question(db_session, skill_id, "Q A", 1)
    await db_session.flush()

    def fake_embed(texts: list[str], model_name: str = "unused") -> np.ndarray:
        vecs = np.zeros((len(texts), 4), dtype=np.float32)
        for i in range(len(texts)):
            vecs[i, 0] = 1.0
        return vecs

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    with patch("app.services.duplicate_detector.embed_texts", side_effect=fake_embed):
        resp = await client.post(
            f"{CONTENT}/duplicates",
            json={"threshold": 0.99},
            headers=_admin(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "total_questions_scanned" in body
    assert "pairs_found" in body
    assert "threshold" in body
    assert "pairs" in body
    if body["pairs"]:
        pair = body["pairs"][0]
        assert "q1_id" in pair
        assert "q2_id" in pair
        assert "similarity" in pair
        assert "q1_stem" in pair
        assert "q2_stem" in pair
        assert 0.0 <= pair["similarity"] <= 1.0
