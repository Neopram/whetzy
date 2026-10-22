"""42.9 / ADR-63 §3-4: la evidencia se trata según su fuente.

Hay una fila `UserSkillState` por (usuario, skill), y antes la escribían tres
copias del mismo bloque Elo/BKT/FSRS: práctica, duelo y test-out. Ninguna sabía
de dónde venía la respuesta. Así, veinte aciertos de duelo dejaban una skill en
«dominada» sin una sola respuesta de práctica.

Regla firmada (ADR-63, firmada por delegación en ADR-69 #5):
- la práctica mueve `p_known` sin tope y cuenta para la puerta;
- el duelo y el test-out lo mueven, pero no lo suben de 0,94 por sí solos ni
  cuentan para la puerta;
- la prueba de nivel siembra (ADR-65 D4) y tampoco cuenta;
- «dominada» = `p_known` ≥ 0,95 y ≥ 7 respuestas de práctica.

Mutación comprobada al escribirlo: con el tope del duelo invertido
(`cap=None`), `test_twenty_duel_wins_do_not_master_a_skill` sale en rojo.
"""

from __future__ import annotations

import pytest

from app.models.content import Question
from app.services import quiz
from app.services.engine import evidence_policy as ep
from app.services.engine.domain_thresholds import (
    MASTERY_THRESHOLD,
    MIN_EVIDENCE_ANSWERS,
    is_mastered,
)


def test_the_policy_table_is_the_signed_one() -> None:
    assert set(ep.RULES) == {"practice", "duel", "test_out", "placement"}
    assert ep.RULES["practice"] == ep.EvidenceRule(counts_for_gate=True, cap=None, floor_at_before=False)
    for source in ("duel", "test_out", "placement"):
        assert ep.RULES[source].counts_for_gate is False
        assert ep.RULES[source].cap == ep.NON_PRACTICE_CAP
    assert ep.RULES["test_out"].floor_at_before is True
    assert ep.NON_PRACTICE_CAP == 0.94 < MASTERY_THRESHOLD


@pytest.mark.parametrize(
    ("source", "before", "after", "expected"),
    [
        ("practice", 0.93, 0.97, 0.97),  # sin tope
        ("duel", 0.93, 0.97, 0.94),  # el duelo no cruza 0,94 por sí solo
        ("duel", 0.96, 0.98, 0.96),  # lo ganado practicando no se pierde ni se infla
        ("duel", 0.80, 0.60, 0.60),  # un fallo de duelo sí baja
        ("test_out", 0.50, 0.40, 0.50),  # test-out aprobado nunca baja (S.9)
        ("test_out", 0.50, 0.99, 0.94),
    ],
)
def test_bound_by_source(source: str, before: float, after: float, expected: float) -> None:
    assert ep.bound(source, before, after) == pytest.approx(expected)


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(KeyError):
        ep.bound("tutor", 0.1, 0.2)


def test_mastered_needs_practice_evidence() -> None:
    assert MIN_EVIDENCE_ANSWERS == 7
    assert is_mastered(0.96, MIN_EVIDENCE_ANSWERS)
    assert not is_mastered(0.96, MIN_EVIDENCE_ANSWERS - 1)
    assert not is_mastered(MASTERY_THRESHOLD - 0.01, 50)


async def _question(db, skill_id: str) -> Question:
    question = Question(
        id="q_evidence_policy_01",
        skill_id=skill_id,
        type="multiple_choice",
        question_es="¿?",
        question_en="?",
        options_es=["a", "b", "c", "d"],
        options_en=["a", "b", "c", "d"],
        correct_index=0,
    )
    db.add(question)
    await db.flush()
    return question


async def _state(db, user_id, skill_id):
    return await quiz._get_or_create_skill_state(db, user_id, skill_id)


@pytest.mark.asyncio
async def test_twenty_duel_wins_do_not_master_a_skill(db_session, user, content_seed) -> None:
    question = await _question(db_session, content_seed["skill_id"])
    for _ in range(20):
        await quiz.apply_evidence(db_session, user.id, question, True, 4000, source="duel")
    state = await _state(db_session, user.id, question.skill_id)
    assert state.p_known <= ep.NON_PRACTICE_CAP
    assert state.attempts == 20
    assert state.practice_attempts == 0
    assert not is_mastered(state.p_known, state.practice_attempts)


@pytest.mark.asyncio
async def test_a_passed_test_out_does_not_master_either(db_session, user, content_seed) -> None:
    question = await _question(db_session, content_seed["skill_id"])
    for _ in range(20):
        await quiz.apply_exam_evidence(db_session, user, question, True, response_time_ms=4000)
    state = await _state(db_session, user.id, question.skill_id)
    assert state.p_known <= ep.NON_PRACTICE_CAP
    assert state.practice_attempts == 0


@pytest.mark.asyncio
async def test_practice_crosses_the_bar_and_counts(db_session, user, content_seed) -> None:
    question = await _question(db_session, content_seed["skill_id"])
    for _ in range(20):
        await quiz.apply_evidence(db_session, user.id, question, True, 4000, source="practice")
    state = await _state(db_session, user.id, question.skill_id)
    assert state.p_known >= MASTERY_THRESHOLD
    assert state.practice_attempts == 20
    assert is_mastered(state.p_known, state.practice_attempts)


@pytest.mark.asyncio
async def test_duel_after_practice_neither_inflates_nor_erases(db_session, user, content_seed) -> None:
    question = await _question(db_session, content_seed["skill_id"])
    for _ in range(20):
        await quiz.apply_evidence(db_session, user.id, question, True, 4000, source="practice")
    state = await _state(db_session, user.id, question.skill_id)
    earned = state.p_known
    await quiz.apply_evidence(db_session, user.id, question, True, 4000, source="duel")
    assert state.p_known == pytest.approx(earned)
    assert state.practice_attempts == 20
