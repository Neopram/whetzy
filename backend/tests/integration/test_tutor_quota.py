"""Cupo diario del tutor: Pro con límite, Pro Max ilimitado (38.6, ADR-49).

Ruta: POST /api/v1/tutor/explain. El proveedor es NullProvider (conftest), así
que cada llamada es local y rápida.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.tutor import TUTOR_UNAVAILABLE
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.tutor_usage import TutorUsage
from app.models.user import User
from app.services import tutor_quota

URL = "/api/v1/tutor/explain"
DAY = date(2026, 9, 25)


async def _user(db: AsyncSession, **kw: object) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"q-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"q{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Quota",
        language="es",
        **kw,
    )
    db.add(u)
    await db.commit()
    return u


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}"}


@pytest_asyncio.fixture
async def fixed_day(monkeypatch):
    state = {"day": DAY}
    monkeypatch.setattr(tutor_quota, "today_utc", lambda now=None: state["day"])
    return state


async def _ask(client: AsyncClient, headers: dict, qid: str) -> int:
    return (
        await client.post(URL, json={"question_id": qid}, headers=headers)
    ).status_code


async def test_pro_se_corta_al_pasar_el_cupo(
    client, db_session, content_seed, fixed_day
) -> None:
    pro = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    limit = settings.TUTOR_DAILY_LIMIT_PLUS
    assert limit == 20
    for _ in range(limit):
        assert await _ask(client, _h(pro), content_seed["question_id"]) == 200
    res = await client.post(
        URL, json={"question_id": content_seed["question_id"]}, headers=_h(pro)
    )
    assert res.status_code == 429
    assert res.json()["detail"] == tutor_quota.LIMIT_REACHED
    assert res.headers["X-Tutor-Daily-Limit"] == str(limit)
    assert res.headers["X-Tutor-Resets-At"] == "2026-09-26T00:00:00+00:00"


async def test_pro_max_no_tiene_cupo(
    client, db_session, content_seed, fixed_day
) -> None:
    pro_max = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="pro",
    )
    for _ in range(settings.TUTOR_DAILY_LIMIT_PLUS + 5):
        assert await _ask(client, _h(pro_max), content_seed["question_id"]) == 200
    # Se cuenta igual: es la cifra para medir el coste del tutor ilimitado.
    row = await db_session.get(TutorUsage, (pro_max.id, DAY))
    assert row is not None and row.explanations == settings.TUTOR_DAILY_LIMIT_PLUS + 5


async def test_creador_dueno_y_admin_sin_cupo(db_session) -> None:
    assert (
        tutor_quota.daily_limit(await _user(db_session, subscription_tier="creator"))
        is None
    )
    assert tutor_quota.daily_limit(await _user(db_session, role="owner")) is None
    assert tutor_quota.daily_limit(await _user(db_session, is_admin=True)) is None
    assert (
        tutor_quota.daily_limit(await _user(db_session, subscription_tier="plus")) == 20
    )


async def test_el_contador_vuelve_a_cero_al_cambiar_el_dia(
    client, db_session, content_seed, fixed_day, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "TUTOR_DAILY_LIMIT_PLUS", 2)
    pro = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    qid = content_seed["question_id"]
    assert [await _ask(client, _h(pro), qid) for _ in range(3)] == [200, 200, 429]
    fixed_day["day"] = date(2026, 9, 26)
    assert await _ask(client, _h(pro), qid) == 200


async def test_el_cupo_de_otro_usuario_no_cuenta(
    client, db_session, content_seed, fixed_day, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "TUTOR_DAILY_LIMIT_PLUS", 1)
    a = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    b = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    qid = content_seed["question_id"]
    assert await _ask(client, _h(a), qid) == 200
    assert await _ask(client, _h(a), qid) == 429
    assert await _ask(client, _h(b), qid) == 200


async def test_gratis_sigue_sin_tutor(client, auth_headers, content_seed) -> None:
    assert await _ask(client, auth_headers, content_seed["question_id"]) == 403


class _RejectedKey:
    """Groq answering 401: what production served on 2026-10-01 (clave no válida)."""

    name = "groq"

    async def complete_named(
        self, system: str, user: str, **_: object
    ) -> tuple[str, str]:
        import httpx

        req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        raise httpx.HTTPStatusError(
            "401", request=req, response=httpx.Response(401, request=req)
        )


async def test_proveedor_rechazado_da_503_y_no_gasta_cupo(
    client, db_session, content_seed, fixed_day, monkeypatch
) -> None:
    from app.services.ai import tutor as tutor_service

    monkeypatch.setattr(tutor_service, "get_provider", lambda: _RejectedKey())
    pro = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="plus",
    )
    res = await client.post(
        URL, json={"question_id": content_seed["question_id"]}, headers=_h(pro)
    )
    assert res.status_code == 503
    assert res.json()["detail"] == TUTOR_UNAVAILABLE
    assert await tutor_quota.used_on(db_session, pro.id, DAY) == 0
