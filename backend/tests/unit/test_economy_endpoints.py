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
async def test_prices_has_cache_control(client: AsyncClient) -> None:
    response = await client.get("/api/v1/economy/prices")
    assert response.status_code == status.HTTP_200_OK
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=" in cc
