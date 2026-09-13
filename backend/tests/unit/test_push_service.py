"""Tests for Web Push delivery.

The failure that matters here is quiet: one dead browser endpoint must not
stop the other devices from being notified, and a 410 Gone must actually
prune the subscription — otherwise the table grows forever with endpoints
that can never be delivered to, and every send re-tries them.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from sqlalchemy import func, select

from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.services import push_service
from app.services.push_service import is_configured, send_to_user


class _Response:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _PushError(Exception):
    def __init__(self, status_code: int | None) -> None:
        super().__init__(f"push failed {status_code}")
        self.response = _Response(status_code) if status_code is not None else None


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv", raising=False)
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub", raising=False)
    monkeypatch.setattr(settings, "VAPID_EMAIL", "mailto:a@b.test", raising=False)


async def add_sub(db, user_id: uuid.UUID, endpoint: str) -> PushSubscription:
    sub = PushSubscription(
        user_id=user_id, endpoint=endpoint, p256dh=f"p_{endpoint}", auth=f"a_{endpoint}"
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


class TestIsConfigured:
    def test_true_with_both_keys(self, configured: None) -> None:
        assert is_configured() is True

    def test_false_without_private_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "", raising=False)
        monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub", raising=False)
        assert is_configured() is False

    def test_false_without_public_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv", raising=False)
        monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "", raising=False)
        assert is_configured() is False


class TestSendToUser:
    @pytest.mark.asyncio
    async def test_unconfigured_is_a_noop(
        self, db_session, user: User, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "", raising=False)
        called: list[Any] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: called.append(kw))
        await add_sub(db_session, user.id, "https://push.test/1")

        assert await send_to_user(db_session, user.id, "T", "B") == 0
        assert called == []

    @pytest.mark.asyncio
    async def test_no_subscriptions_returns_zero(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        called: list[Any] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: called.append(kw))
        assert await send_to_user(db_session, user.id, "T", "B") == 0
        assert called == []

    @pytest.mark.asyncio
    async def test_sends_to_every_subscription(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: calls.append(kw))
        for i in range(3):
            await add_sub(db_session, user.id, f"https://push.test/{i}")

        assert await send_to_user(db_session, user.id, "T", "B") == 3
        assert len(calls) == 3
        endpoints = {c["subscription_info"]["endpoint"] for c in calls}
        assert endpoints == {f"https://push.test/{i}" for i in range(3)}

    @pytest.mark.asyncio
    async def test_payload_shape(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: calls.append(kw))
        await add_sub(db_session, user.id, "https://push.test/1")

        await send_to_user(db_session, user.id, "Título", "Cuerpo", {"url": "/quiz"}, tag="streak")

        payload = json.loads(calls[0]["data"])
        assert payload["title"] == "Título"
        assert payload["body"] == "Cuerpo"
        assert payload["tag"] == "streak"
        assert payload["url"] == "/quiz"

    @pytest.mark.asyncio
    async def test_default_tag(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: calls.append(kw))
        await add_sub(db_session, user.id, "https://push.test/1")
        await send_to_user(db_session, user.id, "T", "B")
        assert json.loads(calls[0]["data"])["tag"] == "whetzy"

    @pytest.mark.asyncio
    async def test_vapid_credentials_are_passed(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: calls.append(kw))
        await add_sub(db_session, user.id, "https://push.test/1")
        await send_to_user(db_session, user.id, "T", "B")

        assert calls[0]["vapid_private_key"] == "priv"
        assert calls[0]["vapid_claims"] == {"sub": "mailto:a@b.test"}
        keys = calls[0]["subscription_info"]["keys"]
        assert keys == {"p256dh": "p_https://push.test/1", "auth": "a_https://push.test/1"}

    @pytest.mark.asyncio
    async def test_one_dead_endpoint_does_not_stop_the_others(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def flaky(**kw: Any) -> None:
            if kw["subscription_info"]["endpoint"].endswith("/1"):
                raise _PushError(500)

        monkeypatch.setattr(push_service, "webpush", flaky)
        for i in range(3):
            await add_sub(db_session, user.id, f"https://push.test/{i}")

        assert await send_to_user(db_session, user.id, "T", "B") == 2

    @pytest.mark.asyncio
    async def test_410_prunes_the_subscription(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            push_service, "webpush", lambda **kw: (_ for _ in ()).throw(_PushError(410))
        )
        await add_sub(db_session, user.id, "https://push.test/gone")

        assert await send_to_user(db_session, user.id, "T", "B") == 0
        remaining = await db_session.scalar(select(func.count(PushSubscription.id)))
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_non_410_failure_keeps_the_subscription(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A transient 500 is not a reason to forget the device."""
        monkeypatch.setattr(
            push_service, "webpush", lambda **kw: (_ for _ in ()).throw(_PushError(500))
        )
        await add_sub(db_session, user.id, "https://push.test/flaky")

        assert await send_to_user(db_session, user.id, "T", "B") == 0
        remaining = await db_session.scalar(select(func.count(PushSubscription.id)))
        assert remaining == 1

    @pytest.mark.asyncio
    async def test_error_without_a_response_is_survivable(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A connection error has no `.response`; the getattr chain must cope."""
        monkeypatch.setattr(
            push_service, "webpush", lambda **kw: (_ for _ in ()).throw(_PushError(None))
        )
        await add_sub(db_session, user.id, "https://push.test/x")

        assert await send_to_user(db_session, user.id, "T", "B") == 0
        assert await db_session.scalar(select(func.count(PushSubscription.id))) == 1

    @pytest.mark.asyncio
    async def test_only_410_subscriptions_are_pruned(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def mixed(**kw: Any) -> None:
            ep = kw["subscription_info"]["endpoint"]
            if ep.endswith("gone"):
                raise _PushError(410)
            if ep.endswith("flaky"):
                raise _PushError(500)

        monkeypatch.setattr(push_service, "webpush", mixed)
        await add_sub(db_session, user.id, "https://push.test/gone")
        await add_sub(db_session, user.id, "https://push.test/flaky")
        await add_sub(db_session, user.id, "https://push.test/ok")

        assert await send_to_user(db_session, user.id, "T", "B") == 1
        left = (await db_session.scalars(select(PushSubscription.endpoint))).all()
        assert set(left) == {"https://push.test/flaky", "https://push.test/ok"}

    @pytest.mark.asyncio
    async def test_another_users_subscriptions_are_untouched(
        self, db_session, user: User, configured: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []
        monkeypatch.setattr(push_service, "webpush", lambda **kw: calls.append(kw))
        stranger = uuid.uuid4()
        await add_sub(db_session, user.id, "https://push.test/mine")
        await add_sub(db_session, stranger, "https://push.test/theirs")

        assert await send_to_user(db_session, user.id, "T", "B") == 1
        assert calls[0]["subscription_info"]["endpoint"] == "https://push.test/mine"
