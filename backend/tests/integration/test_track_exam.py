"""Integration tests for track final exams, test-out and certificates (17.2).

Routes under test:
  GET  /api/v1/exams/track/{track_id}/blueprint
  POST /api/v1/exams/track/{track_id}/start
  POST /api/v1/exams/module/{module_id}/test-out/start
  POST /api/v1/exams/track/{attempt_id}/submit
  GET  /api/v1/exams/certificates/{code}

What is worth testing here is not that the endpoints answer 200. It is the
handful of places where this feature could quietly start lying:

  - the exam size is derived from the track rather than fixed, so a certificate
    covers what it claims to cover;
  - passing a test-out raises mastery **by the evidence**, never by decree;
  - failing one does not push mastery down, so trying to skip ahead is not
    punished;
  - the pass mark is frozen into the attempt, so a config change cannot revoke
    yesterday's certificate;
  - a certificate is minted once and its public URL never goes dead;
  - the public verification endpoint leaks nothing beyond what a certificate is.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Module, Question, Skill, Track
from app.models.exam import Certificate, MockExamAttempt
from app.models.user import User, UserSkillState
from app.services import track_exam as track_exam_service

BASE = "/api/v1/exams"

# Three modules of 4, 3 and 3 skills = 10 skills. Below MIN_TRACK_EXAM_QUESTIONS
# (20), so the floor applies and the final is 20 questions. That is deliberate:
# it exercises the clamp as well as the allocation.
_MODULES = [("m1", 4), ("m2", 3), ("m3", 3)]
_SKILL_COUNT = sum(n for _, n in _MODULES)


@pytest_asyncio.fixture
async def track_seed(db_session: AsyncSession) -> dict:
    """A non-certification track with three modules and a deep question pool."""
    track = Track(
        id="trk_final",
        name_es="Pista de prueba",
        name_en="Test track",
        order=98,
        is_certification=False,
    )
    db_session.add(track)

    skill_ids: list[str] = []
    for index, (module_suffix, skill_count) in enumerate(_MODULES, start=1):
        module = Module(
            id=f"mod_{module_suffix}",
            track_id=track.id,
            name_es=f"Modulo {index}",
            name_en=f"Module {index}",
            order=index,
            min_mastery_to_unlock=0.7,
        )
        db_session.add(module)
        for s in range(skill_count):
            skill = Skill(
                id=f"sk_{module_suffix}_{s}",
                module_id=module.id,
                name_es=f"Skill {module_suffix}{s}",
                name_en=f"Skill {module_suffix}{s}",
                order=s,
            )
            skill_ids.append(skill.id)
            db_session.add(skill)
            # 15 per skill: far more than any blueprint needs, so a short draw
            # means the allocation is wrong rather than the pool being empty.
            for n in range(15):
                db_session.add(
                    Question(
                        id=f"q_{module_suffix}_{s}_{n:02d}",
                        skill_id=skill.id,
                        type="mcq",
                        difficulty_tier="medium",
                        question_es=f"Pregunta {module_suffix}{s}{n}",
                        question_en=f"Question {module_suffix}{s}{n}",
                        options_es=["a", "b", "c", "d"],
                        options_en=["a", "b", "c", "d"],
                        # Varies with n so a test that always picks index 0
                        # cannot accidentally score 100 %.
                        correct_index=n % 4,
                        explanation_es="porque si",
                        explanation_en="because",
                        expected_time_ms=20000,
                        source="test fixture",
                    )
                )
    await db_session.flush()
    return {"track_id": track.id, "skill_ids": skill_ids, "module_ids": [f"mod_{m}" for m, _ in _MODULES]}


async def _answers_for(
    db_session: AsyncSession, attempt_id: str, *, correct: bool | float
) -> list[dict]:
    """Builds a submission for an attempt.

    `correct=True` answers everything right, `False` everything wrong, and a
    float answers that fraction of the paper correctly.
    """
    attempt = await db_session.get(MockExamAttempt, uuid.UUID(attempt_id))
    assert attempt is not None
    questions = (
        await db_session.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
    ).all()
    by_id = {q.id: q for q in questions}

    total = len(attempt.question_ids)
    if correct is True:
        right_count = total
    elif correct is False:
        right_count = 0
    else:
        right_count = int(total * correct)

    answers = []
    for index, question_id in enumerate(attempt.question_ids):
        question = by_id[question_id]
        if index < right_count:
            chosen = question.correct_index
        else:
            chosen = (question.correct_index + 1) % 4
        answers.append({"question_id": question_id, "selected_index": chosen})
    return answers


# ── Blueprint ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blueprint_is_derived_from_the_track(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict
) -> None:
    res = await client.get(f"{BASE}/track/{track_seed['track_id']}/blueprint", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["skills"] == _SKILL_COUNT
    # 10 skills would be 10 questions, but the floor is 20.
    assert body["questions"] == track_exam_service.MIN_TRACK_EXAM_QUESTIONS
    # 20 questions * 90 s = 30 min exactly.
    assert body["duration_minutes"] == 30
    assert body["pass_pct"] == track_exam_service.DEFAULT_PASS_PCT


def test_blueprint_size_scales_with_skills_between_the_bounds() -> None:
    """The size has to actually track the track, or the clamp is the whole rule."""
    size = track_exam_service.blueprint_size
    assert size(3, minimum=20, maximum=50) == 20, "floor applies to a tiny track"
    assert size(31, minimum=20, maximum=50) == 31, "one question per skill in between"
    assert size(52, minimum=20, maximum=50) == 50, "ceiling applies to track01"


def test_allocation_always_sums_to_the_total() -> None:
    """Largest-remainder, so an exam is never one question short of its blueprint."""
    for total in range(5, 60):
        allocation = track_exam_service.allocate({"a": 4, "b": 3, "c": 3}, total)
        assert sum(allocation.values()) == total, f"drifted at total={total}"


def test_test_out_asks_enough_per_skill_to_clear_the_unlock_bar() -> None:
    """The per-skill count is read off the BKT curve, not chosen.

    This is the test that makes the number defensible: if the engine's learn
    rate ever changes so that two correct answers no longer clear 0.70, this
    fails and the blueprint has to be resized — rather than the product quietly
    shipping a test-out that unlocks nothing.
    """
    from app.services.engine import BKTModel, SkillState

    per_skill = track_exam_service.test_out_questions_per_skill(4)
    assert per_skill >= track_exam_service.TEST_OUT_QUESTIONS_PER_SKILL

    bkt = BKTModel()
    state = SkillState(skill_id="x", p_known=0.1, attempts=0, correct=0)
    for _ in range(per_skill):
        bkt.update(state, True)
    assert state.p_known >= 0.7, (
        f"{per_skill} correct answers take a cold skill to {state.p_known:.2f}, "
        "which is below the default min_mastery_to_unlock of 0.70 - passing a "
        "test-out would leave the module locked"
    )

    # Small modules get more per skill so the sitting is not a formality...
    assert track_exam_service.test_out_questions_per_skill(2) == 4
    assert track_exam_service.test_out_questions_per_skill(1) == 8
    # ...and large ones are never capped into under-sampling a skill.
    assert track_exam_service.test_out_questions_per_skill(15) == 2


def test_duration_rounds_up_to_whole_five_minutes() -> None:
    assert track_exam_service.duration_minutes_for(20) == 30
    assert track_exam_service.duration_minutes_for(21) == 35  # 31.5 min -> 35
    assert track_exam_service.duration_minutes_for(50) == 75


# ── Starting a track final ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_draws_the_blueprint_spread_across_modules(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict
) -> None:
    res = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert len(body["questions"]) == track_exam_service.MIN_TRACK_EXAM_QUESTIONS
    assert body["kind"] == track_exam_service.KIND_TRACK_FINAL
    assert body["module_id"] is None

    mix: dict[str, int] = {}
    for question in body["questions"]:
        module_suffix = question["id"].split("_")[1]
        mix[module_suffix] = mix.get(module_suffix, 0) + 1
    # 4:3:3 skills over 20 questions -> 8:6:6 by largest remainder.
    assert mix == {"m1": 8, "m2": 6, "m3": 6}, (
        "the draw must be spread in proportion to each module's skills, or the "
        f"certificate over-tests some modules and skips others. Got {mix}"
    )


@pytest.mark.asyncio
async def test_start_never_reveals_the_correct_answer(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict
) -> None:
    res = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    for question in res.json()["questions"]:
        assert "correct_index" not in question
        assert "explanation_es" not in question


@pytest.mark.asyncio
async def test_certification_track_is_refused_here(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
) -> None:
    """A published blueprint must not be replaced by our invented one."""
    db_session.add(
        Track(
            id="trk_is_cert",
            name_es="Cert",
            name_en="Cert",
            order=97,
            is_certification=True,
            exam_question_count=65,
            exam_duration_minutes=90,
        )
    )
    await db_session.flush()
    res = await client.post(f"{BASE}/track/trk_is_cert/start", headers=auth_headers)
    assert res.status_code == 400
    assert "certification track" in res.json()["detail"]


# ── Grading ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unanswered_counts_as_incorrect(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    start = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=True)

    # Submit only half the paper, all of it right.
    half = answers[: len(answers) // 2]
    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": half}, headers=auth_headers
    )
    assert res.status_code == 200, res.text
    report = res.json()["report"]
    assert report["answered"] == len(half)
    assert report["unanswered"] == len(answers) - len(half)
    assert report["correct"] == len(half)
    assert report["raw_pct"] == 50.0
    assert report["passed"] is False


@pytest.mark.asyncio
async def test_pass_mark_is_frozen_into_the_attempt(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """A later change to the threshold must not revoke a pass already earned."""
    start = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    assert start.json()["pass_pct"] == 70.0

    # The track's policy changes mid-sitting to something the learner cannot meet.
    track = await db_session.get(Track, track_seed["track_id"])
    assert track is not None
    track.passing_score_pct = 99.0
    await db_session.flush()

    answers = await _answers_for(db_session, attempt_id, correct=0.8)
    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    report = res.json()["report"]
    assert report["pass_pct"] == 70.0, "the attempt's own bar, not today's config"
    assert report["raw_pct"] == 80.0
    assert report["passed"] is True


@pytest.mark.asyncio
async def test_late_submission_is_graded_but_marked_expired(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    start = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]

    attempt = await db_session.get(MockExamAttempt, uuid.UUID(attempt_id))
    assert attempt is not None
    attempt.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.flush()

    answers = await _answers_for(db_session, attempt_id, correct=True)
    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["expired"] is True
    assert body["status"] == "expired"
    # Graded rather than discarded - the work was done - but never cashed in.
    assert body["report"]["raw_pct"] == 100.0
    assert body["certificate"] is None, "an expired sitting must not earn a certificate"


@pytest.mark.asyncio
async def test_an_attempt_cannot_be_submitted_twice(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    start = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=True)

    first = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert first.status_code == 200
    second = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_another_users_attempt_is_a_404_not_a_403(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """Telling the two apart would let anyone enumerate other people's sittings."""
    stranger = User(
        id=uuid.uuid4(),
        username="stranger",
        email="stranger@example.com",
        hashed_password="x",
        display_name="Stranger",
    )
    db_session.add(stranger)
    attempt = MockExamAttempt(
        id=uuid.uuid4(),
        user_id=stranger.id,
        track_id=track_seed["track_id"],
        kind=track_exam_service.KIND_TRACK_FINAL,
        question_ids=[],
        duration_minutes=30,
        pass_pct=70.0,
        started_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db_session.add(attempt)
    await db_session.flush()

    res = await client.post(
        f"{BASE}/track/{attempt.id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert res.status_code == 404


# ── Test-out ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_test_out_is_scoped_to_its_module(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict
) -> None:
    module_id = track_seed["module_ids"][0]  # m1, 4 skills
    res = await client.post(f"{BASE}/module/{module_id}/test-out/start", headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["kind"] == track_exam_service.KIND_TEST_OUT
    assert body["module_id"] == module_id
    # 4 skills x 2 questions each. Two is the floor because one question can
    # never lift a cold skill past the 0.70 unlock bar (see the BKT curve in
    # services/track_exam.py), which would make passing unlock nothing.
    assert len(body["questions"]) == 8
    assert all(q["id"].split("_")[1] == "m1" for q in body["questions"]), (
        "a test-out must only ask about the module it lets you skip"
    )
    per_skill: dict[str, int] = {}
    for question in body["questions"]:
        _, _module_suffix, skill_index, _ = question["id"].split("_")
        per_skill[skill_index] = per_skill.get(skill_index, 0) + 1
    assert sorted(per_skill) == ["0", "1", "2", "3"], "every skill must be asked about"
    assert set(per_skill.values()) == {2}, (
        "each skill needs the same, sufficient number of questions; drawing at "
        f"random across the module leaves some unprovable. Got {per_skill}"
    )
    # The bar to skip a module is the bar the module sets to count as unlocked.
    assert body["pass_pct"] == 70.0


@pytest.mark.asyncio
async def test_passing_a_test_out_raises_mastery_by_the_evidence(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict,
    db_session: AsyncSession, user: User,
) -> None:
    """The whole point of 17.2's honesty: earned, not granted.

    Mastery must clear the module's unlock bar for the skills that were actually
    tested, and stay untouched for the ones the draw never reached.
    """
    module_id = track_seed["module_ids"][0]
    start = await client.post(f"{BASE}/module/{module_id}/test-out/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=True)

    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["report"]["passed"] is True
    assert body["mastery_updated"], "a passed test-out must move the engine"

    tested_skills = set(body["mastery_updated"])
    states = (
        await db_session.scalars(
            select(UserSkillState).where(UserSkillState.user_id == user.id)
        )
    ).all()
    by_skill = {s.skill_id: s.p_known for s in states}

    for skill_id in tested_skills:
        assert by_skill[skill_id] >= 0.7, (
            f"{skill_id} was answered correctly throughout and still sits at "
            f"{by_skill[skill_id]:.2f}, below the module's unlock bar - the "
            "test-out did not actually let the learner out"
        )
        assert by_skill[skill_id] <= 1.0

    # Skills in other modules must be untouched: this test-out said nothing
    # about them.
    other_module_skills = [s for s in track_seed["skill_ids"] if not s.startswith("sk_m1")]
    for skill_id in other_module_skills:
        assert skill_id not in by_skill, (
            f"{skill_id} belongs to another module and gained state from a "
            "test-out that never asked about it"
        )


@pytest.mark.asyncio
async def test_failing_a_test_out_does_not_touch_mastery(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict,
    db_session: AsyncSession, user: User,
) -> None:
    """Trying to skip ahead and failing must not cost you mastery you had."""
    module_id = track_seed["module_ids"][0]
    start = await client.post(f"{BASE}/module/{module_id}/test-out/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=False)

    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    body = res.json()
    assert body["report"]["passed"] is False
    assert body["mastery_updated"] == {}

    states = (
        await db_session.scalars(
            select(UserSkillState).where(UserSkillState.user_id == user.id)
        )
    ).all()
    assert states == [], "a failed test-out must leave the learner exactly as it found them"


@pytest.mark.asyncio
async def test_test_out_earns_no_certificate(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """Skipping a module is not finishing a track."""
    module_id = track_seed["module_ids"][0]
    start = await client.post(f"{BASE}/module/{module_id}/test-out/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=True)

    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert res.json()["certificate"] is None


# ── Certificates ─────────────────────────────────────────────────────────────


async def _pass_the_track(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession, track_id: str
) -> dict:
    start = await client.post(f"{BASE}/track/{track_id}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=True)
    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_passing_the_final_issues_a_certificate(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    body = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    certificate = body["certificate"]
    assert certificate is not None
    assert certificate["track_id"] == track_seed["track_id"]
    assert certificate["score_pct"] == 100.0
    assert certificate["questions"] == track_exam_service.MIN_TRACK_EXAM_QUESTIONS
    assert certificate["revoked"] is False
    assert len(certificate["code"]) == 32, "128 bits, or the codes are guessable"


@pytest.mark.asyncio
async def test_failing_the_final_issues_nothing(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    start = await client.post(f"{BASE}/track/{track_seed['track_id']}/start", headers=auth_headers)
    attempt_id = start.json()["attempt_id"]
    answers = await _answers_for(db_session, attempt_id, correct=0.5)
    res = await client.post(
        f"{BASE}/track/{attempt_id}/submit", json={"answers": answers}, headers=auth_headers
    )
    assert res.json()["report"]["passed"] is False
    assert res.json()["certificate"] is None


@pytest.mark.asyncio
async def test_resitting_a_passed_track_keeps_the_same_certificate(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """A URL someone put on their CV must not go dead because they practised again."""
    first = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    second = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    assert first["certificate"]["code"] == second["certificate"]["code"]

    minted = (await db_session.scalars(select(Certificate))).all()
    assert len(minted) == 1


@pytest.mark.asyncio
async def test_certificate_verifies_without_authentication(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict,
    db_session: AsyncSession, user: User,
) -> None:
    """An employer checking a certificate does not have an account here."""
    body = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    code = body["certificate"]["code"]

    res = await client.get(f"{BASE}/certificates/{code}")  # no headers on purpose
    assert res.status_code == 200, res.text
    public = res.json()
    assert public["username"] == user.username
    assert public["track_name_es"] == "Pista de prueba"
    assert public["track_name_en"] == "Test track"
    assert public["score_pct"] == 100.0


@pytest.mark.asyncio
async def test_public_certificate_leaks_nothing_beyond_the_claim(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """The page is public, so what it carries is a privacy decision (red line 5)."""
    body = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    res = await client.get(f"{BASE}/certificates/{body['certificate']['code']}")
    public = res.json()

    assert set(public) == {
        "code",
        "username",
        "track_id",
        "track_name_es",
        "track_name_en",
        "score_pct",
        "questions",
        "issued_at",
        "revoked",
    }
    serialised = res.text
    assert "@" not in serialised, "no email may reach an unauthenticated page"
    assert str(body["attempt_id"]) not in serialised
    assert "user_id" not in public


@pytest.mark.asyncio
async def test_unknown_certificate_code_is_404(client: AsyncClient) -> None:
    res = await client.get(f"{BASE}/certificates/{'0' * 32}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_revoked_certificate_still_resolves_and_says_so(
    client: AsyncClient, auth_headers: dict[str, str], track_seed: dict, db_session: AsyncSession
) -> None:
    """A 404 cannot be told apart from a code that never existed."""
    body = await _pass_the_track(client, auth_headers, db_session, track_seed["track_id"])
    code = body["certificate"]["code"]

    certificate = (
        await db_session.scalars(select(Certificate).where(Certificate.code == code))
    ).first()
    assert certificate is not None
    certificate.revoked = True
    await db_session.flush()

    res = await client.get(f"{BASE}/certificates/{code}")
    assert res.status_code == 200
    assert res.json()["revoked"] is True


# ── Cross-wiring with the certification mock ─────────────────────────────────


@pytest.mark.asyncio
async def test_a_certification_mock_cannot_be_submitted_to_the_track_route(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession, user: User
) -> None:
    """The two report shapes are different; mixing them would score nonsense."""
    db_session.add(Track(id="trk_x", name_es="X", name_en="X", order=96, is_certification=True))
    attempt = MockExamAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        track_id="trk_x",
        kind="certification",
        question_ids=[],
        duration_minutes=90,
        started_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=90),
    )
    db_session.add(attempt)
    await db_session.flush()

    res = await client.post(
        f"{BASE}/track/{attempt.id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert res.status_code == 400
    assert "certification mock" in res.json()["detail"]
