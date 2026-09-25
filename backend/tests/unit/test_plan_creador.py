"""Plan Creador y precios del dueño (ADR-41, 2026-09-24).

Pro ($14.99, tier ``plus``) < Pro Max ($19.99, ``pro``) < Creador ($99.99,
``creator``). El Creador publica bootcamps; de cada venta se queda el 80 %.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import user_meets_tier
from app.models.user import User
from app.services.payment_service import PaymentService

COURSES = "/api/v1/instructor/courses"
BODY = {"title": "Bootcamp de prueba", "description": "d", "price_cents": 9900}


def _u(tier: str | None) -> User:
    return User(id=uuid.uuid4(), email="x@example.com", username="x", hashed_password="x",
                display_name="X", language="es", subscription_tier=tier, is_premium=False)


def test_prices_are_the_owners() -> None:
    assert settings.PLAN_PRICE_PLUS_USD == 14.99
    assert settings.PLAN_PRICE_PRO_USD == 19.99
    assert settings.PLAN_PRICE_CREATOR_USD == 99.99


def test_creator_includes_every_lower_tier() -> None:
    creator = _u("creator")
    assert all(user_meets_tier(creator, t) for t in ("plus", "pro", "creator"))
    assert not user_meets_tier(_u("pro"), "creator")


def test_split_is_eighty_twenty_after_paddle() -> None:
    r = PaymentService.calculate_instructor_payout(10000)
    after_paddle = 10000 - r["paddle_commission_cents"]
    assert r["instructor_gross_cents"] == int(after_paddle * 0.80)


@pytest.mark.asyncio
async def test_gate_off_anyone_can_publish(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "CREATOR_PLAN_REQUIRED", False)
    r = await client.post(COURSES, json=BODY, headers=auth_headers)
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_gate_on_requires_the_creator_plan(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "CREATOR_PLAN_REQUIRED", True)
    user.subscription_tier = "pro"  # Pro Max no basta
    await db_session.commit()
    r = await client.post(COURSES, json=BODY, headers=auth_headers)
    assert r.status_code == 402
    assert r.json()["detail"] == "creator_plan_required"

    user.subscription_tier = "creator"
    await db_session.commit()
    assert (await client.post(COURSES, json=BODY, headers=auth_headers)).status_code == 201


@pytest.mark.asyncio
async def test_gate_on_the_owner_can_still_publish(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "CREATOR_PLAN_REQUIRED", True)
    user.role = "owner"
    await db_session.commit()
    assert (await client.post(COURSES, json=BODY, headers=auth_headers)).status_code == 201
