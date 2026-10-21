"""Tutor por modos (ola 2, 2026-10-21; decisión del dueño: «A fondo» solo Pro Max).

- `why` (por defecto) y `how` para Pro y Pro Max; `deep` solo Pro Max (403
  `deep_requires_pro_max` y sin gastar cupo para Pro).
- Cada modo cambia el prompt y el presupuesto de tokens, no el cupo.
- `/auth/me` dice si el usuario tiene `tutor_deep_access`, para que la
  interfaz no ofrezca lo que el servidor va a negar.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.tutor_usage import TutorUsage
from app.models.user import User
from app.services.ai import tutor as tutor_service

URL = "/api/v1/tutor/explain"


async def _user(db: AsyncSession, tier: str) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"m-{uuid.uuid4().hex[:8]}@example.com",
        username=f"m{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Modos",
        language="es",
        is_premium=True,
        subscription_status="active",
        subscription_tier=tier,
    )
    db.add(u)
    await db.commit()
    return u


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}"}


class _Spy:
    """Proveedor que apunta lo que recibe."""

    name = "spy"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def complete(self, system: str, user: str, max_tokens: int = 500, history: Any = None) -> str:
        self.calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        return "ok"


async def test_pro_pide_a_fondo_403_y_no_gasta_cupo(client, db_session, content_seed) -> None:
    pro = await _user(db_session, "plus")
    r = await client.post(URL, json={"question_id": content_seed["question_id"], "mode": "deep"}, headers=_h(pro))
    assert r.status_code == 403
    assert r.json()["detail"] == "deep_requires_pro_max"
    used = (await db_session.execute(select(TutorUsage).where(TutorUsage.user_id == pro.id))).scalars().all()
    assert all(u.explanations == 0 for u in used)


async def test_modo_desconocido_422(client, db_session, content_seed) -> None:
    pro = await _user(db_session, "plus")
    r = await client.post(URL, json={"question_id": content_seed["question_id"], "mode": "essay"}, headers=_h(pro))
    assert r.status_code == 422


async def test_cada_modo_cambia_prompt_y_presupuesto(client, db_session, content_seed, monkeypatch) -> None:
    spy = _Spy()
    monkeypatch.setattr(tutor_service, "get_provider", lambda: spy)
    promax = await _user(db_session, "pro")
    for mode in ("why", "how", "deep"):
        r = await client.post(URL, json={"question_id": content_seed["question_id"], "mode": mode}, headers=_h(promax))
        assert r.status_code == 200, r.text
        assert r.json()["mode"] == mode
    why, how, deep = spy.calls
    assert "5 frases" in why["system"]
    assert "pasos" in how["system"]
    assert "fuentes" in deep["system"].lower()
    assert why["max_tokens"] == how["max_tokens"] == 500
    assert deep["max_tokens"] > 500


async def test_sin_modo_es_por_que(client, db_session, content_seed) -> None:
    pro = await _user(db_session, "plus")
    r = await client.post(URL, json={"question_id": content_seed["question_id"]}, headers=_h(pro))
    assert r.status_code == 200
    assert r.json()["mode"] == "why"


async def test_me_dice_si_hay_a_fondo(client, db_session) -> None:
    pro, promax = await _user(db_session, "plus"), await _user(db_session, "pro")
    assert (await client.get("/api/v1/auth/me", headers=_h(pro))).json()["tutor_deep_access"] is False
    assert (await client.get("/api/v1/auth/me", headers=_h(promax))).json()["tutor_deep_access"] is True
