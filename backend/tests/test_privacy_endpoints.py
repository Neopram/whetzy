"""Smoke tests for privacy endpoints (21.3)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ccpa_disclosure_public(client: AsyncClient) -> None:
    r = await client.get("/api/v1/privacy/ccpa-disclosure")
    assert r.status_code == 200
    data = r.json()
    assert "categories_collected" in data
    assert "sale_of_data" in data
    assert len(data["categories_collected"]) >= 1


@pytest.mark.asyncio
async def test_privacy_rights_public(client: AsyncClient) -> None:
    r = await client.get("/api/v1/privacy/rights")
    assert r.status_code == 200
    data = r.json()
    assert "rights" in data
    assert len(data["rights"]) >= 5
    assert data["contact"] == "support@whetzy.com"


@pytest.mark.asyncio
async def test_ccpa_opt_out_requires_auth(client: AsyncClient) -> None:
    r = await client.post("/api/v1/privacy/ccpa-opt-out")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ccpa_opt_out_cycle(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post("/api/v1/privacy/ccpa-opt-out", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["ccpa_opt_out"] is True

    r = await client.delete("/api/v1/privacy/ccpa-opt-out", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["ccpa_opt_out"] is False
