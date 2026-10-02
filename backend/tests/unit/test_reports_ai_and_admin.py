"""Reportes de alumnos: el motivo `ai_explanation` (transparencia del tutor IA,
AI Act art. 50) y la cola de admin que hasta el 2026-10-02 solo existía como
recuento (`/admin/metrics/reports`), sin el texto de cada reporte."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _user(db: AsyncSession, role: str = "user") -> User:
    uid = uuid.uuid4()
    u = User(id=uid, email=f"r{uid.hex[:8]}@example.com", username=f"r{uid.hex[:8]}",
             hashed_password="x", display_name="R", language="es", role=role)
    db.add(u)
    await db.commit()
    return u


@pytest.mark.asyncio
async def test_ai_explanation_report_keeps_what_the_learner_saw(
    client: AsyncClient, db_session: AsyncSession, content_seed: dict
):
    learner, admin = await _user(db_session), await _user(db_session, "admin")
    r = await client.post(
        "/api/v1/reports/question",
        json={"question_id": content_seed["question_id"], "reason": "ai_explanation",
              "notes": "El tutor dijo que 42 es un float."},
        headers=_headers(learner),
    )
    assert r.status_code == 201, r.text

    queue = await client.get("/api/v1/admin/reports/recent", headers=_headers(admin))
    assert queue.status_code == 200
    [item] = queue.json()["reports"]
    assert (item["reason"], item["notes"]) == ("ai_explanation", "El tutor dijo que 42 es un float.")
    only_ai = await client.get("/api/v1/admin/reports/recent?reason=ai_explanation", headers=_headers(admin))
    assert len(only_ai.json()["reports"]) == 1
    none = await client.get("/api/v1/admin/reports/recent?reason=typo", headers=_headers(admin))
    assert none.json()["reports"] == []


@pytest.mark.asyncio
async def test_report_notes_have_a_limit(client: AsyncClient, db_session: AsyncSession, content_seed: dict):
    learner = await _user(db_session)
    r = await client.post(
        "/api/v1/reports/question",
        json={"question_id": content_seed["question_id"], "reason": "other", "notes": "x" * 4001},
        headers=_headers(learner),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_the_report_queue_is_admin_only(client: AsyncClient, db_session: AsyncSession):
    learner = await _user(db_session)
    r = await client.get("/api/v1/admin/reports/recent", headers=_headers(learner))
    assert r.status_code == 403
