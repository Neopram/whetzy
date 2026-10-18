"""46.1b (docs/PLAN_UI_AVANZADA.md §6.3): `POST /quiz/answer` dice qué hitos
cruzó esa respuesta en `events[]`, con lo que el servidor ya calcula: subida de
nivel, insignias nuevas, misiones completadas, multiplicador de combo cruzado
(×2/×3/×5) y racha en hito (7/30/100). El cliente celebra lo que el servidor
dice; no adivina comparando fotos. Una respuesta nunca trae dos veces el mismo
evento.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.content import Module, Question, Skill, Track
from app.models.gamification import Badge, Mission
from tests.integration.test_quiz import QUIZ, _h, _see_lesson


async def _seed(db_session, n: int = 16) -> None:
    db_session.add_all(
        [
            Track(id="track_fx", name_es="T", name_en="T", order=92, icon="x", color="#000", total_questions=n),
            Module(id="m_fx", track_id="track_fx", name_es="M", name_en="M", order=1,
                   description_es="", description_en=""),
            Skill(id="sk_fx", module_id="m_fx", name_es="S", name_en="S", order=1),
            *[
                Question(
                    id=f"q_fx_{i}", skill_id="sk_fx", type="mcq", difficulty_tier="easy",
                    question_es=f"P{i}", question_en=f"Q{i}", options_es=["a", "b"], options_en=["a", "b"],
                    correct_index=0, explanation_es="e", explanation_en="e", source="test", elo_rating=1200.0,
                )
                for i in range(n)
            ],
        ]
    )
    await db_session.commit()


async def _answer_n(client, auth_headers, n: int, selected_index: int = 0) -> list[list[dict]]:
    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_fx", "mode": "study"}, headers=_h(auth_headers))
    assert r.status_code == 200, r.text
    data = r.json()
    session_id, qid = data["session_id"], data["question"]["id"]
    eventos = []
    for _ in range(n):
        r = await client.post(
            f"{QUIZ}/answer",
            json={"session_id": session_id, "question_id": qid, "selected_index": selected_index,
                  "response_time_ms": 1500},
            headers=_h(auth_headers),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        eventos.append(body["events"])
        qid = body["next_question"]["id"]
    return eventos


def _tipos(evs: list[dict]) -> list[str]:
    return [e["type"] for e in evs]


async def test_combo_cruza_x2_x3_y_x5_una_vez_cada_uno(client, auth_headers, user, db_session):
    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    eventos = await _answer_n(client, auth_headers, 15)
    combos = [(i + 1, e["payload"]) for i, evs in enumerate(eventos) for e in evs if e["type"] == "combo_multiplier"]
    assert combos == [(3, {"multiplier": 2}), (7, {"multiplier": 3}), (15, {"multiplier": 5})]


async def test_fallar_no_trae_combo(client, auth_headers, user, db_session):
    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    eventos = await _answer_n(client, auth_headers, 4, selected_index=1)
    assert all("combo_multiplier" not in _tipos(evs) for evs in eventos)


async def test_subida_de_nivel_trae_el_antes_y_el_despues(client, auth_headers, user, db_session):
    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    user.total_xp = 495  # nivel 1; un acierto (10 XP) lo lleva a 505 → nivel 2
    user.level = 1
    await db_session.commit()
    [primeros, segundos] = await _answer_n(client, auth_headers, 2)
    assert {"type": "level_up", "payload": {"level_before": 1, "level": 2}} in primeros
    assert "level_up" not in _tipos(segundos)


async def test_mision_completada_e_insignia_nueva_salen_una_sola_vez(client, auth_headers, user, db_session):
    await _seed(db_session)
    db_session.add_all(
        [
            Mission(id="m_fx_2q", type="questions_answered", target_value=2, xp_reward=0,
                    name_es="Responde 2", name_en="Answer 2"),
            Badge(id="b_fx_1q", name_es="Primera", name_en="First", criteria_type="questions_answered",
                  criteria_value=1),
        ]
    )
    await db_session.commit()
    await _see_lesson(db_session, user, "sk_fx")
    eventos = await _answer_n(client, auth_headers, 3)
    assert eventos[0].count({"type": "badge_earned", "payload": {"badge_id": "b_fx_1q"}}) == 1
    assert "mission_completed" not in _tipos(eventos[0])
    assert eventos[1].count({"type": "mission_completed", "payload": {"mission_id": "m_fx_2q"}}) == 1
    # Ya concedidas: no vuelven en las respuestas siguientes.
    assert _tipos(eventos[1]).count("badge_earned") == 0
    assert "mission_completed" not in _tipos(eventos[2])


async def test_racha_en_hito_sale_al_llegar_a_7(client, auth_headers, user, db_session):
    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    user.current_streak = 6
    user.last_active = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()
    [primeros, segundos] = await _answer_n(client, auth_headers, 2)
    assert {"type": "streak_milestone", "payload": {"days": 7}} in primeros
    # El mismo día la racha no vuelve a subir: no se repite.
    assert "streak_milestone" not in _tipos(segundos)


async def test_ninguna_respuesta_trae_un_evento_repetido(client, auth_headers, user, db_session):
    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    user.total_xp = 495
    await db_session.commit()
    for evs in await _answer_n(client, auth_headers, 8):
        claves = [(e["type"], tuple(sorted(e["payload"].items()))) for e in evs]
        assert len(claves) == len(set(claves))


async def test_la_reentrega_idempotente_no_repite_los_hitos(client, auth_headers, user, db_session):
    """La cola offline (33.2) reenvía con el mismo `event_id`: la segunda vez no
    se cuenta la respuesta, así que tampoco se celebra otra vez."""
    import uuid as _uuid

    await _seed(db_session)
    await _see_lesson(db_session, user, "sk_fx")
    user.total_xp = 495
    await db_session.commit()
    r = await client.post(f"{QUIZ}/start", json={"skill_id": "sk_fx", "mode": "study"}, headers=_h(auth_headers))
    data = r.json()
    body = {"session_id": data["session_id"], "question_id": data["question"]["id"], "selected_index": 0,
            "response_time_ms": 1500, "event_id": str(_uuid.uuid4())}
    primera = await client.post(f"{QUIZ}/answer", json=body, headers=_h(auth_headers))
    segunda = await client.post(f"{QUIZ}/answer", json=body, headers=_h(auth_headers))
    assert "level_up" in _tipos(primera.json()["events"])
    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["events"] == []
