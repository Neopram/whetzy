"""29.4: Promo code batch generation, web-only redemption, idempotent canje."""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.economy import PromoCode
from app.models.user import User

REDEEM_URL = "/api/v1/economy/promo/redeem"
BATCH_URL = "/api/v1/admin/promo/batch"


async def _user(db: AsyncSession, **kw: object) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"promo-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"promo{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Promo Tester",
        language="es",
        **kw,
    )
    db.add(u)
    await db.commit()
    return u


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}"}


@pytest_asyncio.fixture
async def promo(db_session: AsyncSession) -> PromoCode:
    p = PromoCode(
        code="TESTCODE",
        code_type="campaign",
        credits=100,
        max_uses=5,
        created_by="test",
    )
    db_session.add(p)
    await db_session.commit()
    return p


async def test_native_client_rejected(client: AsyncClient, db_session, promo):
    user = await _user(db_session, is_premium=True, subscription_status="active")
    for platform in ("ios", "android", "iOS", "Android"):
        resp = await client.post(
            REDEEM_URL,
            json={"code": "TESTCODE"},
            headers={**_h(user), "X-Platform": platform},
        )
        assert resp.status_code == 403, f"Platform {platform} should be rejected"
        assert "web app" in resp.json()["detail"]


async def test_web_client_allowed(client: AsyncClient, db_session, promo):
    user = await _user(db_session, is_premium=True, subscription_status="active")
    resp = await client.post(
        REDEEM_URL,
        json={"code": "TESTCODE"},
        headers={**_h(user), "X-Platform": "web"},
    )
    assert resp.status_code == 200


async def test_no_platform_header_allowed(client: AsyncClient, db_session, promo):
    user = await _user(db_session, is_premium=True, subscription_status="active")
    resp = await client.post(
        REDEEM_URL,
        json={"code": "TESTCODE"},
        headers=_h(user),
    )
    assert resp.status_code == 200


async def test_redeem_idempotent(client: AsyncClient, db_session, promo):
    user = await _user(db_session, is_premium=True, subscription_status="active")
    headers = _h(user)
    r1 = await client.post(REDEEM_URL, json={"code": "TESTCODE"}, headers=headers)
    assert r1.status_code == 200
    r2 = await client.post(REDEEM_URL, json={"code": "TESTCODE"}, headers=headers)
    assert r2.status_code == 400


async def test_redeem_rate_limit(client: AsyncClient, db_session):
    """5 redemptions per 10 min window; 6th must be rejected."""
    from app.api.v1.endpoints.economy import _promo_limiter

    _promo_limiter._hits.clear()
    user = await _user(db_session, is_premium=True, subscription_status="active")
    headers = _h(user)
    for i in range(6):
        code_obj = PromoCode(
            code=f"RATE{i}",
            code_type="campaign",
            credits=10,
            max_uses=100,
            created_by="test",
        )
        db_session.add(code_obj)
    await db_session.commit()

    for i in range(5):
        resp = await client.post(
            REDEEM_URL, json={"code": f"RATE{i}"}, headers=headers
        )
        assert resp.status_code == 200, f"Attempt {i+1} should succeed"

    resp = await client.post(
        REDEEM_URL, json={"code": "RATE5"}, headers=headers
    )
    assert resp.status_code == 429
    _promo_limiter._hits.clear()


async def test_admin_batch_generates_codes(client: AsyncClient, owner):
    resp = await client.post(
        f"{BATCH_URL}?code_type=campaign&credits=50&count=3&max_uses=10&language=es",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert len(data["codes"]) == 3
    assert "csv" in data
    for code in data["codes"]:
        for ch in "0OIL1":
            assert ch not in code, f"Code {code} contains ambiguous char {ch}"


async def test_admin_batch_requires_auth(client: AsyncClient):
    resp = await client.post(
        f"{BATCH_URL}?code_type=campaign&credits=50&count=1",
    )
    assert resp.status_code == 401
