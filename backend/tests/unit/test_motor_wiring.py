"""Motor conectado como dice que está (plan 2026-10-13, fase 2).

- C3: la cohorte DKT no lee respuestas de la prueba de nivel; el brazo BKT
  tampoco las procesa (`_seed_skill_states` siembra una vez), así que el A/B
  comparaba dos historias distintas.
- D3: P(G) sale del formato del ítem: verdadero/falso es 0,5 y n opciones 1/n;
  con 0,25 para todo, un acierto de verdadero/falso subía el dominio como uno de
  cuatro opciones.
- Duelo: un ítem sin `correct_index` nunca puntúa; la rama de ejecutables dejaba
  que `selected_index == 1` decidiera.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.content import Module, Question, Skill, Track
from app.models.duel import Duel
from app.models.session import Response, StudySession
from app.models.user import User
from app.services import quiz
from app.services.engine.bkt import BKTModel, SkillState
from app.services.quiz import _select_skill, guess_rate


def _q(qtype: str, n_options: int | None, correct_index: int | None = 0) -> Question:
    opts = [f"o{i}" for i in range(n_options)] if n_options else None
    return Question(
        id=f"q_{uuid.uuid4().hex[:8]}",
        skill_id="s",
        type=qtype,
        question_es="?",
        question_en="?",
        options_es=opts,
        options_en=opts,
        correct_index=correct_index if n_options else None,
    )


# ── D3 ────────────────────────────────────────────────────────────────────────


class TestGuessRate:
    def test_true_false_is_a_coin_toss(self) -> None:
        assert guess_rate(_q("true_false", 2)) == 0.5

    @pytest.mark.parametrize("n", [3, 4, 5])
    def test_options_give_one_over_n(self, n: int) -> None:
        assert guess_rate(_q("multiple_choice", n)) == pytest.approx(1 / n)

    def test_free_answer_keeps_the_default(self) -> None:
        assert guess_rate(_q("fill_blank_exec", None)) is None

    def test_a_lucky_true_false_counts_for_less_than_a_four_option_hit(self) -> None:
        bkt = BKTModel()
        tf = bkt.update(SkillState("s", p_known=0.3), True, p_guess=guess_rate(_q("true_false", 2)))
        mc = bkt.update(SkillState("s", p_known=0.3), True, p_guess=guess_rate(_q("mcq", 4)))
        assert tf.p_known < mc.p_known

    def test_none_keeps_the_old_behaviour(self) -> None:
        bkt = BKTModel()
        a = bkt.update(SkillState("s", p_known=0.3), True)
        b = bkt.update(SkillState("s", p_known=0.3), True, p_guess=None)
        assert a.p_known == b.p_known


# ── C3 ────────────────────────────────────────────────────────────────────────


async def _skills_with_question(db: AsyncSession) -> tuple[list[str], Question]:
    db.add(Track(id="trkC3", name_es="T", name_en="T", order=1))
    db.add(Module(id="modC3", track_id="trkC3", name_es="M", name_en="M", order=0))
    for i in range(2):
        db.add(Skill(id=f"skC3_{i}", module_id="modC3", name_es="S", name_en="S", order=i))
    q = Question(
        id="qC3", skill_id="skC3_0", type="mcq", question_es="?", question_en="?",
        options_es=["a", "b"], options_en=["a", "b"], correct_index=0,
    )
    db.add(q)
    await db.commit()
    return ["skC3_0", "skC3_1"], q


async def _answer_in(db: AsyncSession, user: User, mode: str, q: Question) -> None:
    session = StudySession(user_id=user.id, mode=mode)
    db.add(session)
    await db.flush()
    db.add(Response(session_id=session.id, question_id=q.id, correct=True, grade=3, response_time_ms=1000))
    await db.commit()


class TestDktHistoryIgnoresPlacement:
    @pytest.mark.asyncio
    async def test_only_placement_answers_means_no_dkt_history(
        self, db_session: AsyncSession, user: User, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skills, q = await _skills_with_question(db_session)
        await _answer_in(db_session, user, "placement", q)
        seen: list[list[dict[str, object]]] = []
        monkeypatch.setattr(quiz, "get_cohort", lambda _uid: "dkt")
        monkeypatch.setattr(quiz._dkt, "predict", lambda h: seen.append(h) or {})

        _, reason = await _select_skill(db_session, user, skills)

        assert seen == []
        assert reason == "mastery_weighting"

    @pytest.mark.asyncio
    async def test_study_answers_still_feed_dkt(
        self, db_session: AsyncSession, user: User, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skills, q = await _skills_with_question(db_session)
        await _answer_in(db_session, user, "placement", q)
        await _answer_in(db_session, user, "study", q)
        seen: list[list[dict[str, object]]] = []
        monkeypatch.setattr(quiz, "get_cohort", lambda _uid: "dkt")
        monkeypatch.setattr(quiz._dkt, "predict", lambda h: seen.append(h) or {})

        await _select_skill(db_session, user, skills)

        assert seen == [[{"skill_id": "skC3_0", "correct": True}]]


# ── Duelo ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duel_item_without_correct_index_never_scores(
    client: AsyncClient, db_session: AsyncSession, user: User
) -> None:
    opponent = User(
        id=uuid.uuid4(),
        email=f"opp-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"opp{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Opp",
        language="es",
    )
    db_session.add(opponent)
    db_session.add(Track(id="trkDu", name_es="T", name_en="T", order=1))
    db_session.add(Module(id="modDu", track_id="trkDu", name_es="M", name_en="M", order=0))
    db_session.add(Skill(id="skDu", module_id="modDu", name_es="S", name_en="S", order=0))
    db_session.add(Question(
        id="qDuExec", skill_id="skDu", type="fill_blank_exec", question_es="?", question_en="?",
        correct_answer_es="42", correct_answer_en="42",
    ))
    duel = Duel(
        challenger_id=user.id, opponent_id=opponent.id, skill_id="skDu",
        question_ids=["qDuExec"], status="in_progress",
    )
    db_session.add(duel)
    await db_session.commit()

    r = await client.post(
        f"/api/v1/duels/{duel.id}/answer",
        json={"question_id": "qDuExec", "selected_index": 1, "response_time_ms": 900},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert r.status_code == 200, r.text

    await db_session.refresh(duel)
    assert duel.challenger_answers is not None
    assert duel.challenger_answers[0]["correct"] is False
