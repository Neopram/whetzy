"""43.3 (ADR-65 D3/D4): la prueba de nivel tiene 20 preguntas y siembra por módulo.

D3: 15 estratificadas (5 básicas, 5 intermedias y 5 avanzadas, repartidas por
módulos) y 5 adaptativas en la banda frontera. La banda de una pregunta es su
`difficulty_tier` cuando el track tiene las tres bandas; si no (16 tracks del
banco llegan sin tier y el loader les pone «medium»), el tercio del módulo
dentro del track.

D4: un módulo con ≥ 70 % deja todas sus skills en 0,6; el resto, encogido
hacia 0,1. Nunca baja una skill con historial (D-18) y no marca lecciones vistas.

Antes: CAT de 20 a 50 preguntas por información de Fisher, sin bandas, y la
siembra copiaba el acierto de cada skill suelta (1 de 1 → 0,94).
"""

from __future__ import annotations

from collections import Counter

import pytest
from sqlalchemy import func, select

from app.models.content import Module, Question, Skill, Track
from app.models.lesson_view import LessonView
from app.models.user import UserSkillState
from app.services.placement import (
    PLACEMENT_LENGTH,
    SEED_PRIOR,
    SEED_STRONG,
    _seed_by_module,
    _track_pool,
)

PLACEMENT = "/api/v1/placement"
MODULES = 6
SKILLS_PER_MODULE = 2
QUESTIONS_PER_SKILL = 6


def _q(qid: str, skill: str, tier: str) -> Question:
    return Question(
        id=qid,
        skill_id=skill,
        type="mcq",
        difficulty_tier=tier,
        question_es="P",
        question_en="Q",
        options_es=["a", "b", "c", "d"],
        options_en=["a", "b", "c", "d"],
        correct_index=0,
        explanation_es="e",
        explanation_en="e",
        source="test",
        elo_rating=1500.0,
    )


async def _track(db, track_id: str, tier_of) -> str:
    db.add(
        Track(
            id=track_id, name_es="T", name_en="T", order=97,
            icon="x", color="#000", total_questions=0,
        )
    )
    for m in range(1, MODULES + 1):
        db.add(
            Module(
                id=f"{track_id}_m{m}", track_id=track_id, name_es=f"M{m}", name_en=f"M{m}",
                order=m, description_es="", description_en="",
            )
        )
        for s in range(1, SKILLS_PER_MODULE + 1):
            sid = f"{track_id}_m{m}s{s}"
            db.add(Skill(id=sid, module_id=f"{track_id}_m{m}", name_es="S", name_en="S", order=s))
            for i in range(QUESTIONS_PER_SKILL):
                db.add(_q(f"{sid}_q{i}", sid, tier_of(m, i)))
    await db.commit()
    return track_id


@pytest.fixture
async def sin_tier(db_session):
    # Como los 16 tracks sin tier: todo llega como «medium».
    return await _track(db_session, "t_sintier", lambda m, i: "medium")


@pytest.fixture
async def con_tier(db_session):
    tiers = ("easy", "medium", "hard", "expert", "easy", "medium")
    return await _track(db_session, "t_contier", lambda m, i: tiers[i])


def _module_of(qid: str) -> int:
    return int(qid.split("_m")[1][0])


