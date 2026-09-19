"""Admin panel endpoints tests."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import get_password_hash
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



# --- 22.8: los tres endpoints de revenue leen la DB, no una constante -------
# El verificador adversario refuto 22.8 porque devolvian valores fijos
# ("mrr": 0, "churn_rate": 0.0) con independencia de los datos. Estos tests
# fallan si alguien vuelve a poner una constante: crean un suscriptor real y
# exigen que el numero se mueva.


async def _make_subscriber(db_session, *, tier: str, language: str = "es",
                           subscription_status: str = "active"):
    u = User(
        id=uuid.uuid4(),
        email=f"sub-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"sub{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Subscriber",
        language=language,
        subscription_status=subscription_status,
        subscription_tier=tier,
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_admin_revenue_mrr_reads_the_database(
    client: AsyncClient, owner: User, db_session
) -> None:
    """Un suscriptor 'pro' activo tiene que mover el MRR y aparecer por tier."""
    before = (
        await client.get(
            "/api/v1/admin/revenue/mrr",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    assert before["mrr"] == 0
    assert before["source"] == "db"

    await _make_subscriber(db_session, tier="pro")

    after = (
        await client.get(
            "/api/v1/admin/revenue/mrr",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    assert after["active_subscriptions"] == 1
    assert after["by_tier"] == {"pro": 1}
    assert after["mrr"] == pytest.approx(settings.PLAN_PRICE_PRO_USD)
    assert after["price_table_usd"]["pro"] == settings.PLAN_PRICE_PRO_USD


@pytest.mark.asyncio
async def test_admin_revenue_mrr_filters_by_segment(
    client: AsyncClient, owner: User, db_session
) -> None:
    """El filtro de idioma tiene que excluir al suscriptor del otro segmento."""
    await _make_subscriber(db_session, tier="plus", language="en")

    es = (
        await client.get(
            "/api/v1/admin/revenue/mrr?segment=es",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    en = (
        await client.get(
            "/api/v1/admin/revenue/mrr?segment=en",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    assert es["active_subscriptions"] == 0
    assert es["mrr"] == 0
    assert en["active_subscriptions"] == 1


@pytest.mark.asyncio
async def test_admin_revenue_conversions_reads_the_database(
    client: AsyncClient, owner: User, db_session
) -> None:
    """Con un registro que convierte, la tasa deja de ser 0."""
    await _make_subscriber(db_session, tier="plus")

    data = (
        await client.get(
            "/api/v1/admin/revenue/conversions?range_days=30",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    assert data["registered"] >= 1
    assert data["conversions"] == 1
    assert data["conversion_rate"] > 0
    assert data["source"] == "db"


@pytest.mark.asyncio
async def test_admin_revenue_churn_reads_the_database(
    client: AsyncClient, owner: User, db_session
) -> None:
    """Una cancelacion dentro de la ventana tiene que mover el churn."""
    u = await _make_subscriber(db_session, tier="pro", subscription_status="canceled")
    u.subscription_expires_at = datetime.now(UTC) - timedelta(days=3)
    db_session.add(u)
    await db_session.commit()

    data = (
        await client.get(
            "/api/v1/admin/revenue/churn?window=30d",
            headers={"Authorization": f"Bearer {owner.token}"},
        )
    ).json()
    assert data["cancelled_subscriptions"] == 1
    assert data["churn_rate"] == pytest.approx(1.0)
    assert data["source"] == "db"


@pytest.mark.asyncio
async def test_admin_revenue_never_claims_live_without_a_live_key(
    client: AsyncClient, owner: User
) -> None:
    """Sin clave sk_live_, ningun endpoint puede decir que esto es ingreso real."""
    for path in ("revenue/mrr", "revenue/conversions", "revenue/churn"):
        data = (
            await client.get(
                f"/api/v1/admin/{path}",
                headers={"Authorization": f"Bearer {owner.token}"},
            )
        ).json()
        assert data["stripe_mode"] in ("unconfigured", "test")
        assert data["status"] == "test_mode"
