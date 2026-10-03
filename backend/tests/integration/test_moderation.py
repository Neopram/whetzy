"""Integration tests for UGC moderation (19.11, App Store 1.2/1.2.1).

Routes under test:
  POST   /api/v1/moderation/report
  POST   /api/v1/moderation/block
  DELETE /api/v1/moderation/block/{user_id}
  GET    /api/v1/moderation/blocked
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User

BASE = "/api/v1/moderation"


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    other = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"other{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Other User",
        language="es",
    )
    db_session.add(other)
    await db_session.commit()
    return other


@pytest_asyncio.fixture
def other_headers(other_user: User) -> dict[str, str]:
    token = create_access_token(other_user.id)
    return {"Authorization": f"Bearer {token}"}


# ── Auth guards ───────────────────────────────────────────────────────────────


async def test_report_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{BASE}/report", json={"reported_user_id": str(uuid.uuid4()), "reason": "spam"})
    assert resp.status_code == 401


async def test_block_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{BASE}/block", json={"user_id": str(uuid.uuid4())})
    assert resp.status_code == 401


# ── POST /report ──────────────────────────────────────────────────────────────


async def test_report_user_success(client: AsyncClient, auth_headers: dict, other_user: User) -> None:
    resp = await client.post(
        f"{BASE}/report",
        json={"reported_user_id": str(other_user.id), "reason": "harassment", "context": "duel"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["reported_id"] == str(other_user.id)
    assert data["reason"] == "harassment"


async def test_report_self_rejected(client: AsyncClient, auth_headers: dict, user: User) -> None:
    resp = await client.post(
        f"{BASE}/report",
        json={"reported_user_id": str(user.id), "reason": "spam"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


async def test_report_invalid_reason_rejected(client: AsyncClient, auth_headers: dict, other_user: User) -> None:
    resp = await client.post(
        f"{BASE}/report",
        json={"reported_user_id": str(other_user.id), "reason": "not-a-real-reason"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_report_unknown_user_404(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        f"{BASE}/report",
        json={"reported_user_id": str(uuid.uuid4()), "reason": "spam"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── block / unblock / list ────────────────────────────────────────────────────


async def test_block_then_list_then_unblock(
    client: AsyncClient, auth_headers: dict, other_user: User
) -> None:
    block = await client.post(f"{BASE}/block", json={"user_id": str(other_user.id)}, headers=auth_headers)
    assert block.status_code == 201, block.text
    assert block.json()["user_id"] == str(other_user.id)

    listed = await client.get(f"{BASE}/blocked", headers=auth_headers)
    assert listed.status_code == 200
    assert [b["user_id"] for b in listed.json()] == [str(other_user.id)]

    # Idempotent: bloquear dos veces no duplica la fila ni falla.
    again = await client.post(f"{BASE}/block", json={"user_id": str(other_user.id)}, headers=auth_headers)
    assert again.status_code == 201

    unblocked = await client.delete(f"{BASE}/block/{other_user.id}", headers=auth_headers)
    assert unblocked.status_code == 204

    listed_after = await client.get(f"{BASE}/blocked", headers=auth_headers)
    assert listed_after.json() == []


async def test_block_self_rejected(client: AsyncClient, auth_headers: dict, user: User) -> None:
    resp = await client.post(f"{BASE}/block", json={"user_id": str(user.id)}, headers=auth_headers)
    assert resp.status_code == 400


async def test_own_blocked_list_does_not_leak_to_the_blocked_side(
    client: AsyncClient, auth_headers: dict, other_headers: dict, other_user: User
) -> None:
    """La lista de "a quién bloqueé" es solo mía, no de a quién me bloquearon."""
    block = await client.post(f"{BASE}/block", json={"user_id": str(other_user.id)}, headers=auth_headers)
    assert block.status_code == 201

    other_list = await client.get(f"{BASE}/blocked", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []
