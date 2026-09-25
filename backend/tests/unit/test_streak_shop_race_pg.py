"""Carrera real contra Postgres: el bloqueo de fila de `streak_shop.buy` (35.3).

SQLite (la base de la suite) no tiene `FOR UPDATE` ni conexiones concurrentes,
así que este test solo corre si `WHETZY_PG_TEST_URL` apunta a un Postgres de
pruebas (p. ej. `postgresql+asyncpg://postgres@localhost:5433/e2e`, ya migrado).

Medido el 2026-09-24 con 8 compras simultáneas y saldo para una, abriendo una
ventana de 0,3 s entre comprobar y cobrar: **con** el bloqueo, 1 compra y
−150 créditos; **sin** él, 8 compras y −1.200 créditos sobre un saldo de 150.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.economy import CreditLedger
from app.models.user import User
from app.services import streak_shop
from app.services.economy import CreditsService

PG_URL = os.environ.get("WHETZY_PG_TEST_URL")

pytestmark = pytest.mark.skipif(not PG_URL, reason="WHETZY_PG_TEST_URL no definido")


@pytest.mark.asyncio
async def test_concurrent_buys_charge_once(monkeypatch: pytest.MonkeyPatch) -> None:
    assert PG_URL is not None
    engine = create_async_engine(PG_URL, pool_size=10)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    uid = uuid.uuid4()
    try:
        async with factory() as s:
            s.add(User(id=uid, email=f"race-{uid.hex[:8]}@example.com", username=f"race{uid.hex[:8]}",
                       hashed_password="x", display_name="R", language="es", streak_freeze_available=0))
            await s.commit()
            await CreditsService.grant_credits(s, uid, streak_shop.FREEZE_PRICE_CREDITS, "admin_adjust", ref_id="race")
            await s.commit()

        original = streak_shop.quote

        async def slow_quote(*args, **kwargs):  # type: ignore[no-untyped-def]
            q = await original(*args, **kwargs)
            await asyncio.sleep(0.3)  # la ventana entre comprobar y cobrar
            return q

        monkeypatch.setattr(streak_shop, "quote", slow_quote)

        async def attempt() -> str:
            async with factory() as s:
                user = await s.get(User, uid)
                assert user is not None
                try:
                    await streak_shop.buy(s, user, uuid.uuid4())
                    await s.commit()
                    return "ok"
                except streak_shop.FreezePurchaseError as exc:
                    await s.rollback()
                    return exc.reason

        results = await asyncio.gather(*[attempt() for _ in range(8)])

        async with factory() as s:
            held = (await s.get(User, uid)).streak_freeze_available  # type: ignore[union-attr]
            spent = (
                await s.execute(
                    select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(
                        CreditLedger.user_id == uid, CreditLedger.amount < 0
                    )
                )
            ).scalar()
        assert results.count("ok") == 1, results
        assert held == 1
        assert spent == -streak_shop.FREEZE_PRICE_CREDITS
    finally:
        await engine.dispose()
