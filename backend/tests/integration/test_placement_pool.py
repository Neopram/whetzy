"""La prueba de nivel solo sirve preguntas que se puedan contestar.

`PlacementAnswerRequest` solo lleva `selected_index`, asi que una pregunta sin
opciones —`sql_exec`, `fill_blank`, `fix_bug`— no tiene forma de responderse. El
pool las incluia todas: una sesion podia servir una y dejar al alumno encallado.

`multiple_choice` entra en el filtro porque el banco usa ese nombre en 1.015
preguntas ademas de `mcq`; sin el, los tracks de certificacion (09, 10, 11) se
quedaban con un pool vacio y la prueba ni arrancaba.
"""

from __future__ import annotations

import pytest

from app.models.content import Module, Question, Skill, Track
from app.services.placement import _TIPOS_RESPONDIBLES, _track_item_pool

PLACEMENT = "/api/v1/placement"


def _pregunta(qid: str, skill: str, tipo: str) -> Question:
    con_opciones = tipo in ("mcq", "multiple_choice", "true_false", "code_output")
    return Question(
        id=qid,
        skill_id=skill,
        type=tipo,
        difficulty_tier="easy",
        question_es="Pregunta",
        question_en="Question",
        options_es=["a", "b"] if con_opciones else None,
        options_en=["a", "b"] if con_opciones else None,
        correct_index=0 if con_opciones else None,
        correct_answer_es=None if con_opciones else "4",
        correct_answer_en=None if con_opciones else "4",
        explanation_es="e",
        explanation_en="e",
        source="test",
        elo_rating=1200.0,
    )


@pytest.fixture
async def track_mixto(db_session):
    """Un track con los dos tipos mezclados, como el banco real."""
    track = Track(
        id="track_pool", name_es="T", name_en="T", order=98,
        icon="x", color="#000", total_questions=0,
    )
    mod = Module(
        id="m_pool", track_id="track_pool", name_es="M", name_en="M",
        order=1, description_es="", description_en="",
    )
    skill = Skill(id="sk_pool", module_id="m_pool", name_es="S", name_en="S", order=1)
    db_session.add_all([track, mod, skill])
    filas = []
    for i, tipo in enumerate(
        ["mcq", "multiple_choice", "true_false", "code_output",
         "sql_exec", "fill_blank", "fill_blank_exec", "fix_bug", "js_exec"]
    ):
        filas.append(_pregunta(f"q_pool_{i}", "sk_pool", tipo))
    db_session.add_all(filas)
    await db_session.commit()
    return "track_pool"


async def test_el_pool_excluye_lo_que_no_se_puede_contestar(db_session, track_mixto) -> None:
    items = await _track_item_pool(db_session, track_mixto)

    ids = {i.item_id for i in items}
    assert len(ids) == 4, ids  # mcq, multiple_choice, true_false, code_output


async def test_multiple_choice_cuenta_como_respondible() -> None:
    """Sin el, los tracks de certificacion se quedan con el pool vacio."""
    assert "multiple_choice" in _TIPOS_RESPONDIBLES
    assert "mcq" in _TIPOS_RESPONDIBLES


@pytest.mark.parametrize("tipo", ["sql_exec", "fill_blank", "fill_blank_exec", "fix_bug", "js_exec"])
async def test_los_tipos_sin_opciones_quedan_fuera(tipo: str) -> None:
    assert tipo not in _TIPOS_RESPONDIBLES


async def test_la_prueba_sirve_una_pregunta_con_opciones(client, auth_headers, track_mixto) -> None:
    """De punta a punta: lo que llega al alumno se puede responder."""
    r = await client.post(
        f"{PLACEMENT}/start", json={"track_id": track_mixto}, headers=auth_headers
    )

    assert r.status_code == 200, r.text
    pregunta = r.json()["question"]
    assert pregunta is not None
    assert pregunta["options_es"], f"tipo {pregunta['type']} llego sin opciones"
    assert pregunta["type"] in _TIPOS_RESPONDIBLES


async def test_un_track_sin_preguntas_respondibles_lo_dice(client, auth_headers, db_session) -> None:
    track = Track(
        id="track_solo_exec", name_es="T", name_en="T", order=97,
        icon="x", color="#000", total_questions=0,
    )
    mod = Module(
        id="m_solo_exec", track_id="track_solo_exec", name_es="M", name_en="M",
        order=1, description_es="", description_en="",
    )
    skill = Skill(id="sk_solo_exec", module_id="m_solo_exec", name_es="S", name_en="S", order=1)
    db_session.add_all([track, mod, skill, _pregunta("q_solo_exec", "sk_solo_exec", "sql_exec")])
    await db_session.commit()

    r = await client.post(
        f"{PLACEMENT}/start", json={"track_id": "track_solo_exec"}, headers=auth_headers
    )

    assert r.status_code == 422
    assert "answered by choosing" in r.json()["detail"]


async def test_una_true_false_sin_opciones_no_entra_en_el_pool(db_session, track_mixto) -> None:
    """El tipo no basta: hace falta con que corregir.

    83 preguntas `true_false` llegaron al banco con `options_*` y
    `correct_index` en null y la respuesta como texto en `correct_answer_es`.
    El quiz y los duelos ya las excluian exigiendo el indice; el pool de
    nivelacion filtraba solo por tipo y las dejaba pasar, asi que el alumno
    recibia una pregunta sin nada que pulsar. El contenido esta arreglado,
    pero la guarda se queda.
    """
    rota = _pregunta("q_pool_tf_rota", "sk_pool", "true_false")
    rota.options_es = None
    rota.options_en = None
    rota.correct_index = None
    rota.correct_answer_es = "Verdadero"
    rota.correct_answer_en = "True"
    db_session.add(rota)
    await db_session.commit()

    items = await _track_item_pool(db_session, track_mixto)

    assert "q_pool_tf_rota" not in {i.item_id for i in items}