def _band_by_third(qid: str) -> str:
    return ("basic", "intermediate", "advanced")[(_module_of(qid) - 1) * 3 // MODULES]


async def _run(client, headers, track_id: str, correct) -> list[str]:
    start = await client.post(f"{PLACEMENT}/start", json={"track_id": track_id}, headers=headers)
    assert start.status_code == 200, start.text
    sid = start.json()["session_id"]
    question = start.json()["question"]
    served: list[str] = []
    finished = False
    while question is not None:
        served.append(question["id"])
        r = await client.post(
            f"{PLACEMENT}/answer",
            json={
                "session_id": sid,
                "question_id": question["id"],
                "selected_index": 0 if correct(question["id"], len(served)) else 1,
                "response_time_ms": 900,
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text
        finished = r.json()["finished"]
        question = r.json()["next_question"]
        assert len(served) <= PLACEMENT_LENGTH + 1, "la prueba no para"
    assert finished
    return served


async def test_banda_por_tercio_de_modulo_en_un_track_sin_tier(db_session, sin_tier):
    pool = await _track_pool(db_session, sin_tier)
    assert {p.band for p in pool if _module_of(p.item.item_id) in (1, 2)} == {"basic"}
    assert {p.band for p in pool if _module_of(p.item.item_id) in (3, 4)} == {"intermediate"}
    assert {p.band for p in pool if _module_of(p.item.item_id) in (5, 6)} == {"advanced"}


async def test_banda_por_tier_cuando_el_track_tiene_las_tres(db_session, con_tier):
    pool = await _track_pool(db_session, con_tier)
    by_id = {p.item.item_id: p.band for p in pool}
    assert by_id["t_contier_m1s1_q0"] == "basic"
    assert by_id["t_contier_m1s1_q1"] == "intermediate"
    assert by_id["t_contier_m6s1_q2"] == "advanced"
    assert by_id["t_contier_m6s1_q3"] == "advanced"  # «expert» cuenta como avanzada


async def test_veinte_preguntas_exactas_5_5_5_por_modulos(client, auth_headers, sin_tier):
    served = await _run(client, auth_headers, sin_tier, lambda qid, n: True)
    assert len(served) == PLACEMENT_LENGTH == 20
    assert len(set(served)) == 20
    for k, band in enumerate(("basic", "intermediate", "advanced")):
        block = served[5 * k : 5 * k + 5]
        assert {_band_by_third(q) for q in block} == {band}, block
        # Repartidas por módulos: los dos módulos de la banda salen (3 + 2).
        assert sorted(Counter(_module_of(q) for q in block).values()) == [2, 3], block


@pytest.mark.parametrize(
    ("aciertos", "frontera"),
    [(lambda qid, n: True, "advanced"), (lambda qid, n: False, "basic")],
    ids=["todo-bien", "todo-mal"],
)
async def test_las_5_adaptativas_van_a_la_banda_frontera(
    client, auth_headers, sin_tier, aciertos, frontera
):
    served = await _run(client, auth_headers, sin_tier, aciertos)
    assert {_band_by_third(q) for q in served[15:]} == {frontera}


async def test_frontera_es_la_primera_banda_que_no_se_supera(client, auth_headers, sin_tier):
    # Acierta las básicas y falla el resto: la frontera es la intermedia.
    served = await _run(
        client, auth_headers, sin_tier, lambda qid, n: _band_by_third(qid) == "basic"
    )
    assert {_band_by_third(q) for q in served[15:]} == {"intermediate"}


async def test_la_siembra_va_por_modulo_y_no_marca_lecciones(
    client, auth_headers, user, db_session, sin_tier
):
    # Acierta todo lo básico (módulos 1 y 2) y falla lo demás.
    await _run(client, auth_headers, sin_tier, lambda qid, n: _band_by_third(qid) == "basic")
    rows = (
        await db_session.scalars(select(UserSkillState).where(UserSkillState.user_id == user.id))
    ).all()
    p = {r.skill_id: r.p_known for r in rows}
    for m in (1, 2):
        for s in (1, 2):
            # Las dos skills del módulo, también la que no salió en la prueba.
            assert p[f"t_sintier_m{m}s{s}"] == pytest.approx(SEED_STRONG)
    for m in (3, 4, 5, 6):
        for s in (1, 2):
            sid = f"t_sintier_m{m}s{s}"
            if sid in p:
                # Todo fallado: el encogimiento lo deja por debajo del prior, nunca a 0.
                assert 0 < p[sid] < SEED_PRIOR, (sid, p[sid])
    vistas = await db_session.scalar(
        select(func.count()).select_from(LessonView).where(LessonView.user_id == user.id)
    )
    assert vistas == 0


async def test_un_modulo_fuerte_necesita_mas_de_una_pregunta(db_session, user, sin_tier):
    # 1 de 1 no es evidencia de módulo: antes daba 0,94 a esa skill.
    await _seed_by_module(
        db_session,
        user.id,
        modules={"t_sintier_m1": ["t_sintier_m1s1", "t_sintier_m1s2"]},
        answers={"t_sintier_m1s1": (1, 1)},
    )
    await db_session.flush()
    row = await db_session.scalar(
        select(UserSkillState).where(
            UserSkillState.user_id == user.id, UserSkillState.skill_id == "t_sintier_m1s1"
        )
    )
    assert row is not None and SEED_PRIOR < row.p_known < SEED_STRONG
