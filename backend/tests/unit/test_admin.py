"""Admin panel endpoints tests."""


import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_admin_metrics_users(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/metrics/users?range_days=7",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "dau" in data
    assert "wau" in data
    assert "mau" in data
    assert data["range_days"] == 7


@pytest.mark.asyncio
async def test_admin_metrics_funnel(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/metrics/funnel?segment=es",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_users" in data
    assert "active_7d" in data
    assert "active_1d" in data
    assert "retention_d1" in data
    assert "retention_d7" in data


@pytest.mark.asyncio
async def test_admin_security_auth_events(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/security/auth-events?limit=50&offset=0",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "events" in data
    assert "limit" in data
    assert "offset" in data


@pytest.mark.asyncio
async def test_admin_security_lockouts(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/security/lockouts?active_only=true",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "lockouts" in data
    assert "active_only" in data


@pytest.mark.asyncio
async def test_admin_ops_health(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/ops/health",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_admin_ops_database(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/ops/database",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "tables" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_admin_gdpr_exports(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/gdpr/exports?status=pending&limit=50&offset=0",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "exports" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_admin_gdpr_deletions(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/gdpr/deletions?status=pending&limit=50&offset=0",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "deletions" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_admin_revenue_mrr(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/revenue/mrr?month=2026-09",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "month" in data
    assert "mrr" in data
    assert data["status"] == "test_mode"


@pytest.mark.asyncio
async def test_admin_economy_credits(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/economy/credits?limit=50&offset=0",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "entries" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_admin_economy_referrals(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/economy/referrals?status=all&limit=50&offset=0",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "referrals" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_admin_economy_k_factor(client: AsyncClient, owner: User) -> None:
    response = await client.get(
        "/api/v1/admin/economy/k-factor",
        headers={"Authorization": f"Bearer {owner.token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "k_factor" in data
    assert "total_users" in data
    assert "successful_referrals" in data


@pytest.mark.asyncio
async def test_admin_unauthorized_user(client: AsyncClient, user: User) -> None:
    """Regular users should not access admin endpoints."""
    response = await client.get(
        "/api/v1/admin/metrics/users",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_unauthenticated(client: AsyncClient) -> None:
    """Unauthenticated requests should fail."""
    response = await client.get("/api/v1/admin/metrics/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

