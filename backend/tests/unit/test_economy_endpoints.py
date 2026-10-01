"""Tests for economy API endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_prices_is_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/economy/prices")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "credit_value_usd" in data
    assert "grifos" in data
    assert "sumideros" in data


@pytest.mark.asyncio
async def test_prices_lists_only_what_the_code_does(client: AsyncClient) -> None:
    """La Cartera pinta esta lista tal cual: cada entrada tiene que existir en
    el código. Hasta el 2026-10-01 anunciaba onboarding, módulo, rachas y
    bienvenida (nadie los abonaba) y simulacro, informe y curso (nadie los
    cobraba). El referido tampoco se abona: credit_matured_referrals solo lo
    llaman los tests. Si se cablea una fuente, se añade aquí y en el endpoint."""
    from app.services import streak_shop

    data = (await client.get("/api/v1/economy/prices")).json()
    assert data["grifos"] == []
    assert data["sumideros"] == [{"item": "freeze_streak_1day", "cost": streak_shop.FREEZE_PRICE_CREDITS}]


def test_referral_credit_is_not_wired_while_prices_omit_it() -> None:
    """Guarda del hueco: el día que alguien llame a credit_matured_referrals
    desde app/, este test cae para que el referido vuelva a /prices (y la
    Cartera vuelva a enseñar «Invitar amigos»)."""
    import re
    from pathlib import Path

    app_dir = Path(__file__).resolve().parents[2] / "app"
    callers = [
        f"{path.relative_to(app_dir)}:{n}"
        for path in app_dir.rglob("*.py")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"(?<!def )\bcredit_matured_referrals\(", line)
    ]
    assert callers == [], f"el referido ya se abona ({callers}): añádelo a /economy/prices"


@pytest.mark.asyncio
async def test_prices_has_cache_control(client: AsyncClient) -> None:
    response = await client.get("/api/v1/economy/prices")
    assert response.status_code == status.HTTP_200_OK
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=" in cc
