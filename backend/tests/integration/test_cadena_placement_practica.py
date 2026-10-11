"""Cadena prueba de nivel → práctica (auditoría de interacciones 2026-10-11).

La prueba de nivel siembra `p_known` y suma `attempts` sin tocar FSRS; la
primera respuesta de práctica construía una tarjeta «review» con estabilidad 0
y FSRS lanzaba `ZeroDivisionError` (500 en bucle: la skill seguía en 0,94 y
el selector la volvía a servir). Cada pieza tenía sus tests; la cadena no.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("selected_index", [0, 1])  # acierto y fallo: los dos caminos de FSRS
async def test_practicar_tras_la_prueba_de_nivel_no_rompe(
    client, auth_headers, user, content_seed, selected_index
) -> None:
    start = await client.post(
        "/api/v1/placement/start", json={"track_id": content_seed["track_id"]}, headers=auth_headers
    )
    assert start.status_code in (200, 201), start.text
    sid = start.json()["session_id"]
    answer = await client.post(
        "/api/v1/placement/answer",
        json={
            "session_id": sid,
            "question_id": content_seed["question_id"],
            "selected_index": 0,
            "response_time_ms": 1000,
        },
        headers=auth_headers,
    )
    assert answer.status_code == 200 and answer.json()["finished"], answer.text

    quiz = await client.post(
        "/api/v1/quiz/start",
        json={"mode": "study", "skill_id": content_seed["skill_id"]},
        headers=auth_headers,
    )
    assert quiz.status_code == 200, quiz.text
    body = quiz.json()
    res = await client.post(
        "/api/v1/quiz/answer",
        json={
            "session_id": body["session_id"],
            "question_id": body["question"]["id"],
            "selected_index": selected_index,
            "response_time_ms": 1500,
        },
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["correct"] is (selected_index == 0)


@pytest.mark.asyncio
async def test_event_id_demasiado_largo_es_422_no_500(
    client, auth_headers, user, db_session, content_seed
) -> None:
    """La cola offline mandaba 65 caracteres a una columna de 64."""
    from tests.integration.test_quiz import _start_quiz

    session_id, question_id = await _start_quiz(
        client, auth_headers, content_seed["skill_id"], db_session, user
    )
    res = await client.post(
        "/api/v1/quiz/answer",
        json={
            "session_id": session_id,
            "question_id": question_id,
            "selected_index": 0,
            "response_time_ms": 1500,
            "event_id": "x" * 65,
        },
        headers=auth_headers,
    )
    assert res.status_code == 422, res.text
