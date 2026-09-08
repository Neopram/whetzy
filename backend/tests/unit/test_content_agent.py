"""Unit tests for the content author agent (5.1).

Tests the JSON parsing, validation, and question building without calling the LLM.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.content_agent import _GeneratedQ, _extract_json, _make_question_id


# ── JSON extraction ───────────────────────────────────────────────────────────

def test_extract_json_plain_array():
    raw = '[{"question_es": "Pregunta", "question_en": "Question"}]'
    data = _extract_json(raw)
    assert isinstance(data, list)
    assert data[0]["question_es"] == "Pregunta"


def test_extract_json_with_markdown_fences():
    raw = "```json\n[{\"a\": 1}]\n```"
    data = _extract_json(raw)
    assert data == [{"a": 1}]


def test_extract_json_with_prose():
    raw = "Here are the questions:\n[{\"a\": 1}]\nHope you enjoy!"
    data = _extract_json(raw)
    assert data == [{"a": 1}]


def test_extract_json_raises_on_no_array():
    import pytest
    with pytest.raises(ValueError, match="No JSON array"):
        _extract_json("just some text, no brackets")


# ── Schema validation ─────────────────────────────────────────────────────────

_VALID_Q = {
    "question_es": "¿Qué es Python?",
    "question_en": "What is Python?",
    "options_es": ["Un lenguaje", "Un reptil", "Un IDE", "Una librería"],
    "options_en": ["A language", "A reptile", "An IDE", "A library"],
    "correct_index": 0,
    "explanation_es": "Python es un lenguaje de programación.",
    "explanation_en": "Python is a programming language.",
    "difficulty_tier": "easy",
}


def test_valid_question_parses():
    q = _GeneratedQ.model_validate(_VALID_Q)
    assert q.correct_index == 0
    assert len(q.options_es) == 4
    assert q.difficulty_tier == "easy"


def test_unknown_difficulty_defaults_to_medium():
    data = dict(_VALID_Q, difficulty_tier="legendary")
    q = _GeneratedQ.model_validate(data)
    assert q.difficulty_tier == "medium"


def test_wrong_option_count_raises():
    from pydantic import ValidationError
    data = dict(_VALID_Q, options_es=["A", "B"])
    with pytest.raises(ValidationError):
        _GeneratedQ.model_validate(data)


def test_correct_index_out_of_range_raises():
    from pydantic import ValidationError
    data = dict(_VALID_Q, correct_index=5)
    with pytest.raises(ValidationError):
        _GeneratedQ.model_validate(data)


def test_question_id_is_unique():
    id1 = _make_question_id("sk_test", 0)
    id2 = _make_question_id("sk_test", 0)
    assert id1 != id2
    assert id1.startswith("sk_test_")
