"""Single source of truth for all prices (ADR-41, 38.1).

Owner's decision (2026-09-24): Pro $14.99/mo, Pro Max $19.99/mo,
Creador $99.99/mo (80/20 of each sale), certification exam $39.99
one-time (ADR-49).

Every frontend and doc reference to a price MUST match these values.
The test ``test_constantes_planes.py`` enforces this by grepping the
frontend source for ``$`` amounts that don't come from here.
"""

from __future__ import annotations

from decimal import Decimal

PRO_MONTHLY_USD = Decimal("14.99")
PRO_MAX_MONTHLY_USD = Decimal("19.99")
CREATOR_MONTHLY_USD = Decimal("99.99")
CREATOR_REVENUE_SHARE = Decimal("0.80")
CERT_EXAM_USD = Decimal("39.99")

PRICES = {
    "pro": PRO_MONTHLY_USD,
    "pro_max": PRO_MAX_MONTHLY_USD,
    "creator": CREATOR_MONTHLY_USD,
    "cert_exam": CERT_EXAM_USD,
}
