"""Borrado de cuenta con 30 días de gracia (19.12).

Lo que se fija aquí es lo que prometen los textos legales vigentes y la pantalla
`/delete-account`: desactivar al momento, recuperar si se vuelve a entrar antes de
30 días, y a los 30 días borrar los datos de la cuenta de forma permanente.
"""

from __future__ import annotations

import itertools
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.cookies import OAUTH_STATE_COOKIE
from app.models.admin import GDPRRequest
from app.models.analytics import AnalyticsEvent
from app.models.auth import LoginAttempt, RefreshToken
from app.models.lesson_completion import LessonCompletion
from app.models.push_subscription import PushSubscription
from app.models.user import User, UserSkillState
from app.services import account_deletion

AUTH = "/api/v1/auth"
_ips = itertools.count(1)


def _h(extra: dict | None = None) -> dict:
    headers = {"X-Forwarded-For": f"198.51.100.{next(_ips) % 255 or 255}"}
    if extra:
        headers.update(extra)
    return headers


async def _pending(db, user_id) -> list[GDPRRequest]:
    rows = await db.execute(
        select(GDPRRequest).where(
            GDPRRequest.user_id == user_id, GDPRRequest.request_type == "deletion"
        )
    )
    return list(rows.scalars())


async def _age_request(db, user_id, days: int) -> None:
    """Simula que la solicitud se hizo hace `days` días."""
    for req in await _pending(db, user_id):
        req.created_at = datetime.now(UTC) - timedelta(days=days)
    await db.commit()


# ── Pedir el borrado ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_deletion_deactivates_and_opens_one_request(db_session, user) -> None:
    db_session.add(RefreshToken(
        user_id=user.id, token_hash="h" * 64, family_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    ))
    await db_session.commit()
    version = user.jwt_version

    purge_at = await account_deletion.request_deletion(db_session, user)
    await account_deletion.request_deletion(db_session, user)  # repetir no duplica

    await db_session.refresh(user)
    assert user.is_active is False
    assert user.jwt_version > version
    reqs = await _pending(db_session, user.id)
    assert [r.status for r in reqs] == ["pending"]
    assert purge_at > datetime.now(UTC) + timedelta(days=29)
    tokens = (await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))).scalars()
    assert all(t.revoked for t in tokens)


@pytest.mark.asyncio
async def test_delete_endpoint_kills_the_open_session(client, auth_headers) -> None:
    r = await client.delete(f"{AUTH}/me/account", headers=_h(auth_headers))
    assert r.status_code == 200, r.text
    assert "purge_after" in r.json()
    me = await client.get(f"{AUTH}/me", headers=_h(auth_headers))
    assert me.status_code in (401, 403)


# ── Recuperar dentro de la gracia ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_within_grace_restores_the_account(client, db_session, user) -> None:
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=10)

    r = await client.post(
        f"{AUTH}/login", data={"username": user.email, "password": "Passw0rd!"}, headers=_h()
    )
    assert r.status_code == 200, r.text
    await db_session.refresh(user)
    assert user.is_active is True
    assert [q.status for q in await _pending(db_session, user.id)] == ["cancelled"]


@pytest.mark.asyncio
async def test_login_after_grace_does_not_restore(client, db_session, user) -> None:
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=31)

    r = await client.post(
        f"{AUTH}/login", data={"username": user.email, "password": "Passw0rd!"}, headers=_h()
    )
    assert r.status_code == 403
    await db_session.refresh(user)
    assert user.is_active is False


@pytest.mark.asyncio
async def test_a_suspended_account_is_not_restored_by_login(client, db_session, user) -> None:
    """Desactivada sin solicitud de borrado = suspensión: el login no la reactiva."""
    user.is_active = False
    await db_session.commit()
    r = await client.post(
        f"{AUTH}/login", data={"username": user.email, "password": "Passw0rd!"}, headers=_h()
    )
    assert r.status_code == 403


# ── Purgar a los 30 días ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_nothing_is_purged_before_30_days(db_session, user) -> None:
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=29)
    assert await account_deletion.purge_due(db_session) == 0
    await db_session.refresh(user)
    assert user.email.endswith("@whetzy.test")


