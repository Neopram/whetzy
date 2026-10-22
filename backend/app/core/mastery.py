"""The one definition of a mastered skill (42.6, ADR-63 §3).

Mastery at or above `MASTERY_THRESHOLD` AND `MIN_EVIDENCE_ANSWERS` answers of
PRACTICE. A duel, a test-out or the placement test move `p_known`, but never
count as that evidence (`app/services/engine/evidence_policy.py`).

It lives in `core`, below both the motor and gamification, because both need
it and neither may import the other (`tests/unit/test_service_boundaries.py`).
The motor re-exports it from `app.services.engine.domain_thresholds`;
`tests/unit/test_domain_thresholds_guard.py` fails if anyone else compares a
mastery value with the threshold on their own.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_

from app.core.config import settings

MASTERY_THRESHOLD: float = settings.MASTERY_THRESHOLD
MIN_EVIDENCE_ANSWERS: int = settings.MIN_EVIDENCE_ANSWERS


def is_mastered(p_known: float, practice_attempts: int) -> bool:
    return p_known >= MASTERY_THRESHOLD and practice_attempts >= MIN_EVIDENCE_ANSWERS


def mastered_clause(state: Any) -> ColumnElement[bool]:
    """`is_mastered` as a SQL condition on `UserSkillState` (or an alias of it)."""
    return and_(
        state.p_known >= MASTERY_THRESHOLD,
        state.practice_attempts >= MIN_EVIDENCE_ANSWERS,
    )
