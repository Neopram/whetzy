"""B2: QuestionPublic must never expose expected execution output to the client.

The server grades fill_blank_exec, fix_bug, fill_blank, sql_exec and js_exec by
comparing the submitted output against its own stored value — sending that value
in the HTTP response lets anyone skip running code and forge a correct answer.
"""

from __future__ import annotations

import pytest

from app.schemas.content import QuestionPublic


def _make(type_: str, correct_es: str = "42", correct_en: str = "42") -> QuestionPublic:
    return QuestionPublic(
        id="q_test",
        skill_id="sk_test",
        type=type_,
        difficulty_tier="medium",
        question_es="Q",
        question_en="Q",
        correct_answer_es=correct_es,
        correct_answer_en=correct_en,
        expected_time_ms=30000,
    )


@pytest.mark.parametrize("q_type", ["fill_blank_exec", "fix_bug", "fill_blank", "sql_exec", "js_exec"])
def test_server_graded_types_never_expose_expected_output(q_type: str) -> None:
    q = _make(q_type)
    assert q.correct_answer_es is None, f"{q_type}: correct_answer_es leaked to client"
    assert q.correct_answer_en is None, f"{q_type}: correct_answer_en leaked to client"


def test_mcq_preserves_correct_answer_field_when_set() -> None:
    # mcq questions don't use correct_answer_es/en for grading (they use
    # correct_index), but the field must not be silently wiped for non-exec types.
    q = _make("mcq", correct_es="irrelevant", correct_en="irrelevant")
    assert q.correct_answer_es == "irrelevant"


def test_true_false_preserves_correct_answer_field_when_set() -> None:
    q = _make("true_false", correct_es="True", correct_en="True")
    assert q.correct_answer_es == "True"