@pytest.mark.asyncio
async def test_purge_erases_personal_data_and_keeps_nothing_identifying(db_session, user) -> None:
    original_email = user.email
    user.is_premium = True
    user.subscription_status = "active"
    user.subscription_tier = "pro"
    user.subscription_provider = "revenuecat"
    user.subscription_expires_at = datetime.now(UTC) + timedelta(days=20)
    user.eu_withdrawal_waiver_at = datetime.now(UTC)
    db_session.add_all([
        UserSkillState(user_id=user.id, skill_id="sk1", attempts=3),
        LessonCompletion(user_id=user.id, skill_id="sk1"),
        PushSubscription(user_id=user.id, endpoint="https://push.example/x", p256dh="k", auth="a"),
        AnalyticsEvent(user_id=user.id, event_type="quiz_answered", properties={}),
        LoginAttempt(email=original_email, ip="203.0.113.9", success=True),
    ])
    await db_session.commit()
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=31)

    assert await account_deletion.purge_due(db_session) == 1

    await db_session.refresh(user)
    assert user.email.endswith("@deleted.invalid") and original_email not in user.email
    assert user.username.startswith("deleted_")
    assert user.display_name == "—"
    assert user.hashed_password is None
    assert user.is_active is False
    assert user.is_premium is False
    assert (user.subscription_status, user.subscription_tier, user.subscription_provider) == (None, None, None)
    assert user.subscription_expires_at is None and user.eu_withdrawal_waiver_at is None

    async def count(model, *where) -> int:
        return (await db_session.execute(select(func.count()).select_from(model).where(*where))).scalar_one()

    assert await count(UserSkillState, UserSkillState.user_id == user.id) == 0
    assert await count(LessonCompletion, LessonCompletion.user_id == user.id) == 0
    assert await count(PushSubscription, PushSubscription.user_id == user.id) == 0
    assert await count(AnalyticsEvent, AnalyticsEvent.user_id == user.id) == 0
    assert await count(AnalyticsEvent) == 1  # el evento queda, sin persona
    assert await count(LoginAttempt, LoginAttempt.email == original_email) == 0
    assert [q.status for q in await _pending(db_session, user.id)] == ["completed"]


@pytest.mark.asyncio
async def test_purge_is_idempotent(db_session, user) -> None:
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=31)
    assert await account_deletion.purge_due(db_session) == 1
    assert await account_deletion.purge_due(db_session) == 0


@pytest.mark.asyncio
async def test_a_cancelled_request_is_never_purged(db_session, user) -> None:
    await account_deletion.request_deletion(db_session, user)
    assert await account_deletion.restore_if_pending(db_session, user) is True
    await _age_request(db_session, user.id, days=40)
    assert await account_deletion.purge_due(db_session) == 0
    await db_session.refresh(user)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_purging_one_user_leaves_others_alone(db_session, user) -> None:
    other = User(
        email="other@whetzy.test", username="otheruser1", display_name="Other",
        hashed_password=None, language="es",
    )
    db_session.add(other)
    await db_session.commit()
    db_session.add(UserSkillState(user_id=other.id, skill_id="sk1", attempts=1))
    await db_session.commit()
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=31)

    await account_deletion.purge_due(db_session)

    await db_session.refresh(other)
    assert other.email == "other@whetzy.test"
    left = await db_session.execute(select(UserSkillState).where(UserSkillState.user_id == other.id))
    assert len(list(left.scalars())) == 1


# ── Cancelar desde el panel ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_owner_cancel_reactivates_the_account(client, db_session, user, owner) -> None:
    await account_deletion.request_deletion(db_session, user)
    r = await client.post(
        f"/api/v1/admin/gdpr/deletions/{user.id}/cancel",
        headers=_h({"Authorization": f"Bearer {owner.token}"}),
    )
    assert r.status_code == 200, r.text
    await db_session.refresh(user)
    assert user.is_active is True


# ── La misma regla por OAuth ──────────────────────────────────────────────────

OAUTH = "/api/v1/auth/oauth"


async def _oauth_login(client):
    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    state = dict(p.split("=") for p in start.headers["location"].split("?")[1].split("&"))["state"]
    # 41.14: la cookie del state es Secure y el cliente de test habla http,
    # así que no se reenvía sola -- se manda a mano.
    return await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "test-code", "state": state},
        headers={**_h(), "Cookie": f"{OAUTH_STATE_COOKIE}={state}"},
        follow_redirects=False,
    )


