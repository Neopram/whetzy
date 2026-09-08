"""A/B harness: BKT vs DKT skill-selection cohort assignment (4.6).

Cohort assignment is *deterministic*: we hash the user's UUID so each user
always lands in the same cohort across sessions, with no DB column required.

    get_cohort(user_id) -> "bkt" | "dkt"

The split ratio is controlled by ``DKT_AB_RATIO`` in settings (default 0.5).
Users with hash(user_id) % 1000 < DKT_AB_RATIO * 1000 are assigned to DKT.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Literal

from app.core.config import settings

Cohort = Literal["bkt", "dkt"]


def get_cohort(user_id: uuid.UUID) -> Cohort:
    """Return the A/B cohort for *user_id*.

    The assignment is stable: same user_id → same cohort forever, regardless
    of when the function is called or what the DB contains.
    """
    digest = hashlib.sha256(str(user_id).encode()).digest()
    bucket = int.from_bytes(digest[:4], "big") % 1000
    ratio = max(0.0, min(1.0, settings.DKT_AB_RATIO))
    return "dkt" if bucket < round(ratio * 1000) else "bkt"
