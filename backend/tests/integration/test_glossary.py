"""Integration tests for /api/v1/glossary endpoints.

Endpoints under test:
  GET /api/v1/glossary/{track_id}  — list[GlossaryTermRead]  (public, no auth required)

The glossary is reference content: no per-user state, unauthenticated access.
"""

from __future__ import annotations

import pytest

from app.models.content import GlossaryTerm


BASE = "/api/v1/glossary"


@pytest.mark.asyncio
async def test_glossary_track_not_found(client):
    """Unknown track_id → 404."""
    resp = await client.get(f"{BASE}/no-such-track")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_glossary_empty_list_for_known_track(client, content_seed):
    """Track exists but has no glossary terms → 200 with empty list."""
    resp = await client.get(f"{BASE}/{content_seed['track_id']}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_glossary_public_no_auth_required(client, content_seed):
    """Glossary is a public endpoint — no Authorization header needed."""
    # No auth headers — still 200
    resp = await client.get(f"{BASE}/{content_seed['track_id']}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_glossary_returns_seeded_term(client, db_session, content_seed):
    """Seeding a GlossaryTerm makes it appear in the response with correct shape."""
    term = GlossaryTerm(
        id="gt_test_001",
        track_id=content_seed["track_id"],
        term_es="Entero",
        term_en="Integer",
        definition_es="Número sin parte decimal.",
        definition_en="A whole number without a fractional part.",
        source="Python docs 3.13 — Built-in Types",
        order=1,
    )
    db_session.add(term)
    await db_session.commit()

    resp = await client.get(f"{BASE}/{content_seed['track_id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    t = items[0]
    assert t["id"] == "gt_test_001"
    assert t["track_id"] == content_seed["track_id"]
    assert t["term_en"] == "Integer"
    assert t["term_es"] == "Entero"
    assert "definition_es" in t
    assert "definition_en" in t
    assert t["order"] == 1


@pytest.mark.asyncio
async def test_glossary_terms_ordered(client, db_session, content_seed):
    """Multiple terms come back in ascending order."""
    for i, (en, es) in enumerate([("List", "Lista"), ("Dict", "Diccionario"), ("Tuple", "Tupla")], start=1):
        db_session.add(
            GlossaryTerm(
                id=f"gt_ord_{i:03d}",
                track_id=content_seed["track_id"],
                term_es=es,
                term_en=en,
                definition_es=f"Definición de {es}.",
                definition_en=f"Definition of {en}.",
                order=i,
            )
        )
    await db_session.commit()

    resp = await client.get(f"{BASE}/{content_seed['track_id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 3
    orders = [item["order"] for item in items]
    assert orders == sorted(orders)
