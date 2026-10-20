"""Preguntas `interactive` en el quiz (40.1).

El servidor corrige el `widget_state` con el checker de la pregunta, no se fía
del cliente, no enseña el `target` antes de responder y lo devuelve después
para que el cliente vuelva a corregir. El acierto mueve BKT/Elo como cualquier
otro tipo.
"""

from __future__ import annotations

import itertools

import pytest
from sqlalchemy import select

from app.models.lesson_completion import LessonCompletion

QUIZ = "/api/v1/quiz"
SPEC = {"widget": "binarySearch", "params": {"items": [1, 3, 5, 7, 9]}, "target": [5, 7], "checker": "exact"}

_ip = itertools.count(20)


def _h(auth_headers: dict) -> dict:
    return {"X-Forwarded-For": f"198.51.101.{next(_ip) % 255 or 255}", **auth_headers}


async def _seed(db_session, spec: dict | None = SPEC, qid: str = "q_int401") -> None:
    from app.models.content import Module, Question, Skill, Track

    db_session.add_all(
        [
            Track(id="track_int401", name_es="T", name_en="T", order=98, icon="x", color="#000", total_questions=1),
            Module(
                id="m_int401", track_id="track_int401", name_es="M", name_en="M", order=1,
                description_es="", description_en="",
            ),
            Skill(id="sk_int401", module_id="m_int401", name_es="S", name_en="S", order=1),
            Question(
                id=qid,
                skill_id="sk_int401",
                type="interactive",
                difficulty_tier="easy",
                question_es="Busca el 7.",
                question_en="Find 7.",
                interactive=spec,
                explanation_es="Mitad, luego derecha.",
                explanation_en="Middle, then right.",
                source="test",
                elo_rating=1200.0,
            ),
        ]
    )
    await db_session.commit()


async def _start(client, auth_headers, qid: str = "q_int401") -> dict:
    r = await client.post(f"{QUIZ}/start", json={"force_question_id": qid}, headers=_h(auth_headers))
    assert r.status_code == 200, r.text
    return r.json()


async def _answer(client, auth_headers, data: dict, **extra) -> dict:
    r = await client.post(
        f"{QUIZ}/answer",
        json={"session_id": data["session_id"], "question_id": data["question"]["id"], "response_time_ms": 1200, **extra},
        headers=_h(auth_headers),
    )
    assert r.status_code == 200, r.text
    return r.json()


async def test_la_pregunta_no_ensena_el_target(client, auth_headers, db_session):
    await _seed(db_session)
    q = (await _start(client, auth_headers))["question"]
    assert q["type"] == "interactive"
    assert q["interactive"] == {"widget": "binarySearch", "params": {"items": [1, 3, 5, 7, 9]}, "checker": "exact"}
    assert "target" not in q["interactive"]


@pytest.mark.parametrize(
    ("extra", "correct"),
    [
        ({"widget_state": [5, 7]}, True),
        ({"widget_state": [7, 5]}, False),
        # Sin estado es incorrecto aunque el cliente mande el índice «bueno».
        ({"selected_index": 1}, False),
        ({"widget_state": None, "selected_index": 1}, False),
    ],
)
async def test_el_servidor_corrige_el_estado(client, auth_headers, db_session, extra, correct):
    await _seed(db_session)
    res = await _answer(client, auth_headers, await _start(client, auth_headers), **extra)
    assert res["correct"] is correct
    # El objetivo llega después de responder, para que el cliente vuelva a corregir.
    assert res["widget_target"] == [5, 7]


async def test_un_acierto_mueve_el_dominio(client, auth_headers, db_session):
    await _seed(db_session)
    res = await _answer(client, auth_headers, await _start(client, auth_headers), widget_state=[5, 7])
    assert res["skill_mastery"]["sk_int401"] > 0.0
    assert res["next_review"] is not None


async def test_otros_tipos_no_llevan_widget_target(client, auth_headers, content_seed, db_session):
    data = await _start(client, auth_headers, content_seed["question_id"])
    res = await _answer(client, auth_headers, data, selected_index=0)
    assert res["widget_target"] is None
    assert data["question"]["interactive"] is None


async def test_un_estado_enorme_es_422(client, auth_headers, db_session):
    await _seed(db_session)
    data = await _start(client, auth_headers)
    r = await client.post(
        f"{QUIZ}/answer",
        json={
            "session_id": data["session_id"],
            "question_id": data["question"]["id"],
            "response_time_ms": 1200,
            "widget_state": ["x" * 1000] * 25,
        },
        headers=_h(auth_headers),
    )
    assert r.status_code == 422


async def test_la_practica_sirve_interactive_solo_con_especificacion(client, auth_headers, user, db_session):
    # Sin especificación no hay contra qué corregir: el selector no la sirve.
    await _seed(db_session, spec=None)
    db_session.add(LessonCompletion(user_id=user.id, skill_id="sk_int401"))
    await db_session.commit()
    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_int401", "mode": "study"}, headers=_h(auth_headers))
    assert r.status_code == 200, r.text
    assert r.json()["question"] is None

    from app.models.content import Question

    q = (await db_session.execute(select(Question).where(Question.id == "q_int401"))).scalar_one()
    q.interactive = SPEC
    await db_session.commit()
    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_int401", "mode": "study"}, headers=_h(auth_headers))
    assert r.json()["question"]["id"] == "q_int401"
