"""Verifiable domain-mastery report: the numbers behind 14.9.

14.9 asks for a publicly shareable report — "p_known >= 0.95 en N de M
skills, X respuestas en Y semanas, Z% a la primera" — something a recruiter
can check against, unlike "finished the course". This module is the
computation only: three pure functions over data the caller already has
(each one independently testable with synthetic input, no DB session
required), used together by `build_domain_report`.

What this does NOT include, and why: a public URL needs a shareable token
(and therefore a new column/table — a migration) and a new, unauthenticated
API endpoint. Both are endpoint/infrastructure work outside the engine's own
terrain (see `[COORD] -> S5` in issue #89: `backend/app/api/v1/endpoints/**`
is S1's, except the motor's own). Flagged in this PR's "Fuera de alcance"
as a NECESITO to S1, not built here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MasterySummary:
    n_mastered: int
    m_total: int
    threshold: float

    @property
    def fraction(self) -> float:
        return self.n_mastered / self.m_total if self.m_total else 0.0


def compute_mastery_summary(skill_p_known: dict[str, float], threshold: float = 0.95) -> MasterySummary:
    """`N` of `M` skills at or above `threshold` p_known. `M` is every skill
    passed in, including ones never attempted (p_known at their prior) — a
    report that only counts attempted skills would let an untouched module
    quietly not count against the learner, same reasoning as
    `get_certification_readiness` in exams.py (BKT prior 0.1 for untouched
    skills, not an omission)."""
    n_mastered = sum(1 for p in skill_p_known.values() if p >= threshold)
    return MasterySummary(n_mastered=n_mastered, m_total=len(skill_p_known), threshold=threshold)


def compute_first_try_accuracy(responses: list[tuple[str, bool, datetime]]) -> float | None:
    """Percentage of DISTINCT questions the learner got right on their
    FIRST attempt at that question — not overall accuracy across every
    attempt, which would let unlimited retries inflate the number.
    `responses` is `(question_id, correct, created_at)` tuples, any order
    (sorted here by `created_at` per question). Returns None when there are
    no responses — an empty report should say "no data" explicitly, not 0%
    or 100%, both of which would be a specific, false claim."""
    if not responses:
        return None

    first_attempt_correct: dict[str, bool] = {}
    first_attempt_at: dict[str, datetime] = {}
    for question_id, correct, created_at in responses:
        if question_id not in first_attempt_at or created_at < first_attempt_at[question_id]:
            first_attempt_at[question_id] = created_at
            first_attempt_correct[question_id] = correct

    n_questions = len(first_attempt_correct)
    n_correct_first_try = sum(1 for correct in first_attempt_correct.values() if correct)
    return 100.0 * n_correct_first_try / n_questions


def compute_weeks_active(response_timestamps: list[datetime]) -> float:
    """Calendar weeks between the first and last response, inclusive of a
    minimum of one day so a single-session learner reports "< 1 week", not
    a division-adjacent zero. Returns 0.0 for no responses."""
    if not response_timestamps:
        return 0.0
    span = max(response_timestamps) - min(response_timestamps)
    days = max(span.total_seconds() / 86400.0, 1.0)
    return days / 7.0


@dataclass(frozen=True)
class DomainReport:
    mastery: MasterySummary
    total_responses: int
    weeks_active: float
    first_try_accuracy_pct: float | None

    def headline(self) -> str:
        """The one-line claim the report makes, matching 14.9's own
        example shape exactly: 'p_known >= 0.95 en N de M skills, X
        respuestas en Y semanas, Z% a la primera'."""
        weeks_label = f"{self.weeks_active:.1f}"
        if self.first_try_accuracy_pct is None:
            accuracy_label = "sin datos suficientes"
        else:
            accuracy_label = f"{self.first_try_accuracy_pct:.0f}% a la primera"
        return (
            f"p_known >= {self.mastery.threshold:.2f} en {self.mastery.n_mastered} de "
            f"{self.mastery.m_total} skills, {self.total_responses} respuestas en "
            f"{weeks_label} semanas, {accuracy_label}"
        )


def build_domain_report(
    skill_p_known: dict[str, float],
    responses: list[tuple[str, bool, datetime]],
    mastery_threshold: float = 0.95,
) -> DomainReport:
    """Combine the three independent measurements into one report. Every
    number here is either a direct count or a straightforward function of
    one — nothing here is a model prediction or a probability, so there is
    no calibration question the way there is for 14.8: a recruiter reading
    "X respuestas en Y semanas" is reading an exact fact about what
    happened, not an estimate."""
    mastery = compute_mastery_summary(skill_p_known, mastery_threshold)
    timestamps = [created_at for _question_id, _correct, created_at in responses]
    return DomainReport(
        mastery=mastery,
        total_responses=len(responses),
        weeks_active=compute_weeks_active(timestamps),
        first_try_accuracy_pct=compute_first_try_accuracy(responses),
    )
