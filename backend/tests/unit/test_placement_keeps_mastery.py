"""D-18 (dueño, 2026-10-12): la prueba de nivel nunca borra dominio ganado.

`_seed_skill_states` sobrescribía `p_known` en las skills que ya tenían
historial, así que un placement malo de tres preguntas tiraba al suelo una
skill practicada durante semanas. Los cinco casos que pidió el dueño: sin
historial, con historial, placement peor que el estado, placement mejor y
placement repetido.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.user import UserSkillState
from app.services.placement import _P_KNOWN_CAP, _seed_skill_states

SKILL = "sk010101"


async def _state(db, user) -> UserSkillState | None:
    await db.flush()  # la sesión de test no autoflushea; las filas nuevas van en add()
    return await db.scalar(
        select(UserSkillState).where(
            UserSkillState.user_id == user.id, UserSkillState.skill_id == SKILL
        )
    )


async def _with_history(db, user, p_known: float, attempts: int = 20) -> None:
    db.add(
        UserSkillState(
            user_id=user.id,
            skill_id=SKILL,
            p_known=p_known,
            attempts=attempts,
            correct_count=attempts // 2,
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_without_history_placement_sets_the_estimate(db_session, user, content_seed):
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 3}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(0.75)
    assert (state.attempts, state.correct_count) == (4, 3)


@pytest.mark.asyncio
async def test_an_untouched_row_is_only_the_prior_so_placement_sets_it(
    db_session, user, content_seed
):
    await _with_history(db_session, user, p_known=0.1, attempts=0)
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 0}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_worse_placement_never_lowers_earned_mastery(db_session, user, content_seed):
    await _with_history(db_session, user, p_known=0.9)
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 3, "correct": 0}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(0.9)
    # La evidencia sí cuenta: los intentos se suman.
    assert state.attempts == 23


@pytest.mark.asyncio
async def test_better_placement_raises_a_skill_with_history(db_session, user, content_seed):
    await _with_history(db_session, user, p_known=0.3)
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 4}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(_P_KNOWN_CAP)


@pytest.mark.asyncio
async def test_a_mastered_skill_is_not_pulled_under_the_cap(db_session, user, content_seed):
    await _with_history(db_session, user, p_known=0.98)
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 4}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(0.98)


@pytest.mark.asyncio
async def test_repeated_placement_does_not_ratchet_down(db_session, user, content_seed):
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 3}})
    await db_session.flush()
    await _seed_skill_states(db_session, user.id, {SKILL: {"total": 4, "correct": 1}})
    state = await _state(db_session, user)
    assert state is not None
    assert state.p_known == pytest.approx(0.75)
    assert state.attempts == 8
