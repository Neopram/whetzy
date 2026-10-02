"""El 422 de validación no devuelve lo que envió el usuario (ASVS V7.1) y un
validador que lanza ValueError da 422, no 500."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_a_short_password_is_not_echoed_back(client: AsyncClient):
    secret = "Sh0rt!"
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "username": "ana_echo", "display_name": "Ana",
              "password": secret, "age_confirmed": True},
    )
    assert r.status_code == 422
    assert secret not in r.text
    assert all(set(e) == {"type", "loc", "msg"} for e in r.json()["detail"])


@pytest.mark.asyncio
async def test_a_validator_value_error_is_a_422_not_a_500(client: AsyncClient, auth_headers: dict[str, str]):
    r = await client.post(
        "/api/v1/reports/question",
        json={"question_id": "q1", "reason": "not-a-reason"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert "reason must be one of" in r.json()["detail"][0]["msg"]
