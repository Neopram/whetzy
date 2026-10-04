"""Integration tests for POST /ml/rollback (S.2, 2026-10-04).

Admin-only: this endpoint swaps the DKT checkpoint that serves every live
user's skill-selection in one call — a plain learner must not be able to
roll back a production model. Does not exercise `_Registry` itself (that's
tests/unit/test_model_registry.py); only the HTTP-level auth boundary.
"""

from __future__ import annotations

import pytest

from app.core.security import create_access_token

ML = "/api/v1/ml"


def _h(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.mark.asyncio
async def test_rollback_requires_auth(client) -> None:
    resp = await client.post(f"{ML}/rollback", params={"version": 1})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rollback_rejects_a_non_admin_user(client, auth_headers) -> None:
    resp = await client.post(f"{ML}/rollback", params={"version": 1}, headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_rollback_lets_an_admin_through_the_auth_gate(client, owner) -> None:
    """An admin clears the 403 gate — what happens next (404 with no
    checkpoints in this test environment) is _Registry's own business,
    covered by test_model_registry.py."""
    resp = await client.post(f"{ML}/rollback", params={"version": 1}, headers=_h(owner))
    assert resp.status_code != 403
