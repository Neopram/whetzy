"""Certification track data model (10.1): Domain + Track exam blueprint fields.

A cert track reuses Track/Module/Skill/Question — these tests confirm the
new Domain model and the exam-blueprint columns on Track/Skill behave, and
that a certification track coexists with a core (non-cert) track without
affecting it.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Domain, Module, Skill, Track

pytestmark = pytest.mark.asyncio


async def test_core_track_defaults_to_non_certification(db_session: AsyncSession, content_seed: dict) -> None:
    track = await db_session.get(Track, content_seed["track_id"])
    assert track is not None
    assert track.is_certification is False
    assert track.cert_provider is None
    assert track.exam_question_count is None


async def test_certification_track_coexists_with_core_tracks(
    db_session: AsyncSession, content_seed: dict
) -> None:
    cert_track = Track(
        id="aws-ccp",
        name_es="AWS Cloud Practitioner",
        name_en="AWS Cloud Practitioner",
        order=8,
        icon="☁️",
        color="#FF9900",
        is_certification=True,
        cert_provider="AWS",
        exam_question_count=65,
        exam_duration_minutes=90,
        passing_score_pct=70.0,
    )
    db_session.add(cert_track)
    await db_session.commit()

    result = await db_session.execute(select(Track))
    tracks = result.scalars().all()
    track_ids = {t.id for t in tracks}
    assert track_ids == {content_seed["track_id"], "aws-ccp"}

    core_track = await db_session.get(Track, content_seed["track_id"])
    assert core_track is not None
    assert core_track.is_certification is False


async def test_domains_carry_exam_weights_and_link_skills(db_session: AsyncSession) -> None:
    track = Track(
        id="aws-ccp",
        name_es="AWS Cloud Practitioner",
        name_en="AWS Cloud Practitioner",
        order=8,
        is_certification=True,
        cert_provider="AWS",
    )
    domains = [
        Domain(id="d1", track_id="aws-ccp", name_es="Conceptos cloud", name_en="Cloud Concepts", weight_pct=24, order=1),
        Domain(id="d2", track_id="aws-ccp", name_es="Seguridad", name_en="Security and Compliance", weight_pct=30, order=2),
        Domain(id="d3", track_id="aws-ccp", name_es="Tecnología cloud", name_en="Cloud Technology", weight_pct=34, order=3),
        Domain(id="d4", track_id="aws-ccp", name_es="Facturación", name_en="Billing and Pricing", weight_pct=12, order=4),
    ]
    mod = Module(id="m-aws1", track_id="aws-ccp", name_es="Fundamentos", name_en="Fundamentals", order=1)
    skill = Skill(id="sk-aws1", module_id="m-aws1", name_es="EC2", name_en="EC2", order=1, domain_id="d3")
    db_session.add_all([track, *domains, mod, skill])
    await db_session.commit()

    assert sum(d.weight_pct for d in domains) == 100

    loaded_skill = await db_session.get(Skill, "sk-aws1")
    assert loaded_skill is not None
    await db_session.refresh(loaded_skill, attribute_names=["domain"])
    assert loaded_skill.domain is not None
    assert loaded_skill.domain.id == "d3"

    loaded_track = await db_session.get(Track, "aws-ccp")
    assert loaded_track is not None
    await db_session.refresh(loaded_track, attribute_names=["domains"])
    assert {d.id for d in loaded_track.domains} == {"d1", "d2", "d3", "d4"}
