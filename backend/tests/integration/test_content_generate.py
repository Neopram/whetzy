"""Integration tests for POST /content/generate (task 5.1).

Tests the AI content author agent endpoint.  The LLM is always mocked so tests
run without a real GROQ_API_KEY.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, patch

from app.models.content import Module, Skill, Track

CONTENT = "/api/v1/content"
ADMIN_KEY = "test-admin-key-5-1"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _admin(key: str = ADMIN_KEY) -> dict:
    return {"X-Admin-Key": key}


_SOURCE_TEXT = (
    "Photosynthesis is the process by which green plants convert light energy "
    "into chemical energy stored as glucose.  Chlorophyll in chloroplasts "
    "absorbs sunlight; carbon dioxide and water are the raw materials; oxygen "
    "is released as a byproduct.  The light-dependent reactions occur in the "
    "thylakoid membranes, while the Calvin cycle occurs in the stroma."
)

_SOURCE_CITATION = "Campbell Biology, 11th edition, chapter 10"

_MOCK_LLM_RESPONSE = json.dumps([
    {
        "question_es": "¿Cuál es el subproducto de la fotosíntesis?",
        "question_en": "What is the byproduct of photosynthesis?",
        "options_es": ["Glucosa", "Dióxido de carbono", "Oxígeno", "Agua"],
        "options_en": ["Glucose", "Carbon dioxide", "Oxygen", "Water"],
        "correct_index": 2,
        "explanation_es": "El oxígeno se libera como subproducto.",
        "explanation_en": "Oxygen is released as a byproduct.",
        "difficulty_tier": "easy",
    },
    {
        "question_es": "¿Dónde ocurre el ciclo de Calvin?",
        "question_en": "Where does the Calvin cycle occur?",
        "options_es": ["Membrana tilacoidea", "Estroma", "Citoplasma", "Núcleo"],
        "options_en": ["Thylakoid membrane", "Stroma", "Cytoplasm", "Nucleus"],
        "correct_index": 1,
        "explanation_es": "El ciclo de Calvin ocurre en el estroma del cloroplasto.",
        "explanation_en": "The Calvin cycle occurs in the stroma of the chloroplast.",
        "difficulty_tier": "medium",
    },
])


async def _make_skill(db_session) -> Skill:
    uid = uuid.uuid4().hex[:8]
    track = Track(id=f"tr_{uid}", name_es="Biología", name_en="Biology", order=1, icon="🧬", color="#10b981", total_questions=0)
    mod = Module(id=f"mod_{uid}", track_id=f"tr_{uid}", name_es="Plantas", name_en="Plants", order=1, description_es="", description_en="")
    skill = Skill(id=f"sk_{uid}", module_id=f"mod_{uid}", name_es="Fotosíntesis", name_en="Photosynthesis", order=1)
    db_session.add_all([track, mod, skill])
    await db_session.commit()
    await db_session.refresh(skill)
    return skill


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_generate_returns_201_with_questions(client, db_session, monkeypatch):
    """Happy-path: LLM returns valid JSON, questions are inserted."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    skill = await _make_skill(db_session)

    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value=_MOCK_LLM_RESPONSE)

    with patch("app.services.content_agent.get_provider", return_value=mock_provider):
        r = await client.post(
            f"{CONTENT}/generate",
            json={
                "skill_id": skill.id,
                "source_text": _SOURCE_TEXT,
                "source_citation": _SOURCE_CITATION,
                "n": 2,
            },
            headers=_admin(),
        )

    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body) == 2
    assert body[0]["correct_index"] == 2
    assert body[1]["difficulty_tier"] == "medium"
    assert body[0]["source"] == _SOURCE_CITATION


