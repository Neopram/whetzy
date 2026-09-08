"""Integration tests for tutor endpoint.

Route under test: POST /api/v1/tutor/explain

In the test environment GROQ_API_KEY="" (set by conftest), so get_provider()
returns NullProvider. NullProvider.complete() is fully async and requires no
network access — it extracts the grounding context from the built prompt and
returns it directly. No mocking needed.

The RAG module's retrieve() also short-circuits to [] when its index has not
been built (no build_bg() is called during tests), so no ChromaDB I/O either.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

BASE = "/api/v1/tutor"


# ── Auth guards ───────────────────────────────────────────────────────────────


async def test_explain_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{BASE}/explain", json={"question_id": "any"})
    assert resp.status_code == 401


# ── Input validation ──────────────────────────────────────────────────────────


async def test_explain_missing_question_id(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Omitting required ``question_id`` → 422 Unprocessable Entity."""
    resp = await client.post(f"{BASE}/explain", json={}, headers=auth_headers)
    assert resp.status_code == 422


async def test_explain_no_body(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Sending no body at all → 422."""
    resp = await client.post(f"{BASE}/explain", headers=auth_headers)
    assert resp.status_code == 422


# ── Happy path with NullProvider ─────────────────────────────────────────────


async def test_explain_unknown_question_returns_200(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Unknown question_id: tutor returns empty explanation gracefully, not 500."""
    resp = await client.post(
        f"{BASE}/explain",
        json={"question_id": "nonexistent_question_id"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "explanation" in data
    assert "provider" in data
    assert "grounded" in data
    assert isinstance(data["times_missed"], int)
    # grounded=False when question is not found
    assert data["grounded"] is False


async def test_explain_known_question_returns_grounded_answer(
    client: AsyncClient,
    auth_headers: dict,
    content_seed: dict,
) -> None:
    """With a seeded question, NullProvider returns the canonical explanation."""
    resp = await client.post(
        f"{BASE}/explain",
        json={"question_id": content_seed["question_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 0
    # NullProvider identifies itself as "fallback"
    assert data["provider"] == "fallback"
    assert data["grounded"] is True
    assert data["times_missed"] == 0


async def test_explain_with_conversation_history(
    client: AsyncClient,
    auth_headers: dict,
    content_seed: dict,
) -> None:
    """Passing prior conversation turns must not crash the endpoint."""
    resp = await client.post(
        f"{BASE}/explain",
        json={
            "question_id": content_seed["question_id"],
            "conversation_history": [
                {"role": "user", "content": "Can you elaborate?"},
                {"role": "assistant", "content": "Sure, let me explain."},
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "explanation" in data


async def test_explain_conversation_history_none_accepted(
    client: AsyncClient,
    auth_headers: dict,
    content_seed: dict,
) -> None:
    """Explicitly passing null for conversation_history is valid (it's optional)."""
    resp = await client.post(
        f"{BASE}/explain",
        json={"question_id": content_seed["question_id"], "conversation_history": None},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text


async def test_explain_does_not_return_500_without_api_key(
    client: AsyncClient,
    auth_headers: dict,
    content_seed: dict,
) -> None:
    """Regression guard: endpoint must never return 500 when GROQ_API_KEY is empty."""
    resp = await client.post(
        f"{BASE}/explain",
        json={"question_id": content_seed["question_id"]},
        headers=auth_headers,
    )
    assert resp.status_code != 500


async def test_explain_response_schema(
    client: AsyncClient,
    auth_headers: dict,
    content_seed: dict,
) -> None:
    """Response must include all fields defined in ExplainResponse."""
    resp = await client.post(
        f"{BASE}/explain",
        json={"question_id": content_seed["question_id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # All four ExplainResponse fields must be present
    assert set(data.keys()) >= {"explanation", "provider", "grounded", "times_missed"}
    assert isinstance(data["explanation"], str)
    assert isinstance(data["provider"], str)
    assert isinstance(data["grounded"], bool)
    assert isinstance(data["times_missed"], int)
