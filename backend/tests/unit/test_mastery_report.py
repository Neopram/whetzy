"""Informe de dominio con créditos (ECONOMIA §2.3): cobra 300 una vez por
intento, guarda una instantánea y la publica por un código sin sesión."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.content import Module, Skill, Track
from app.models.economy import CreditLedger, CreditReasonEnum
from app.models.user import User, UserSkillState
from app.services.economy import CreditsService


async def _setup(db: AsyncSession, credits: int) -> tuple[User, dict[str, str]]:
    uid = uuid.uuid4()
    u = User(id=uid, email=f"r{uid.hex[:8]}@example.com", username=f"ana{uid.hex[:6]}",
             hashed_password="x", display_name="Ana", language="es", max_streak=12)
    db.add(u)
    db.add(Track(id="trk_mr", name_es="Python", name_en="Python", order=1, icon="🐍", color="#000000"))
    db.add(Module(id="m_mr", track_id="trk_mr", name_es="M", name_en="M", order=1,
                  description_es="", description_en="", min_mastery_to_unlock=0.7))
    for i, p in enumerate((0.97, 0.5)):
        db.add(Skill(id=f"sk_mr{i}", module_id="m_mr", name_es=f"Bucles {i}", name_en=f"Loops {i}", order=i))
        db.add(UserSkillState(user_id=uid, skill_id=f"sk_mr{i}", p_known=p, attempts=5))
    await db.flush()
    if credits:
        await CreditsService.grant_credits(db, uid, credits, "promo_code", ref_id="seed")
    await db.commit()
    return u, {"Authorization": f"Bearer {create_access_token(uid)}"}


@pytest.mark.asyncio
async def test_buying_charges_300_once_per_request_and_snapshots(client: AsyncClient, db_session: AsyncSession):
    u, auth = await _setup(db_session, 700)
    rid = str(uuid.uuid4())
    r = await client.post("/api/v1/mastery-reports", json={"request_id": rid}, headers=auth)
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body["code"]) == 32
    snap = body["snapshot"]
    assert (snap["display_name"], snap["max_streak"]) == ("Ana", 12)
    [track] = snap["tracks"]
    assert (track["track_id"], track["skills_mastered"], track["total_skills"]) == ("trk_mr", 1, 2)
    assert [s["name_en"] for s in track["mastered_skills"]] == ["Loops 0"]
    assert "email" not in str(snap)
    assert await CreditsService.get_balance(db_session, u.id) == 400

    # Reintento con el mismo request_id: el mismo informe, sin otro cobro.
    again = await client.post("/api/v1/mastery-reports", json={"request_id": rid}, headers=auth)
    assert again.status_code == 201 and again.json()["code"] == body["code"]
    assert await CreditsService.get_balance(db_session, u.id) == 400
    spends = (await db_session.execute(
        select(CreditLedger).where(CreditLedger.user_id == u.id, CreditLedger.reason == CreditReasonEnum.SPEND_REPORT.value)
    )).scalars().all()
    assert sum(s.amount for s in spends) == -300

    mine = (await client.get("/api/v1/mastery-reports", headers=auth)).json()
    assert [x["code"] for x in mine["reports"]] == [body["code"]]


@pytest.mark.asyncio
async def test_public_page_needs_no_session_and_does_not_change(client: AsyncClient, db_session: AsyncSession):
    _, auth = await _setup(db_session, 300)
    code = (await client.post("/api/v1/mastery-reports", json={"request_id": str(uuid.uuid4())}, headers=auth)).json()["code"]

    # El dominio cambia después: el informe es una afirmación con fecha.
    state = (await db_session.execute(select(UserSkillState).where(UserSkillState.skill_id == "sk_mr1"))).scalar_one()
    state.p_known = 0.99
    await db_session.commit()

    client.cookies.clear()
    r = await client.get(f"/api/v1/mastery-reports/{code}")
    assert r.status_code == 200
    assert r.json()["snapshot"]["tracks"][0]["skills_mastered"] == 1
    assert (await client.get("/api/v1/mastery-reports/nope")).status_code == 404


@pytest.mark.asyncio
async def test_without_300_credits_nothing_is_charged(client: AsyncClient, db_session: AsyncSession):
    u, auth = await _setup(db_session, 299)
    uid = u.id  # el rollback del endpoint expira `u`
    r = await client.post("/api/v1/mastery-reports", json={"request_id": str(uuid.uuid4())}, headers=auth)
    assert (r.status_code, r.json()["detail"]) == (409, "insufficient_credits")
    assert await CreditsService.get_balance(db_session, uid) == 299
