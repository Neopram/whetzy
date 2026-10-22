"""Plan anual = «2 meses gratis» (H.35; dueño, 2026-10-22, ADR-70).

Unas 10 mensualidades: por debajo de 11 y nunca por debajo de 10. Si alguien cambia el
mensual sin tocar el anual, o al revés, deja de ser «2 meses gratis» y esto lo dice.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.prices import (
    PRO_ANNUAL_USD,
    PRO_MAX_ANNUAL_USD,
    PRO_MAX_MONTHLY_USD,
    PRO_MONTHLY_USD,
)


def test_precios_anuales_del_dueno() -> None:
    assert PRO_ANNUAL_USD == Decimal("149.99")
    assert PRO_MAX_ANNUAL_USD == Decimal("199.99")


def test_el_anual_son_dos_meses_gratis() -> None:
    for anual, mensual in (
        (PRO_ANNUAL_USD, PRO_MONTHLY_USD),
        (PRO_MAX_ANNUAL_USD, PRO_MAX_MONTHLY_USD),
    ):
        assert 10 * mensual <= anual < 11 * mensual
