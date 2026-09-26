"""Tests for HMAC-SHA256 admin auth (22.15 phase 3)."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import secrets
import time

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.admin_auth import _seen_nonces, require_admin

ADMIN_KEY = "test-admin-secret-key-for-hmac"

app = FastAPI()


@app.get("/protected")
async def protected(_: None = Depends(require_admin)):
    return {"ok": True}


def _sign(method: str, path: str, key: str = ADMIN_KEY) -> dict[str, str]:
    ts = str(int(time.time()))
    nonce = secrets.token_hex(16)
    message = f"{ts}.{nonce}.{method}.{path}"
    sig = hmac_mod.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {
        "X-Admin-Timestamp": ts,
        "X-Admin-Nonce": nonce,
        "X-Admin-Signature": sig,
    }


@pytest.fixture(autouse=True)
def _clear_nonces():
    _seen_nonces.clear()
    yield
    _seen_nonces.clear()


@pytest.fixture
def _set_admin_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    monkeypatch.setattr("app.core.config.settings.ENVIRONMENT", "development")


@pytest.mark.asyncio
async def test_hmac_valid_signature(_set_admin_key):
    headers = _sign("GET", "/protected")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_hmac_wrong_key(_set_admin_key):
    headers = _sign("GET", "/protected", key="wrong-key")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers=headers)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_hmac_expired_timestamp(_set_admin_key):
    ts = str(int(time.time()) - 600)
    nonce = secrets.token_hex(16)
    message = f"{ts}.{nonce}.GET./protected"
    sig = hmac_mod.new(ADMIN_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-Admin-Timestamp": ts,
        "X-Admin-Nonce": nonce,
        "X-Admin-Signature": sig,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers=headers)
    assert r.status_code == 401
    assert "Timestamp" in r.json()["detail"]


@pytest.mark.asyncio
async def test_hmac_replay_nonce(_set_admin_key):
    headers = _sign("GET", "/protected")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r1 = await c.get("/protected", headers=headers)
        assert r1.status_code == 200
        r2 = await c.get("/protected", headers=headers)
        assert r2.status_code == 401
        assert "Nonce" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_hmac_short_nonce(_set_admin_key):
    ts = str(int(time.time()))
    nonce = "short"
    message = f"{ts}.{nonce}.GET./protected"
    sig = hmac_mod.new(ADMIN_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-Admin-Timestamp": ts,
        "X-Admin-Nonce": nonce,
        "X-Admin-Signature": sig,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers=headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_plaintext_key_allowed_in_dev(_set_admin_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers={"X-Admin-Key": ADMIN_KEY})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_plaintext_key_rejected_in_production(_set_admin_key, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ENVIRONMENT", "production")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers={"X-Admin-Key": ADMIN_KEY})
    assert r.status_code == 401
    assert "HMAC" in r.json()["detail"]


@pytest.mark.asyncio
async def test_no_credentials_rejected(_set_admin_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_wrong_plaintext_key_rejected(_set_admin_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers={"X-Admin-Key": "wrong"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_no_admin_key_configured(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", "")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/protected", headers={"X-Admin-Key": "anything"})
    assert r.status_code == 403
