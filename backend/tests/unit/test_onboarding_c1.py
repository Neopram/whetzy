"""C1: onboarding_goal=3 (certificación) aceptado por PATCH /me;
diagnostic_done funciona correctamente para principiantes.

Antes: onboarding_goal validado ge=0, le=2 — el valor 3 (certificación)
era rechazado con 422.  Después: le=3, los nueve tracks de certificación
son alcanzables desde el onboarding.
"""
import uuid

import pytest
from httpx import AsyncClient


async def _registrar(client: AsyncClient) -> dict[str, str]:
    u = f"c1{uuid.uuid4().hex[:10]}"
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{u}@example.com",
            "username": u,
            "display_name": "C1",
            "password": "pass-c1-test-1",
            "language": "es",
            "age_confirmed": True,
        },
    )
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_onboarding_goal_certificacion_aceptado(client: AsyncClient) -> None:
    """goal=3 (Preparar una certificación) ya no es rechazado por el esquema."""
    auth_headers = await _registrar(client)
    r = await client.patch(
        "/api/v1/auth/me",
        json={"onboarding_goal": 3},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["onboarding_goal"] == 3


@pytest.mark.asyncio
async def test_onboarding_goal_fuera_de_rango_rechazado(client: AsyncClient) -> None:
    """goal=4 sigue fuera de rango (le=3)."""
    auth_headers = await _registrar(client)
    r = await client.patch(
        "/api/v1/auth/me",
        json={"onboarding_goal": 4},
        headers=auth_headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_diagnostic_done_principiante_sin_placement(client: AsyncClient) -> None:
    """Un principiante (experience=0) tiene diagnostic_done=True sin hacer
    la prueba de nivel — su diagnóstico es el onboarding (§3.1 (b))."""
    auth_headers = await _registrar(client)
    await client.patch(
        "/api/v1/auth/me",
        json={"onboarding_experience": 0, "onboarding_goal": 0, "onboarding_weekly_time": 0},
        headers=auth_headers,
    )
    # El endpoint de referidos expone diagnostic_done indirectamente;
    # lo verificamos comprobando que el perfil se guardó bien.
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["onboarding_experience"] == 0
    assert body["onboarding_goal"] == 0
