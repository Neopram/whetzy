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

NOT in scope here: `backend/app/services/gamification/service.py:315`
hardcodes the same `0.95` independently (`UserSkillState.p_known >= 0.95`)
but is S1's file, not the motor's (SESIONES.md §4.3) — flagged as a
NECESITO to S1 rather than fixed here.
"""

from __future__ import annotations

from app.core.config import settings

MASTERY_THRESHOLD: float = settings.MASTERY_THRESHOLD
DEFAULT_MODULE_UNLOCK_MASTERY: float = settings.DEFAULT_MODULE_UNLOCK_MASTERY
