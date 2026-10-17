"""43.5 (ADR-65 D7, H.60 decidida por el dueño el 2026-10-17).

La práctica de una skill exige su lección vista, salvo que el módulo se haya
superado por test-out o haya empezado con ventaja en la prueba de nivel
(≥ 70 % de ≥ 2 preguntas, la regla de 43.3). Ni la prueba ni el test-out
marcan la lección como vista.

Antes `UserSkillState.attempts > 0` contaba como lección vista, así que
contestar la prueba de nivel ya desbloqueaba la práctica de cualquier skill
que saliera en ella (choque D4/D7). El historial anterior al 2026-09-27, que
era lo que cubría esa regla, se rellena en la migración
`20261017_lesson_backfill`.
"""

from __future__ import annotations

import uuid

from app.models.content import Module, Question, Skill, Track
from app.models.exam import MockExamAttempt
from app.models.lesson_completion import LessonCompletion
from app.models.session import Response, StudySession
from app.models.user import UserSkillState
from app.services import lesson_gate


async def _track(db) -> None:
    db.add(Track(id="lp", name_es="LP", name_en="LP", order=96, icon="x", color="#000", total_questions=0))
    for m in (1, 2):
        db.add(Module(id=f"lp_m{m}", track_id="lp", name_es="M", name_en="M", order=m,
                      description_es="", description_en=""))
        for s in (1, 2):
            sid = f"lp_m{m}s{s}"
            db.add(Skill(id=sid, module_id=f"lp_m{m}", name_es=sid, name_en=sid, order=s))
            for i in range(2):
                db.add(Question(
                    id=f"{sid}_q{i}", skill_id=sid, type="mcq", difficulty_tier="medium",
                    question_es="P", question_en="Q", options_es=["a", "b"], options_en=["a", "b"],
                    correct_index=0, explanation_es="e", explanation_en="e", source="t",
                    elo_rating=1500.0,
                ))
    await db.commit()


SKILLS = ["lp_m1s1", "lp_m1s2", "lp_m2s1", "lp_m2s2"]


async def test_practicar_ya_no_cuenta_como_leccion_vista(db_session, user):
    await _track(db_session)
    db_session.add(UserSkillState(user_id=user.id, skill_id="lp_m1s1", attempts=3, correct_count=3))
    await db_session.commit()
    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == set()


async def test_la_leccion_vista_desbloquea_solo_su_skill(db_session, user):
    await _track(db_session)
    await lesson_gate.record_lesson_seen(db_session, user.id, "lp_m1s1")
    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == {"lp_m1s1"}
    assert await lesson_gate.lesson_viewed_skill_ids(db_session, user.id, SKILLS) == {"lp_m1s1"}


async def test_un_test_out_aprobado_desbloquea_el_modulo_sin_marcar_lecciones(db_session, user):
    await _track(db_session)
    from datetime import UTC, datetime, timedelta

    for passed, module in ((True, "lp_m1"), (False, "lp_m2")):
        db_session.add(MockExamAttempt(
            user_id=user.id, track_id="lp", kind="test_out", module_id=module,
            question_ids=[], duration_minutes=10, status="submitted",
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            report={"passed": passed},
        ))
    await db_session.commit()
    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == {"lp_m1s1", "lp_m1s2"}
    assert await lesson_gate.lesson_viewed_skill_ids(db_session, user.id, SKILLS) == set()


async def test_un_modulo_con_ventaja_en_la_prueba_desbloquea_sin_marcar_lecciones(db_session, user):
    await _track(db_session)
    session = StudySession(user_id=user.id, mode="placement")
    db_session.add(session)
    await db_session.flush()
    # Módulo 1: 2 de 2 (ventaja). Módulo 2: 1 de 2 (no).
    for qid, ok in (("lp_m1s1_q0", True), ("lp_m1s2_q0", True), ("lp_m2s1_q0", True), ("lp_m2s2_q0", False)):
        db_session.add(Response(session_id=session.id, question_id=qid, correct=ok,
                                grade=4 if ok else 1, response_time_ms=500))
    from datetime import UTC, datetime

    session.ended_at = datetime.now(UTC)
    await db_session.commit()

    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == {"lp_m1s1", "lp_m1s2"}
    assert await lesson_gate.lesson_viewed_skill_ids(db_session, user.id, SKILLS) == set()


async def test_una_prueba_sin_terminar_no_desbloquea(db_session, user):
    await _track(db_session)
    session = StudySession(user_id=user.id, mode="placement")
    db_session.add(session)
    await db_session.flush()
    for qid in ("lp_m1s1_q0", "lp_m1s2_q0"):
        db_session.add(Response(session_id=session.id, question_id=qid, correct=True, grade=4,
                                response_time_ms=500))
    await db_session.commit()
    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == set()


async def test_lo_de_otro_usuario_no_cuenta(db_session, user):
    await _track(db_session)
    other = uuid.uuid4()
    db_session.add(LessonCompletion(user_id=other, skill_id="lp_m1s1"))
    await db_session.commit()
    assert await lesson_gate.practice_unlocked_skill_ids(db_session, user.id, SKILLS) == set()