async def _oauth_user(db_session) -> User:
    row = await db_session.execute(select(User).where(User.email == "oauth-test-code@example.com"))
    return row.scalar_one()


@pytest.mark.asyncio
async def test_oauth_login_within_grace_restores(client, db_session) -> None:
    assert (await _oauth_login(client)).status_code == 302
    u = await _oauth_user(db_session)
    await account_deletion.request_deletion(db_session, u)
    await _age_request(db_session, u.id, days=5)

    r = await _oauth_login(client)
    assert r.status_code == 302 and "oauth_error" not in r.headers["location"]
    await db_session.refresh(u)
    assert u.is_active is True


@pytest.mark.asyncio
async def test_oauth_login_after_grace_is_refused(client, db_session) -> None:
    assert (await _oauth_login(client)).status_code == 302
    u = await _oauth_user(db_session)
    await account_deletion.request_deletion(db_session, u)
    await _age_request(db_session, u.id, days=31)

    r = await _oauth_login(client)
    assert "oauth_error=account_inactive" in r.headers["location"]
    # 41.14 añadió un Set-Cookie legítimo aquí (borra la cookie del state,
    # ya consumido): lo que de verdad importa es que ninguna cookie de
    # sesión se cuela en un login refusado.
    cookies_set = {c.split("=", 1)[0] for c in r.headers.get_list("set-cookie")}
    assert cookies_set.isdisjoint({"whetzy_access", "whetzy_refresh", "whetzy_logged_in"})


def test_every_table_pointing_at_users_is_classified() -> None:
    """Una tabla nueva con clave a `users` que nadie clasifica se queda con los
    datos de una cuenta borrada: el 2026-10-11 eran mastery_reports,
    user_blocks, user_reports e instructors."""
    import app.models  # noqa: F401
    from app.core.db import Base

    classified = (
        set(account_deletion._OWNED_TABLES)
        | set(account_deletion._DETACHED_TABLES)
        | set(account_deletion._KEPT_TABLES)
        | account_deletion._HANDLED_IN_PURGE
    )
    pointing = {
        t.name
        for t in Base.metadata.sorted_tables
        if t.name != "users"
        and any(f.column.table.name == "users" for c in t.columns for f in c.foreign_keys)
    }
    assert pointing - classified == set(), sorted(pointing - classified)


@pytest.mark.asyncio
async def test_purge_removes_reports_blocks_and_instructor_profile(db_session, user) -> None:
    from app.models.economy import MasteryReport
    from app.models.instructor import Instructor
    from app.models.moderation import UserBlock, UserReport

    other = User(
        id=uuid.uuid4(), email=f"other-{uuid.uuid4().hex[:6]}@whetzy.test",
        username=f"other{uuid.uuid4().hex[:6]}", hashed_password="x", language="es", display_name="Otro",
    )
    db_session.add(other)
    await db_session.flush()
    db_session.add_all([
        MasteryReport(user_id=user.id, code="mr-del-1", request_id="req-del-1", snapshot={}),
        UserBlock(blocker_id=user.id, blocked_id=other.id),
        UserBlock(blocker_id=other.id, blocked_id=user.id),
        UserReport(reporter_id=user.id, reported_id=other.id, reason="spam", context="duel"),
        UserReport(reporter_id=other.id, reported_id=user.id, reason="spam", context="duel"),
        Instructor(user_id=user.id, display_name="Ana Real", bio="Mi bio", website="https://ana.example"),
    ])
    await db_session.commit()
    await account_deletion.request_deletion(db_session, user)
    await _age_request(db_session, user.id, days=31)
    assert await account_deletion.purge_due(db_session) == 1

    async def count(model, *where) -> int:
        return (await db_session.execute(select(func.count()).select_from(model).where(*where))).scalar_one()

    assert await count(MasteryReport, MasteryReport.user_id == user.id) == 0
    assert await count(UserBlock) == 0
    assert await count(UserReport, UserReport.reporter_id == user.id) == 0
    assert await count(UserReport, UserReport.reported_id == user.id) == 1
    inst = (await db_session.execute(select(Instructor).where(Instructor.user_id == user.id))).scalar_one()
    assert (inst.display_name, inst.bio, inst.website) == ("—", None, None)
