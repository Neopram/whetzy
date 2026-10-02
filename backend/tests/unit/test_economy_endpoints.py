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
    cobraba). Hoy: el programa de referidos (ADR-35) y el comodín de racha."""
    from app.services import learning_rewards as lr
    from app.services import streak_shop
    from app.services.economy import (
        REFERRAL_CREDITS,
        REFERRAL_MILESTONES,
        REFERRAL_MONTHLY_CAP,
        REFERRAL_WELCOME_CREDITS,
    )

    data = (await client.get("/api/v1/economy/prices")).json()
    assert data["grifos"] == [
        {
            "event": "referral_activated",
            "credits": REFERRAL_CREDITS,
            "cap": f"{REFERRAL_MONTHLY_CAP}/month",
            "milestones": [{"at": at, "reward": reward} for at, reward in REFERRAL_MILESTONES],
        },
        {"event": "referral_welcome", "credits": REFERRAL_WELCOME_CREDITS, "cap": "once"},
        # Grifos de aprendizaje (2026-10-02, services/learning_rewards).
        {"event": "diagnostic_done", "credits": lr.DIAGNOSTIC_CREDITS, "cap": "once"},
        {"event": "module_done", "credits": lr.MODULE_CREDITS, "cap": "per_module"},
        {"event": "skill_skipped", "credits": lr.SKILL_SKIPPED_CREDITS, "cap": "500/month"},
        {"event": "streak_7", "credits": lr.STREAK_7_CREDITS, "cap": "per_week"},
        {"event": "streak_30", "credits": lr.STREAK_30_CREDITS, "cap": "per_month"},
    ]
    assert data["learning_monthly_cap"] == 1500
    assert data["sumideros"] == [
        {"item": "freeze_streak_1day", "cost": streak_shop.FREEZE_PRICE_CREDITS}
    ]


def test_referral_program_loop_is_started() -> None:
    """/prices anuncia el referido: algo tiene que activarlo y abonarlo. Hasta
    el 2026-10-01 nada llamaba a credit_matured_referrals fuera de los tests y
    la Cartera prometía créditos que no llegaban. Si alguien quita el bucle del
    arranque, este test cae."""
    from pathlib import Path

    main = (Path(__file__).resolve().parents[2] / "app" / "main.py").read_text(encoding="utf-8")
    assert "asyncio.create_task(referral_program_loop(" in main

    economy = (
        Path(__file__).resolve().parents[2] / "app" / "services" / "economy.py"
    ).read_text(encoding="utf-8")
    loop = economy[economy.index("async def referral_program_loop("):]
    assert "activate_ready_referrals(db)" in loop
    assert "credit_matured_referrals(db)" in loop


@pytest.mark.asyncio
async def test_prices_has_cache_control(client: AsyncClient) -> None:
    response = await client.get("/api/v1/economy/prices")
    assert response.status_code == status.HTTP_200_OK
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=" in cc
