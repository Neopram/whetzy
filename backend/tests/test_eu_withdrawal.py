"""Tests for EU withdrawal waiver in checkout (21.4)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_checkout_requires_auth(client: AsyncClient) -> None:
    r = await client.post("/api/v1/billing/checkout", json={"price_id": "price_test"})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_checkout_accepts_eu_waiver_field(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/billing/checkout",
        json={"price_id": "price_test", "eu_withdrawal_waiver": True},
        headers=auth_headers,
    )
    # Stripe is not configured in test env, so we expect 503 (not a validation error)
    assert r.status_code in (200, 503)


@pytest.mark.asyncio
async def test_checkout_without_waiver(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/billing/checkout",
        json={"price_id": "price_test"},
        headers=auth_headers,
    )
    # Should work without waiver (defaults to false) — 503 from Stripe being unconfigured
    assert r.status_code in (200, 503)


@pytest.mark.asyncio
async def test_renewal_reminder_email_template() -> None:
    from app.services.email import _render
    subject, html = _render("renewal_reminder", "en", name="Test", plan_name="Pro", renewal_date="2026-10-26", amount="$14.99")
    assert "Test" in html
    assert "Pro" in html
    assert "2026-10-26" in html
    assert "$14.99" in html
    assert "renew" in subject.lower()

    subject_es, html_es = _render("renewal_reminder", "es", name="Test", plan_name="Pro", renewal_date="2026-10-26", amount="$14.99")
    assert "renueva" in subject_es.lower() or "renovar" in subject_es.lower() or "renuev" in subject_es.lower()
    assert "Test" in html_es
