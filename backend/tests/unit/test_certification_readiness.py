"""Unit tests for GET /exams/certification/{track_id}/readiness (18.1)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Domain, Module, Skill, Track
from app.models.user import User, UserSkillState

pytestmark = pytest.mark.asyncio

CERT_TRACK_ID = "test-cert"
DOMAIN_A_ID = "domtestcerta01"
DOMAIN_B_ID = "domtestcerta02"


async def _seed_cert_track(db: AsyncSession) -> tuple[str, str, str, str]:
    """Creates a minimal cert track with 2 domains × 1 skill each."""
    track = Track(
        id=CERT_TRACK_ID,
        name_es="Test Cert",
        name_en="Test Cert",
        order=99,
        icon="🧪",
        color="#000000",
        is_certification=True,
        cert_provider="Test",
        exam_question_count=10,
        exam_duration_minutes=30,
    )
    mod_a = Module(id="modtestcerta01", track_id=CERT_TRACK_ID, name_es="A", name_en="A", order=1)
    mod_b = Module(id="modtestcerta02", track_id=CERT_TRACK_ID, name_es="B", name_en="B", order=2)
    dom_a = Domain(
        id=DOMAIN_A_ID,
        track_id=CERT_TRACK_ID,
        name_es="Dominio A",
        name_en="Domain A",
        weight_pct=60.0,
        order=1,
    )
    dom_b = Domain(
        id=DOMAIN_B_ID,
        track_id=CERT_TRACK_ID,
        name_es="Dominio B",
        name_en="Domain B",
        weight_pct=40.0,
        order=2,
    )
    sk_a = Skill(
        id="sktestcerta0101",
        module_id="modtestcerta01",
        name_es="Habilidad A",
        name_en="Skill A",
        order=1,
        domain_id=DOMAIN_A_ID,
    )
    sk_b = Skill(
        id="sktestcerta0201",
        module_id="modtestcerta02",
        name_es="Habilidad B",
        name_en="Skill B",
        order=1,
        domain_id=DOMAIN_B_ID,
    )
    db.add_all([track, mod_a, mod_b, dom_a, dom_b, sk_a, sk_b])
    await db.commit()
    return sk_a.id, sk_b.id, DOMAIN_A_ID, DOMAIN_B_ID


async def test_readiness_reports_sin_datos_for_untouched_domains(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict
) -> None:
    """C.2, 2026-10-04: a user who has never practised gets p_known_mean=None
    ("sin datos") per domain, not the old BKT-prior placeholder (0.1) -
    "no evidence yet" and "evidence and it's bad" are different claims."""
    await _seed_cert_track(db_session)
    r = await client.get(f"/api/v1/exams/certification/{CERT_TRACK_ID}/readiness", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["track_id"] == CERT_TRACK_ID
    assert len(body["domains"]) == 2
    for d in body["domains"]:
        assert d["p_known_mean"] is None
        assert d["ready"] is False
        assert d["skills_assessed"] == 0
        assert d["skills_total"] == 1
    assert body["overall_p_known"] is None, "every domain is sin datos, so the overall is too"


async def test_readiness_reflects_practised_skill(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict
) -> None:
    """When a user has practised Domain A to p_known 0.9, that domain is ready."""
    sk_a_id, _sk_b_id, dom_a_id, _ = await _seed_cert_track(db_session)

    uss = UserSkillState(user_id=user.id, skill_id=sk_a_id, p_known=0.9)
    db_session.add(uss)
    await db_session.commit()

    r = await client.get(f"/api/v1/exams/certification/{CERT_TRACK_ID}/readiness", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    dom_a = next(d for d in body["domains"] if d["domain_id"] == dom_a_id)
    assert dom_a["p_known_mean"] == pytest.approx(0.9)
    assert dom_a["ready"] is True
    assert dom_a["skills_assessed"] == 1


async def test_readiness_404_for_non_certification_track(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict, content_seed: dict
) -> None:
    """A non-cert track returns 404."""
    r = await client.get(
        f"/api/v1/exams/certification/{content_seed['track_id']}/readiness",
        headers=auth_headers,
    )
    assert r.status_code == 404


async def test_readiness_404_for_missing_track(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.get("/api/v1/exams/certification/nonexistent/readiness", headers=auth_headers)
    assert r.status_code == 404


async def test_readiness_overall_excludes_untouched_domains(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict
) -> None:
    """C.2: Domain B is untouched (sin datos), so it must not pull the
    overall average toward 0.1 just for existing - it is left out of both
    the numerator and the denominator, leaving overall_p_known = Domain A's
    own 0.9, not the old weighted blend (0.9×60% + 0.1×40% = 0.58)."""
    sk_a_id, _sk_b_id, _, _ = await _seed_cert_track(db_session)
    db_session.add(UserSkillState(user_id=user.id, skill_id=sk_a_id, p_known=0.9))
    await db_session.commit()

    r = await client.get(f"/api/v1/exams/certification/{CERT_TRACK_ID}/readiness", headers=auth_headers)
    body = r.json()
    assert body["overall_p_known"] == pytest.approx(0.9)
