"""Comprar comodines de racha con créditos (ledger 37.3, `services/streak_shop.py`)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import CreditLedger, CreditReasonEnum
from app.models.user import User
from app.services import streak_shop
from app.services.economy import CreditsService

URL = "/api/v1/economy/streak-freeze"
PRICE = streak_shop.FREEZE_PRICE_CREDITS


async def _grant(db: AsyncSession, user: User, amount: int, ref: str = "t") -> None:
    await CreditsService.grant_credits(db, user.id, amount, CreditReasonEnum.ADMIN_ADJUST.value, ref_id=ref)
    await db.commit()


async def _set_held(db: AsyncSession, user: User, held: int) -> None:
    user.streak_freeze_available = held
    await db.commit()


async def _buy(client: AsyncClient, headers: dict[str, str], rid: uuid.UUID | None = None):
    return await client.post(URL, json={"request_id": str(rid or uuid.uuid4())}, headers=headers)


async def _charges(db: AsyncSession, user_id: uuid.UUID) -> list[CreditLedger]:
    # Recibe el id y no el objeto: tras el rollback de un 409 la sesión expira
    # `user` y leer `user.id` intentaría un lazy-load fuera de contexto async.
    rows = await db.execute(
        select(CreditLedger).where(
            CreditLedger.user_id == user_id,
            CreditLedger.reason == CreditReasonEnum.SPEND_FREEZE.value,
        )
    )
    return list(rows.scalars())


@pytest.mark.asyncio
async def test_quote_without_credits_says_why(client: AsyncClient, user: User, auth_headers: dict[str, str]) -> None:
    r = await client.get(URL, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["price"] == PRICE
    assert body["can_buy"] is False
    assert body["blocked_by"] == "insufficient_credits"


@pytest.mark.asyncio
async def test_buy_charges_once_and_adds_a_freeze(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    uid = user.id
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, 400)

    r = await _buy(client, auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["replayed"] is False
    assert body["held"] == 1
    assert body["balance"] == 400 - PRICE
    assert body["purchases_this_week"] == 1
    assert sum(c.amount for c in await _charges(db_session, uid)) == -PRICE


@pytest.mark.asyncio
async def test_same_request_id_never_charges_twice(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    uid = user.id
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, 400)
    rid = uuid.uuid4()

    first = await _buy(client, auth_headers, rid)
    again = await _buy(client, auth_headers, rid)

    assert first.status_code == again.status_code == 200
    assert again.json()["replayed"] is True
    assert again.json()["held"] == 1
    assert again.json()["balance"] == 400 - PRICE
    assert sum(c.amount for c in await _charges(db_session, uid)) == -PRICE


@pytest.mark.asyncio
async def test_weekly_purchase_limit(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    uid = user.id
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, 10 * PRICE)

    for _ in range(streak_shop.MAX_PURCHASES_PER_WEEK):
        assert (await _buy(client, auth_headers)).status_code == 200

    r = await _buy(client, auth_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "weekly_limit"
    assert len({c.ref_id for c in await _charges(db_session, uid)}) == streak_shop.MAX_PURCHASES_PER_WEEK


@pytest.mark.asyncio
async def test_holding_cap(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    uid = user.id
    await _set_held(db_session, user, streak_shop.MAX_FREEZES_HELD)
    await _grant(db_session, user, 400)

    r = await _buy(client, auth_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "max_held"
    assert await _charges(db_session, uid) == []


@pytest.mark.asyncio
async def test_insufficient_credits_charges_nothing(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    uid = user.id
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, PRICE - 1)

    r = await _buy(client, auth_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "insufficient_credits"
    assert await _charges(db_session, uid) == []
    assert (await client.get(URL, headers=auth_headers)).json()["held"] == 0


@pytest.mark.asyncio
async def test_a_purchase_across_two_lots_counts_once(db_session: AsyncSession, user: User) -> None:
    uid = user.id
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, 100, ref="a")
    await _grant(db_session, user, 100, ref="b")

    q, replayed = await streak_shop.buy(db_session, user, uuid.uuid4())

    assert replayed is False
    assert len(await _charges(db_session, uid)) == 2  # un cargo por lote
    assert q.purchases_this_week == 1
    assert q.balance == 200 - PRICE


@pytest.mark.asyncio
async def test_a_new_iso_week_resets_the_purchase_limit(db_session: AsyncSession, user: User) -> None:
    await _set_held(db_session, user, 0)
    await _grant(db_session, user, 10 * PRICE)
    sunday = datetime(2026, 9, 27, 23, 0, tzinfo=UTC)  # semana 39
    monday = datetime(2026, 9, 28, 0, 30, tzinfo=UTC)  # semana 40

    for _ in range(streak_shop.MAX_PURCHASES_PER_WEEK):
        await streak_shop.buy(db_session, user, uuid.uuid4(), now=sunday)
    with pytest.raises(streak_shop.FreezePurchaseError):
        await streak_shop.buy(db_session, user, uuid.uuid4(), now=sunday)

    user.streak_freeze_available = 0
    q, _ = await streak_shop.buy(db_session, user, uuid.uuid4(), now=monday)
    assert q.purchases_this_week == 1


def test_iso_week_key_across_the_year_boundary() -> None:
    # El 1 de enero de 2027 cae en la semana 53 de 2026 (ISO), no en la 1 de 2027.
    assert streak_shop.iso_week_key(datetime(2027, 1, 1, tzinfo=UTC)) == "2026-W53"
    assert streak_shop.iso_week_key(datetime(2027, 1, 4, tzinfo=UTC)) == "2027-W01"


@pytest.mark.asyncio
async def test_request_id_must_be_a_uuid(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post(URL, json={"request_id": "doble-click"}, headers=auth_headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_requires_login(client: AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401
    assert (await client.post(URL, json={"request_id": str(uuid.uuid4())})).status_code == 401
