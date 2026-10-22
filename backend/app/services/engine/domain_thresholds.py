"""Single source of truth for the motor's domain/mastery thresholds (C.1,
2026-10-04).

Before this module existed, `app/services/quiz.py`, `app/services/engine/
bkt.py` and `app/services/domain_report.py` each hardcoded their OWN
`0.95` mastery-threshold literal, independent of `app.core.config.Settings.
MASTERY_THRESHOLD` and of each other. Only `app/services/progress.py`
actually read `settings.MASTERY_THRESHOLD` (confirmed with grep before
writing this) — the other three would keep using `0.95` forever even if
the owner changed the setting, and in the meantime could silently disagree
with progress.py's own number. The same pattern showed up for the module
unlock default: `app/services/content_loader.py` hardcoded its own `0.7`
fallback, independent of `settings.DEFAULT_MODULE_UNLOCK_MASTERY` (which
nothing read).

Every motor module that needs a domain threshold imports it from HERE —
never a bare literal, and never `app.core.config` directly (settings is
S5's module to own; this one re-exports the two values the motor cares
about under motor-owned names, read-only).
`tests/unit/test_domain_thresholds_guard.py` fails if a threshold-shaped
literal shows up in a motor file outside this one.

`gamification/service.py` hardcoded the same `0.95` on its own until 42.6
(2026-10-22); it now asks `is_mastered`, like progress.

42.6 / ADR-63 §3: there is ONE definition of a mastered skill, `is_mastered`
below — mastery at or above the threshold AND `MIN_EVIDENCE_ANSWERS` practice
answers. A duel, a test-out or the placement test move `p_known` but never
count as that evidence (`evidence_policy.py`).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_

from app.core.config import settings

MASTERY_THRESHOLD: float = settings.MASTERY_THRESHOLD
DEFAULT_MODULE_UNLOCK_MASTERY: float = settings.DEFAULT_MODULE_UNLOCK_MASTERY
MIN_EVIDENCE_ANSWERS: int = settings.MIN_EVIDENCE_ANSWERS


def is_mastered(p_known: float, practice_attempts: int) -> bool:
    return p_known >= MASTERY_THRESHOLD and practice_attempts >= MIN_EVIDENCE_ANSWERS


def mastered_clause(state: Any) -> ColumnElement[bool]:
    """`is_mastered` as a SQL condition on `UserSkillState` (or an alias of it)."""
    return and_(
        state.p_known >= MASTERY_THRESHOLD,
        state.practice_attempts >= MIN_EVIDENCE_ANSWERS,
    )
