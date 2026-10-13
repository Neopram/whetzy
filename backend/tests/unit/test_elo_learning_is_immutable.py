"""Regla del dueño del 2026-10-12: el Elo aprendido es inmutable para el contenido.

`content_loader` corre en cada arranque (`start.sh`). Si sembrara el prior
editorial (`difficulty_tier`) sin mirar si la pregunta ya aprendió, cada deploy
borraría la calibración hecha por respuestas reales. Prueba de aceptación que
pidió el dueño: crear la pregunta (Elo = f(nivel)), responderla por quiz y por
duelo (y por examen, el tercer escritor), sincronizar el contenido DOS veces y
comprobar que el Elo aprendido sigue intacto.
"""

from __future__ import annotations

import pytest

from app.models.content import Question
from app.services import quiz
from app.services.content_loader import ELO_TIER_PRIOR, _upsert_question, seed_elo


def _q(skill_id: str, tier: str = "hard", **extra) -> dict:
    return {
        "id": "q_elo_accept_01",
        "skill_id": skill_id,
        "type": "multiple_choice",
        "difficulty_tier": tier,
        "question_es": "¿?", "question_en": "?",
        "options_es": ["a", "b"], "options_en": ["a", "b"],
        "correct_index": 0,
        **extra,
    }


async def _sync(db, q: dict) -> Question:
    """Lo que hace `load_content` por cada pregunta del banco."""
    assert await _upsert_question(db, q)
    await db.flush()
    question = await db.get(Question, q["id"])
    assert question is not None
    return question


def test_the_prior_follows_the_editorial_tier() -> None:
    assert [seed_elo({"difficulty_tier": t}) for t in ("easy", "medium", "hard", "expert")] == [
        1350.0, 1500.0, 1650.0, 1800.0,
    ]
    assert seed_elo({}) == ELO_TIER_PRIOR["medium"]
    assert seed_elo({"difficulty_tier": "hard", "difficulty": 1.0}) == 1620.0  # IRT manda


@pytest.mark.asyncio
async def test_learned_elo_survives_two_content_syncs(db_session, user, content_seed) -> None:
    q = _q(content_seed["skill_id"])
    question = await _sync(db_session, q)
    assert question.elo_rating == 1650.0
    assert question.elo_updates == 0

    # Duelo (quiz.apply_answer_to_skill_state) y examen (quiz.apply_exam_evidence):
    # los dos escritores que no dejan fila en `responses`.
    await quiz.apply_answer_to_skill_state(db_session, user.id, question, True, 4000)
    await quiz.apply_exam_evidence(db_session, user, question, False, response_time_ms=4000)
    await db_session.flush()
    learned = question.elo_rating
    assert learned != 1650.0
    assert question.elo_updates == 2

    for _ in range(2):
        question = await _sync(db_session, q)
    assert question.elo_rating == learned
    assert question.elo_updates == 2


@pytest.mark.asyncio
async def test_a_question_nobody_answered_follows_its_new_tier(db_session, content_seed) -> None:
    """Sin evidencia el rating es solo el prior: si el autor cambia el nivel, se re-siembra."""
    await _sync(db_session, _q(content_seed["skill_id"], tier="hard"))
    question = await _sync(db_session, _q(content_seed["skill_id"], tier="easy"))
    assert question.elo_rating == 1350.0


@pytest.mark.asyncio
async def test_item_k_decays_with_real_interactions(db_session, user, content_seed) -> None:
    """El ítem usa sus interacciones reales para la K de `elo.py` (antes, 30 fijas: K=12
    siempre). La primera respuesta a una pregunta nueva mueve más que la vigésima."""
    question = await _sync(db_session, _q(content_seed["skill_id"], tier="medium"))
    before = question.elo_rating
    await quiz.apply_answer_to_skill_state(db_session, user.id, question, True, 4000)
    first_move = abs(question.elo_rating - before)
    question.elo_updates = 25
    before = question.elo_rating
    await quiz.apply_answer_to_skill_state(db_session, user.id, question, True, 4000)
    late_move = abs(question.elo_rating - before)
    assert first_move > late_move
