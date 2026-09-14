"""Integration tests for streak push reminders (P.13).

Covers:
- PATCH /push/preferences → updates push_streak_enabled
- POST /push/streak-reminder → requires admin key → 403 without
- POST /push/streak-reminder → sends push to eligible users (mocked)
- POST /push/streak-reminder → skips users with no active streak
- POST /push/streak-reminder → skips users with push_streak_enabled=False
- POST /push/streak-reminder → skips users already reminded today
"""

from __future__ import annotations

import itertools
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.core.security import create_access_token, get_password_hash
from app.models.push_subscription import PushSubscription
from app.models.user import User

PUSH = "/api/v1/push"
_ip_counter = itertools.count(700)
ADMIN_KEY = "test-admin-key-p13"


def _ip() -> str:
    n = next(_ip_counter)
    return f"192.0.5.{n % 255 or 255}"


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": _ip()}
    if extra:
        headers.update(extra)
    return headers


def _auth(u: User) -> dict:
    token = create_access_token(u.id)
    return {"Authorization": f"Bearer {token}"}


async def _make_user_with_sub(db_session, *, streak: int = 5, push_enabled: bool = True,
                               last_active: datetime | None = None,
                               last_reminded: datetime | None = None) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"p13-{uuid.uuid4().hex[:6]}@whetzy.test",
        username=f"p13u{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="P13 User",
        language="es",
        current_streak=streak,
        push_streak_enabled=push_enabled,
        last_active=last_active,
        last_streak_reminder_at=last_reminded,
    )
    db_session.add(u)
    await db_session.flush()
    sub = PushSubscription(
        user_id=u.id,
        endpoint=f"https://fcm.example.com/{uuid.uuid4().hex}",
        p256dh="BNYkuMo8hVl7",
        auth="aW1h",
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ── Preferences ───────────────────────────────────────────────────────────────


async def test_patch_preferences_disables_streak_push(client, user, db_session):
    r = await client.patch(
        f"{PUSH}/preferences",
        json={"streak_enabled": False},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 200, r.text
    assert r.json()["push_streak_enabled"] is False
    await db_session.refresh(user)
    assert user.push_streak_enabled is False


async def test_patch_preferences_re_enables(client, user, db_session):
    user.push_streak_enabled = False
    await db_session.commit()
    r = await client.patch(
        f"{PUSH}/preferences",
        json={"streak_enabled": True},
        headers=_h(_auth(user)),
    )
    assert r.status_code == 200
    assert r.json()["push_streak_enabled"] is True


async def test_patch_preferences_requires_auth(client):
    r = await client.patch(f"{PUSH}/preferences", json={"streak_enabled": False}, headers=_h())
    assert r.status_code == 401


# ── Streak reminder ───────────────────────────────────────────────────────────


async def test_streak_reminder_requires_admin(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.post(f"{PUSH}/streak-reminder", headers=_h())
    assert r.status_code == 403


async def test_streak_reminder_sends_to_eligible_user(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    u = await _make_user_with_sub(db_session, streak=3, last_active=yesterday)

    send_mock = AsyncMock(return_value=1)
    with patch("app.services.push_service.send_to_user", send_mock):
        r = await client.post(
            f"{PUSH}/streak-reminder",
            headers=_h({"X-Admin-Key": ADMIN_KEY}),
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["notified_users"] >= 1
    assert data["notifications_sent"] >= 1
    # Not just 'something was sent' — it must be sent for *this* eligible user.
    assert any(call.args[1] == u.id for call in send_mock.call_args_list)


async def test_streak_reminder_skips_zero_streak(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    await _make_user_with_sub(db_session, streak=0, last_active=yesterday)

    send_mock = AsyncMock(return_value=0)
    with patch("app.services.push_service.send_to_user", send_mock):
        r = await client.post(
            f"{PUSH}/streak-reminder",
            headers=_h({"X-Admin-Key": ADMIN_KEY}),
        )
    assert r.status_code == 200
    # Zero-streak user should not be passed to send_to_user
    # (the WHERE filter excludes them before reaching the send loop)
    assert send_mock.call_count == 0


async def test_streak_reminder_skips_disabled_users(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    await _make_user_with_sub(db_session, streak=5, push_enabled=False, last_active=yesterday)

    send_mock = AsyncMock(return_value=0)
    with patch("app.services.push_service.send_to_user", send_mock):
        r = await client.post(
            f"{PUSH}/streak-reminder",
            headers=_h({"X-Admin-Key": ADMIN_KEY}),
        )
    assert r.status_code == 200
    assert send_mock.call_count == 0


async def test_streak_reminder_skips_already_reminded_today(client, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CONTENT_ADMIN_KEY", ADMIN_KEY)
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    # Anchored to the same UTC midnight the endpoint uses (push.py: `today_start
    # = now.replace(hour=0, ...)`), not to "now minus a couple of hours".
    # Between 00:00 and 02:00 UTC that arithmetic lands on *yesterday*, the user
    # stops counting as already-reminded, a reminder goes out and the assertion
    # below flips — deterministically, for a two-hour window every single day.
    # CI caught it at 00:03 UTC.
    reminded_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    await _make_user_with_sub(db_session, streak=5, last_active=yesterday, last_reminded=reminded_today)

    send_mock = AsyncMock(return_value=0)
    with patch("app.services.push_service.send_to_user", send_mock):
        r = await client.post(
            f"{PUSH}/streak-reminder",
            headers=_h({"X-Admin-Key": ADMIN_KEY}),
        )
    assert r.status_code == 200
    assert send_mock.call_count == 0
