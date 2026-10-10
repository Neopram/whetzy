"""Perfil de instructor (28.8): `ProfileTab` no llamaba a nada — `GET`/`PATCH
/instructor/profile` existen desde aquí. Publicar un curso convierte en
instructor (`_current_instructor`), así que cualquier usuario autenticado
tiene un perfil, creado al vuelo si hace falta.
"""

from __future__ import annotations

from httpx import AsyncClient

BASE = "/api/v1/instructor/profile"


async def test_profile_requires_auth(client: AsyncClient) -> None:
    resp = await client.get(BASE)
    assert resp.status_code == 401


async def test_get_profile_creates_instructor_on_the_fly(client: AsyncClient, auth_headers: dict, user) -> None:
    resp = await client.get(BASE, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["display_name"] == user.display_name
    assert data["bio"] is None
    assert data["avatar_url"] is None
    assert data["website"] is None


async def test_update_profile_persists_fields(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.patch(
        BASE,
        json={
            "display_name": "Jane Teaches Python",
            "bio": "10 years building backends.",
            "avatar_url": "https://example.com/avatar.png",
            "website": "https://example.com",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data == {
        "display_name": "Jane Teaches Python",
        "bio": "10 years building backends.",
        "avatar_url": "https://example.com/avatar.png",
        "website": "https://example.com",
    }

    # Persiste de verdad: una segunda lectura ve lo mismo.
    again = await client.get(BASE, headers=auth_headers)
    assert again.json() == data


async def test_update_profile_partial_keeps_other_fields(client: AsyncClient, auth_headers: dict) -> None:
    await client.patch(BASE, json={"bio": "Original bio"}, headers=auth_headers)
    resp = await client.patch(BASE, json={"website": "https://example.org"}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["bio"] == "Original bio"
    assert data["website"] == "https://example.org"


async def test_update_profile_rejects_empty_display_name(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.patch(BASE, json={"display_name": ""}, headers=auth_headers)
    assert resp.status_code == 422