async def test_generate_returns_503_when_no_llm(client, db_session, monkeypatch):
    """When NullProvider is active, endpoint returns 503."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    skill = await _make_skill(db_session)

    from app.services.ai.provider import NullProvider
    with patch("app.services.content_agent.get_provider", return_value=NullProvider()):
        r = await client.post(
            f"{CONTENT}/generate",
            json={
                "skill_id": skill.id,
                "source_text": _SOURCE_TEXT,
                "source_citation": _SOURCE_CITATION,
            },
            headers=_admin(),
        )

    assert r.status_code == 503


async def test_generate_requires_admin_key(client, db_session):
    """Missing admin key returns 403."""
    r = await client.post(
        f"{CONTENT}/generate",
        json={
            "skill_id": "sk_any",
            "source_text": _SOURCE_TEXT,
            "source_citation": _SOURCE_CITATION,
        },
    )
    assert r.status_code == 403


async def test_generate_wrong_admin_key(client, db_session, monkeypatch):
    """Wrong admin key returns 403."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(
        f"{CONTENT}/generate",
        json={
            "skill_id": "sk_any",
            "source_text": _SOURCE_TEXT,
            "source_citation": _SOURCE_CITATION,
        },
        headers=_admin("wrong-key"),
    )
    assert r.status_code == 403


async def test_generate_returns_422_for_unknown_skill(client, db_session, monkeypatch):
    """Non-existent skill_id raises 422 (ValueError from service)."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)

    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value=_MOCK_LLM_RESPONSE)

    with patch("app.services.content_agent.get_provider", return_value=mock_provider):
        r = await client.post(
            f"{CONTENT}/generate",
            json={
                "skill_id": "sk_does_not_exist",
                "source_text": _SOURCE_TEXT,
                "source_citation": _SOURCE_CITATION,
            },
            headers=_admin(),
        )

    assert r.status_code == 422


async def test_generate_rejects_short_source_text(client, db_session, monkeypatch):
    """source_text shorter than 50 chars returns 422 validation error."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(
        f"{CONTENT}/generate",
        json={
            "skill_id": "sk_any",
            "source_text": "Too short",
            "source_citation": _SOURCE_CITATION,
        },
        headers=_admin(),
    )
    assert r.status_code == 422


async def test_generate_persists_questions_to_db(client, db_session, monkeypatch):
    """Generated questions actually appear in the database."""
    from sqlalchemy import select as sa_select

    from app.models.content import Question

    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    skill = await _make_skill(db_session)

    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value=_MOCK_LLM_RESPONSE)

    with patch("app.services.content_agent.get_provider", return_value=mock_provider):
        r = await client.post(
            f"{CONTENT}/generate",
            json={
                "skill_id": skill.id,
                "source_text": _SOURCE_TEXT,
                "source_citation": _SOURCE_CITATION,
                "n": 2,
            },
            headers=_admin(),
        )

    assert r.status_code == 201
    ids = [q["id"] for q in r.json()]

    for qid in ids:
        row = await db_session.scalar(sa_select(Question).where(Question.id == qid))
        assert row is not None
        assert row.skill_id == skill.id


async def test_generate_handles_partial_llm_failure(client, db_session, monkeypatch):
    """If some questions fail validation, the valid ones are still inserted."""
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    skill = await _make_skill(db_session)

    bad_response = json.dumps([
        {
            # good question
            "question_es": "¿Cuál es el pigmento fotosintético?",
            "question_en": "What is the photosynthetic pigment?",
            "options_es": ["Clorofila", "Hemoglobina", "Melanina", "Caroteno"],
            "options_en": ["Chlorophyll", "Hemoglobin", "Melanin", "Carotene"],
            "correct_index": 0,
            "explanation_es": "La clorofila absorbe la luz solar.",
            "explanation_en": "Chlorophyll absorbs sunlight.",
            "difficulty_tier": "easy",
        },
        {
            # bad question — only 2 options
            "question_es": "Mala pregunta",
            "question_en": "Bad question",
            "options_es": ["A", "B"],
            "options_en": ["A", "B"],
            "correct_index": 0,
            "explanation_es": "x",
            "explanation_en": "x",
            "difficulty_tier": "easy",
        },
    ])

    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value=bad_response)

    with patch("app.services.content_agent.get_provider", return_value=mock_provider):
        r = await client.post(
            f"{CONTENT}/generate",
            json={
                "skill_id": skill.id,
                "source_text": _SOURCE_TEXT,
                "source_citation": _SOURCE_CITATION,
                "n": 2,
            },
            headers=_admin(),
        )

    assert r.status_code == 201
    assert len(r.json()) == 1  # only the valid question
