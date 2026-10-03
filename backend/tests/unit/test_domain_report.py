"""Unit tests for the domain-mastery report computation (14.9).

Pure functions over synthetic (question_id, correct, created_at) tuples and
skill_id -> p_known maps — no DB session needed, matching how the full 14.9
public report would still need a real endpoint to collect this input, but
the arithmetic itself is independently verifiable here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.domain_report import (
    build_domain_report,
    compute_first_try_accuracy,
    compute_mastery_summary,
    compute_weeks_active,
)

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _at(days: float) -> datetime:
    return T0 + timedelta(days=days)


# ── compute_mastery_summary ───────────────────────────────────────────────────


def test_mastery_summary_counts_skills_at_or_above_threshold() -> None:
    summary = compute_mastery_summary({"s1": 0.95, "s2": 0.96, "s3": 0.80, "s4": 0.10}, threshold=0.95)
    assert summary.n_mastered == 2
    assert summary.m_total == 4
    assert summary.fraction == 0.5


def test_mastery_summary_counts_untouched_skills_in_the_denominator() -> None:
    """A skill the learner never touched still counts in M — otherwise
    ignoring a whole module would look the same as mastering it."""
    summary = compute_mastery_summary({"touched": 0.99, "never_touched": 0.1}, threshold=0.95)
    assert summary.m_total == 2
    assert summary.n_mastered == 1


def test_mastery_summary_empty_bank_is_zero_not_a_crash() -> None:
    summary = compute_mastery_summary({}, threshold=0.95)
    assert summary.m_total == 0
    assert summary.fraction == 0.0


# ── compute_first_try_accuracy ────────────────────────────────────────────────


def test_first_try_accuracy_uses_only_the_earliest_attempt_per_question() -> None:
    """Got q1 wrong first, then retried and got it right — only the FIRST
    attempt counts. Got q2 right immediately."""
    responses = [
        ("q1", False, _at(0)),
        ("q1", True, _at(1)),  # retry — must not count
        ("q2", True, _at(0)),
    ]
    assert compute_first_try_accuracy(responses) == 50.0


def test_first_try_accuracy_is_order_independent_in_the_input_list() -> None:
    """Same data, responses passed in a different order — must find the
    same earliest timestamp regardless of list order."""
    responses = [
        ("q1", True, _at(1)),  # later attempt listed FIRST in the list
        ("q1", False, _at(0)),  # earlier attempt listed SECOND
    ]
    assert compute_first_try_accuracy(responses) == 0.0  # the day-0 attempt was wrong


def test_first_try_accuracy_none_when_no_responses() -> None:
    assert compute_first_try_accuracy([]) is None


def test_first_try_accuracy_perfect_and_zero() -> None:
    assert compute_first_try_accuracy([("q1", True, _at(0)), ("q2", True, _at(0))]) == 100.0
    assert compute_first_try_accuracy([("q1", False, _at(0)), ("q2", False, _at(0))]) == 0.0


# ── compute_weeks_active ──────────────────────────────────────────────────────


def test_weeks_active_spans_first_to_last_response() -> None:
    assert compute_weeks_active([_at(0), _at(7), _at(14)]) == 2.0


def test_weeks_active_no_responses_is_zero() -> None:
    assert compute_weeks_active([]) == 0.0


def test_weeks_active_single_day_floors_to_one_day_not_zero() -> None:
    """Two responses an hour apart must not report "0.0 weeks" — that
    reads as no time at all, which is a different (false) claim from
    "under a week"."""
    weeks = compute_weeks_active([_at(0), _at(0) + timedelta(hours=1)])
    assert weeks > 0.0
    assert weeks == 1.0 / 7.0  # the 1-day floor


# ── build_domain_report / headline ────────────────────────────────────────────


def test_build_domain_report_combines_all_three_measurements() -> None:
    skill_p_known = {"s1": 0.97, "s2": 0.30}
    responses = [
        ("q1", True, _at(0)),
        ("q2", False, _at(0)),
        ("q2", True, _at(1)),  # retry, doesn't change the first-try count
        ("q3", True, _at(7)),
    ]

    report = build_domain_report(skill_p_known, responses, mastery_threshold=0.95)

    assert report.mastery.n_mastered == 1
    assert report.mastery.m_total == 2
    assert report.total_responses == 4
    assert report.weeks_active == 1.0
    assert report.first_try_accuracy_pct == pytest.approx(66.67, abs=0.01)


def test_headline_reads_like_the_14_9_example_shape() -> None:
    skill_p_known = {"s1": 0.97, "s2": 0.30, "s3": 0.99}
    responses = [("q1", True, _at(0)), ("q2", True, _at(7))]

    report = build_domain_report(skill_p_known, responses, mastery_threshold=0.95)
    headline = report.headline()

    assert "2 de 3 skills" in headline
    assert "2 respuestas" in headline
    assert "a la primera" in headline


def test_headline_handles_no_data_honestly() -> None:
    report = build_domain_report({"s1": 0.5}, [], mastery_threshold=0.95)
    assert "sin datos suficientes" in report.headline()
