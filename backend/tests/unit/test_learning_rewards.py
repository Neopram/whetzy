"""Créditos por aprender (ECONOMIA §2.2, services/learning_rewards).

Hasta el 2026-10-02 la Cartera los prometía (y antes de ADR-57, /economy/prices
los anunciaba) y nadie los abonaba. Aquí: qué paga, cuántas veces, el tope de
1.500 al mes y que los enganches (fin de quiz, vuelta horaria) existen.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.content import Module, Skill, Track
from app.models.economy import CreditLedger
from app.models.exam import MockExamAttempt
from app.models.session import StudySession
from app.models.user import User, UserSkillState
from app.services.economy import CreditsService
from app.services.learning_rewards import (
    LEARNING_MONTHLY_CAP,
    award_learning_credits,
)
from app.services.periodic import run_periodic_jobs

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)  # martes, semana ISO 43


def _user(**kw: object) -> User:
    uid = uuid.uuid4()
    fields: dict[str, object] = {
        "id": uid, "email": f"l{uid.hex[:10]}@example.com", "username": f"l{uid.hex[:10]}",
        "hashed_password": "x", "display_name": "Ana", "language": "es",
        # Experiencia 1: el diagnóstico exige una prueba de nivel terminada, así
        # que no cuela en los tests que no van de eso.
        "onboarding_experience": 1,
    }
    fields.update(kw)
    return User(**fields)


async def _track(db: AsyncSession, modules: int, skills_per_module: int = 2) -> list[list[str]]:
    db.add(Track(id="trk_lr", name_es="T", name_en="T", order=1, icon="t", color="#000000"))
    out: list[list[str]] = []
    for m in range(modules):
        db.add(Module(id=f"m_lr{m}", track_id="trk_lr", name_es="M", name_en="M", order=m,
                      description_es="", description_en="", min_mastery_to_unlock=0.7))
        ids = [f"sk_lr{m}_{i}" for i in range(skills_per_module)]
        for i, sid in enumerate(ids):
            db.add(Skill(id=sid, module_id=f"m_lr{m}", name_es=sid, name_en=sid, order=i))
        out.append(ids)
    await db.flush()
    return out


async def _master(db: AsyncSession, user: User, skills: list[str], p: float = 0.9) -> None:
    for sid in skills:
        db.add(UserSkillState(user_id=user.id, skill_id=sid, p_known=p, attempts=5))
    await db.flush()


async def _reasons(db: AsyncSession, user: User) -> list[tuple[str, int]]:
    rows = await db.execute(
        select(CreditLedger.reason, CreditLedger.amount)
        .where(CreditLedger.user_id == user.id)
        .order_by(CreditLedger.reason, CreditLedger.ref_id)
    )
    return [(r, a) for r, a in rows.all()]


@pytest.mark.asyncio
async def test_diagnostic_pays_50_once(db_session: AsyncSession):
    """El principiante (experiencia 0) no ve la prueba de nivel: su diagnóstico
    es el onboarding, la misma regla que la activación de referidos (§3.1)."""
    u = _user(onboarding_experience=0)
    db_session.add(u)
    await db_session.flush()
    assert await award_learning_credits(db_session, u, NOW) == 50
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=40)) == 0
    assert await CreditsService.get_balance(db_session, u.id) == 50


@pytest.mark.asyncio
async def test_module_pays_100_only_when_every_skill_reaches_08(db_session: AsyncSession):
    [skills] = await _track(db_session, 1)
    u = _user()
    db_session.add(u)
    await db_session.flush()
    # Media 0,825 ≥ 0,7: la app lo pinta como superado, pero una skill va por
    # debajo de 0,8 y la regla del §2.2 es «todas sus skills».
    db_session.add(UserSkillState(user_id=u.id, skill_id=skills[0], p_known=0.9, attempts=5))
    db_session.add(UserSkillState(user_id=u.id, skill_id=skills[1], p_known=0.75, attempts=5))
    await db_session.flush()
    assert await award_learning_credits(db_session, u, NOW) == 0

    state = (await db_session.execute(
        select(UserSkillState).where(UserSkillState.user_id == u.id, UserSkillState.skill_id == skills[1])
    )).scalar_one()
    state.p_known = 0.8
    await db_session.flush()
    assert await award_learning_credits(db_session, u, NOW) == 100
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=3)) == 0


@pytest.mark.asyncio
async def test_streaks_pay_per_week_and_per_month(db_session: AsyncSession):
    u = _user(current_streak=30)
    db_session.add(u)
    await db_session.flush()
    assert await award_learning_credits(db_session, u, NOW) == 70 + 300
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=2)) == 0  # misma semana
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=7)) == 70  # semana 44
    u.current_streak = 6
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=14)) == 0


@pytest.mark.asyncio
async def test_monthly_cap_holds_and_what_did_not_fit_waits(db_session: AsyncSession):
    modules = await _track(db_session, 17, skills_per_module=1)
    u = _user()
    db_session.add(u)
    await db_session.flush()
    await _master(db_session, u, [s for ids in modules for s in ids])

    assert await award_learning_credits(db_session, u, NOW) == LEARNING_MONTHLY_CAP == 1500
    assert await award_learning_credits(db_session, u, NOW + timedelta(days=5)) == 0
    # Mes siguiente: los dos módulos que no cupieron se pagan entonces.
    assert await award_learning_credits(db_session, u, datetime(2026, 11, 2, tzinfo=UTC)) == 200


@pytest.mark.asyncio
async def test_skills_skipped_by_a_passed_test_out_pay_50_each(db_session: AsyncSession):
    [skills] = await _track(db_session, 1, skills_per_module=3)
    u = _user()
    db_session.add(u)
    await db_session.flush()
    await _master(db_session, u, skills[:2])
    await _master(db_session, u, skills[2:], p=0.5)

    def attempt(passed: bool, status: str = "submitted") -> MockExamAttempt:
        return MockExamAttempt(
            id=uuid.uuid4(), user_id=u.id, track_id="trk_lr", module_id="m_lr0", kind="test_out",
            question_ids=[], duration_minutes=15, expires_at=NOW, status=status,
            report={"passed": passed},
        )

    db_session.add(attempt(False))
    db_session.add(attempt(True, status="expired"))  # fuera de tiempo no cuenta
    await db_session.flush()
    assert await award_learning_credits(db_session, u, NOW) == 0

    db_session.add(attempt(True))
    await db_session.flush()
    # Dos skills con dominio confirmado; la tercera (0,5) no se ha «saltado».
    assert await award_learning_credits(db_session, u, NOW) == 100
    assert ("skill_skipped", 50) in await _reasons(db_session, u)


@pytest.mark.asyncio
async def test_quiz_end_pays_and_says_how_much(client: AsyncClient, db_session: AsyncSession):
    u = _user(current_streak=7)
    db_session.add(u)
    await db_session.flush()
    session = StudySession(id=uuid.uuid4(), user_id=u.id, mode="study")
    db_session.add(session)
    await db_session.commit()

    r = await client.post(
        "/api/v1/quiz/end", json={"session_id": str(session.id)},
        headers={"Authorization": f"Bearer {create_access_token(u.id)}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["credits_earned"] == 70
    assert await CreditsService.get_balance(db_session, u.id) == 70


@pytest.mark.asyncio
async def test_hourly_loop_pays_recently_active_learners(db_session: AsyncSession):
    active = _user(current_streak=7, last_active=datetime.now(UTC) - timedelta(hours=2))
    idle = _user(current_streak=7, last_active=datetime.now(UTC) - timedelta(days=5))
    db_session.add_all([active, idle])
    await db_session.commit()
    results = await run_periodic_jobs(db_session)
    assert results["learning_credits"] == 70
    assert await CreditsService.get_balance(db_session, active.id) == 70
    assert await CreditsService.get_balance(db_session, idle.id) == 0
