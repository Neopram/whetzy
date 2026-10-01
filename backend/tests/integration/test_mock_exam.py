"""Integration tests for the timed certification mock exam (10.3).

Routes under test:
  POST /api/v1/exams/mock/start
  POST /api/v1/exams/mock/{attempt_id}/submit
  GET  /api/v1/exams/mock/{attempt_id}

The properties that matter here are not "the endpoint returns 200". They are
that the question mix mirrors the published blueprint, that the clock belongs to
the server, that unanswered questions count as wrong, and that the report never
invents a scaled score - each of those is a way the exercise could quietly stop
resembling the real exam.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import Domain, Module, Question, Skill, Track
from app.models.exam import MockExamAttempt
from app.services import mock_exam as mock_exam_service

BASE = "/api/v1/exams"

# A miniature certification: 4 domains at the real CLF-C02 weights, but a
# 20-question exam so the fixture stays small. The weights are what is being
# tested, not the absolute counts.
_WEIGHTS = [("d1", 24.0), ("d2", 30.0), ("d3", 34.0), ("d4", 12.0)]
_EXAM_QUESTIONS = 20
_EXPECTED_MIX = {"d1": 5, "d2": 6, "d3": 7, "d4": 2}  # largest remainder, sums to 20


@pytest_asyncio.fixture
async def cert_seed(db_session: AsyncSession) -> dict:
    """A certification track with four weighted domains and plenty of questions."""
    track = Track(
        id="trk_cert",
        name_es="Certificacion de prueba",
        name_en="Test certification",
        order=99,
        is_certification=True,
        cert_provider="TestCorp",
        exam_question_count=_EXAM_QUESTIONS,
        exam_duration_minutes=90,
    )
    db_session.add(track)

    question_ids: list[str] = []
    for index, (suffix, weight) in enumerate(_WEIGHTS, start=1):
        domain = Domain(
            id=f"dom_{suffix}",
            track_id=track.id,
            name_es=f"Dominio {index}",
            name_en=f"Domain {index}",
            weight_pct=weight,
            order=index,
        )
        module = Module(
            id=f"mod_{suffix}", track_id=track.id, name_es=f"M{index}", name_en=f"M{index}", order=index
        )
        skill = Skill(
            id=f"sk_{suffix}",
            module_id=module.id,
            name_es=f"S{index}",
            name_en=f"S{index}",
            order=1,
            domain_id=domain.id,
        )
        db_session.add_all([domain, module, skill])
        # 12 questions per domain: comfortably more than any domain needs, so a
        # short draw means the allocation is wrong rather than the pool empty.
        for n in range(12):
            qid = f"q_{suffix}_{n:02d}"
            question_ids.append(qid)
            db_session.add(
                Question(
                    id=qid,
                    skill_id=skill.id,
                    type="mcq",
                    difficulty_tier="medium",
                    question_es=f"Pregunta {qid}",
                    question_en=f"Question {qid}",
                    options_es=["a", "b", "c", "d"],
                    options_en=["a", "b", "c", "d"],
                    # Answer position varies with n so a test that always picks
                    # index 0 cannot accidentally score 100 %.
                    correct_index=n % 4,
                    explanation_es="porque si",
                    explanation_en="because",
                    expected_time_ms=20000,
                    source="test fixture",
                )
            )
    await db_session.flush()
    return {"track_id": track.id, "question_ids": question_ids}


@pytest_asyncio.fixture
async def cert_seed_reserved(db_session: AsyncSession, cert_seed: dict) -> dict:
    """Marks 8 of `cert_seed`'s 12-per-domain questions "simulacro" — still
    comfortably more than any single domain's allocation (the largest is
    d3's 7 in `_EXPECTED_MIX`) and less than the full 12, so a test that
    forgets to filter draws from outside the reserved set too."""
    reserved_ids = [qid for qid in cert_seed["question_ids"] if int(qid.rsplit("_", 1)[1]) < 8]
    await db_session.execute(
        Question.__table__.update().where(Question.id.in_(reserved_ids)).values(pool="simulacro")
    )
    await db_session.commit()
    return {**cert_seed, "reserved_ids": set(reserved_ids)}


# ── 37.18: reserved mock-exam pool (ADR-53 §4) ──────────────────────────────


@pytest.mark.asyncio
async def test_reserved_pool_off_by_default_draws_the_full_bank(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed_reserved: dict
) -> None:
    assert settings.MOCK_EXAM_RESERVED_POOL_ENABLED is False
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed_reserved["track_id"]}, headers=auth_headers
    )
    assert res.status_code == 201, res.text
    drawn = {q["id"] for q in res.json()["questions"]}
    # With the flag off, marking half the bank "simulacro" must change nothing:
    # some drawn questions fall outside the reserved half.
    assert drawn - cert_seed_reserved["reserved_ids"], (
        "flag off must still draw from the whole bank, same as before 37.18"
    )


@pytest.mark.asyncio
async def test_reserved_pool_on_never_draws_outside_it(
    client: AsyncClient,
    auth_headers: dict[str, str],
    cert_seed_reserved: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "MOCK_EXAM_RESERVED_POOL_ENABLED", True)
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed_reserved["track_id"]}, headers=auth_headers
    )
    assert res.status_code == 201, res.text
    drawn = {q["id"] for q in res.json()["questions"]}
    assert drawn.issubset(cert_seed_reserved["reserved_ids"]), (
        f"drew outside the reserved pool: {drawn - cert_seed_reserved['reserved_ids']}"
    )


@pytest.mark.asyncio
async def test_reserved_pool_on_refuses_a_track_with_no_reserved_questions(
    client: AsyncClient,
    auth_headers: dict[str, str],
    cert_seed: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`cert_seed` (unlike `cert_seed_reserved`) marks nothing "simulacro" —
    the realistic state of every certification today. Turning the flag on
    must refuse cleanly (`MockExamError`, tested directly against the
    service in `test_start_rejects_a_non_certification_track`'s style of
    fixture), not silently serve a shorter or wrong exam."""
    monkeypatch.setattr(settings, "MOCK_EXAM_RESERVED_POOL_ENABLED", True)
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    assert res.status_code == 400, res.text
    assert "not enough questions" in res.json()["detail"]


# ── Question selection ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_draws_the_published_domain_mix(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict, db_session: AsyncSession
) -> None:
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert len(body["questions"]) == _EXAM_QUESTIONS

    mix: dict[str, int] = {}
    for question in body["questions"]:
        suffix = question["id"].split("_")[1]
        mix[suffix] = mix.get(suffix, 0) + 1
    assert mix == _EXPECTED_MIX, (
        "the question mix must mirror the published weights; an exam weighted "
        f"differently from the real one is not a rehearsal of it. Got {mix}"
    )


@pytest.mark.asyncio
async def test_start_never_reveals_the_correct_answer(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    for question in res.json()["questions"]:
        assert "correct_index" not in question
        assert "explanation_es" not in question


@pytest.mark.asyncio
async def test_start_rejects_a_non_certification_track(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
) -> None:
    db_session.add(Track(id="trk_plain", name_es="Normal", name_en="Plain", order=1))
    await db_session.flush()
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": "trk_plain"}, headers=auth_headers
    )
    assert res.status_code == 400
    assert "certification" in res.json()["detail"]


@pytest.mark.asyncio
async def test_start_refuses_rather_than_serving_a_short_exam(
    db_session: AsyncSession, cert_seed: dict, user
) -> None:
    """A domain without enough questions must fail loudly.

    Silently drawing fewer would make every score incomparable with the real
    exam, and nothing in the response would say so.
    """
    await db_session.execute(delete(Question).where(Question.skill_id == "sk_d3"))
    await db_session.flush()

    with pytest.raises(mock_exam_service.MockExamError) as err:
        await mock_exam_service.start_attempt(db_session, user, cert_seed["track_id"])
    assert "blueprint" in str(err.value)


@pytest.mark.asyncio
async def test_allocation_sums_to_the_exam_size() -> None:
    """Naive rounding of 24/30/34/12 over 65 gives 66, not 65."""
    weights = {"a": 24.0, "b": 30.0, "c": 34.0, "d": 12.0}
    allocation = mock_exam_service._domain_allocation(weights, 65)
    assert sum(allocation.values()) == 65
    assert allocation == {"a": 16, "b": 19, "c": 22, "d": 8}


@pytest.mark.asyncio
async def test_allocation_is_deterministic_for_the_same_weights() -> None:
    weights = {"a": 24.0, "b": 30.0, "c": 34.0, "d": 12.0}
    first = mock_exam_service._domain_allocation(weights, 65)
    second = mock_exam_service._domain_allocation(dict(reversed(list(weights.items()))), 65)
    assert first == second, "the split must not depend on dict ordering"


# ── Scoring ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unanswered_questions_count_as_incorrect(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    """The real exam scores blanks as wrong; excluding them would flatter."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    attempt_id = start.json()["attempt_id"]

    res = await client.post(
        f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert res.status_code == 200, res.text
    report = res.json()["report"]
    assert report["questions"] == _EXAM_QUESTIONS
    assert report["answered"] == 0
    assert report["unanswered"] == _EXAM_QUESTIONS
    assert report["correct"] == 0
    assert report["raw_pct"] == 0.0
    # The denominator is the whole exam, not the answered subset.
    assert sum(d["total"] for d in report["per_domain"]) == _EXAM_QUESTIONS


@pytest.mark.asyncio
async def test_report_scores_and_attributes_by_domain(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict, db_session: AsyncSession
) -> None:
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    body = start.json()
    ids = [q["id"] for q in body["questions"]]

    correct_by_id = {
        q.id: q.correct_index for q in await db_session.scalars(select(Question))
    }
    # Answer the first half correctly and the rest wrongly, so the totals are
    # something other than 0 or 100 - a report that only works at the extremes
    # would pass a laxer test.
    answers = []
    for position, qid in enumerate(ids):
        right = correct_by_id[qid]
        answers.append(
            {"question_id": qid, "selected_index": right if position < 10 else (right + 1) % 4}
        )

    res = await client.post(
        f"{BASE}/mock/{body['attempt_id']}/submit", json={"answers": answers}, headers=auth_headers
    )
    report = res.json()["report"]
    assert report["correct"] == 10
    assert report["answered"] == _EXAM_QUESTIONS
    assert report["raw_pct"] == 50.0
    assert sum(d["correct"] for d in report["per_domain"]) == 10
    assert {d["domain_id"] for d in report["per_domain"]} == {
        "dom_d1", "dom_d2", "dom_d3", "dom_d4"
    }
    for row in report["per_domain"]:
        assert row["correct"] <= row["total"]


@pytest.mark.asyncio
async def test_report_refuses_to_invent_a_scaled_score(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    """Red line 1: a number that looks official and is invented is worse than none."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    res = await client.post(
        f"{BASE}/mock/{start.json()['attempt_id']}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    report = res.json()["report"]
    for forbidden in ("scaled_score", "predicted_score", "pass_probability", "will_pass"):
        assert forbidden not in report, f"{forbidden} would be fabricated"
    # The note is present in both languages regardless of provider (red line 3).
    assert report["scoring_note_es"]
    assert report["scoring_note_en"]


@pytest_asyncio.fixture
async def aws_cert_seed(db_session: AsyncSession) -> dict:
    """Certification track with cert_provider='AWS' for provider-note tests."""
    track = Track(
        id="trk_aws",
        name_es="Certificacion AWS de prueba",
        name_en="AWS test certification",
        order=98,
        is_certification=True,
        cert_provider="AWS",
        exam_question_count=_EXAM_QUESTIONS,
        exam_duration_minutes=90,
    )
    db_session.add(track)
    for index, (suffix, weight) in enumerate(_WEIGHTS, start=1):
        domain = Domain(
            id=f"aws_dom_{suffix}",
            track_id=track.id,
            name_es=f"Dominio {index}",
            name_en=f"Domain {index}",
            weight_pct=weight,
            order=index,
        )
        module = Module(
            id=f"aws_mod_{suffix}",
            track_id=track.id,
            name_es=f"M{index}",
            name_en=f"M{index}",
            order=index,
        )
        skill = Skill(
            id=f"aws_sk_{suffix}",
            module_id=module.id,
            name_es=f"S{index}",
            name_en=f"S{index}",
            order=1,
            domain_id=domain.id,
        )
        db_session.add_all([domain, module, skill])
        for n in range(12):
            qid = f"aws_q_{suffix}_{n:02d}"
            db_session.add(
                Question(
                    id=qid,
                    skill_id=skill.id,
                    type="mcq",
                    difficulty_tier="medium",
                    question_es=f"Pregunta {qid}",
                    question_en=f"Question {qid}",
                    options_es=["a", "b", "c", "d"],
                    options_en=["a", "b", "c", "d"],
                    correct_index=n % 4,
                    explanation_es="porque si",
                    explanation_en="because",
                    source="test fixture",
                )
            )
    await db_session.commit()
    return {"track_id": track.id}


@pytest.mark.asyncio
async def test_aws_provider_note_mentions_700_scale(
    client: AsyncClient, auth_headers: dict[str, str], aws_cert_seed: dict
) -> None:
    """AWS has a documented 700/1000 scale; the note must explain it."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": aws_cert_seed["track_id"]}, headers=auth_headers
    )
    res = await client.post(
        f"{BASE}/mock/{start.json()['attempt_id']}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    report = res.json()["report"]
    assert "700" in report["scoring_note_es"]
    assert "700" in report["scoring_note_en"]


@pytest.mark.asyncio
async def test_non_aws_provider_note_does_not_mention_aws(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    """cert_seed uses cert_provider='TestCorp'; the generic note must not invent AWS text."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    res = await client.post(
        f"{BASE}/mock/{start.json()['attempt_id']}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    report = res.json()["report"]
    assert "AWS" not in report["scoring_note_es"]
    assert "AWS" not in report["scoring_note_en"]
    assert "700" not in report["scoring_note_es"]
    assert "700" not in report["scoring_note_en"]


@pytest.mark.asyncio
async def test_small_domains_are_flagged_as_too_small_to_judge(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    """Domain 4 is 12 % of the exam, so a handful of questions: the guide itself
    asks for caution reading section-level feedback."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    res = await client.post(
        f"{BASE}/mock/{start.json()['attempt_id']}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    rows = {d["domain_id"]: d for d in res.json()["report"]["per_domain"]}
    assert rows["dom_d4"]["total"] == 2
    assert rows["dom_d4"]["enough_questions_to_judge"] is False
    assert rows["dom_d4"]["weight_pct"] == 12.0


# ── The clock ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deadline_is_set_by_the_server_from_the_blueprint(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    body = res.json()
    started = datetime.fromisoformat(body["started_at"])
    expires = datetime.fromisoformat(body["expires_at"])
    assert body["duration_minutes"] == 90
    assert abs((expires - started) - timedelta(minutes=90)) < timedelta(seconds=2)


@pytest.mark.asyncio
async def test_a_late_submission_is_graded_but_marked_expired(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict, db_session: AsyncSession
) -> None:
    """Refusing to score it would lose the learner's work; hiding that it was
    late would let a score obtained past the deadline read as one within it."""
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    attempt_id = uuid.UUID(start.json()["attempt_id"])

    attempt = await db_session.get(MockExamAttempt, attempt_id)
    assert attempt is not None
    attempt.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.flush()

    res = await client.post(
        f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["expired"] is True
    assert res.json()["status"] == "expired"
    assert res.json()["report"]["questions"] == _EXAM_QUESTIONS


@pytest.mark.asyncio
async def test_an_attempt_cannot_be_submitted_twice(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    attempt_id = start.json()["attempt_id"]
    first = await client.post(
        f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert first.status_code == 200
    second = await client.post(
        f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=auth_headers
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_the_stored_report_is_returned_unchanged(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    attempt_id = start.json()["attempt_id"]
    submitted = await client.post(
        f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=auth_headers
    )
    reread = await client.get(f"{BASE}/mock/{attempt_id}", headers=auth_headers)
    assert reread.status_code == 200
    assert reread.json()["report"] == submitted.json()["report"]


@pytest.mark.asyncio
async def test_an_unsubmitted_attempt_has_no_report_to_read(
    client: AsyncClient, auth_headers: dict[str, str], cert_seed: dict
) -> None:
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    res = await client.get(f"{BASE}/mock/{start.json()['attempt_id']}", headers=auth_headers)
    assert res.status_code == 409


# ── Ownership ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_another_users_attempt_is_not_reachable(
    client: AsyncClient,
    auth_headers: dict[str, str],
    plus_auth_headers: dict[str, str],
    cert_seed: dict,
) -> None:
    start = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=auth_headers
    )
    attempt_id = start.json()["attempt_id"]

    for response in (
        await client.get(f"{BASE}/mock/{attempt_id}", headers=plus_auth_headers),
        await client.post(
            f"{BASE}/mock/{attempt_id}/submit", json={"answers": []}, headers=plus_auth_headers
        ),
    ):
        # 404 rather than 403: distinguishing them would confirm the attempt exists.
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_the_endpoints_require_authentication(
    client: AsyncClient, cert_seed: dict
) -> None:
    res = await client.post(f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]})
    assert res.status_code in (401, 403)


# ── Determinism of the draw ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_the_same_seed_draws_the_same_exam(
    db_session: AsyncSession, cert_seed: dict, user
) -> None:
    first = await mock_exam_service.start_attempt(
        db_session, user, cert_seed["track_id"], rng=random.Random(7)
    )
    second = await mock_exam_service.start_attempt(
        db_session, user, cert_seed["track_id"], rng=random.Random(7)
    )
    assert first.question_ids == second.question_ids


@pytest.mark.asyncio
async def test_different_sittings_draw_different_exams(
    db_session: AsyncSession, cert_seed: dict, user
) -> None:
    """Two sittings must not be the same 20 questions, or the second one only
    measures memory of the first."""
    first = await mock_exam_service.start_attempt(
        db_session, user, cert_seed["track_id"], rng=random.Random(1)
    )
    second = await mock_exam_service.start_attempt(
        db_session, user, cert_seed["track_id"], rng=random.Random(2)
    )
    assert set(first.question_ids) != set(second.question_ids)


@pytest.mark.asyncio
async def test_option_less_questions_are_never_drawn_into_an_exam(
    db_session: AsyncSession, cert_seed: dict, user
) -> None:
    """A `fill_blank` has no options, and the exam screen is a radiogroup.

    Drawn into a sitting it paints an empty radiogroup — nothing to click — and
    `_grade` still scores it as failed, so the candidate loses a mark on a
    question the product never let them answer. The draw has to exclude them at
    the source; the blueprint mix must survive the exclusion unchanged.
    """
    for suffix, _weight in _WEIGHTS:
        for n in range(6):
            db_session.add(
                Question(
                    id=f"qfb_{suffix}_{n:02d}",
                    skill_id=f"sk_{suffix}",
                    type="fill_blank",
                    difficulty_tier="medium",
                    question_es=f"El pilar de ___ reduce gastos ({n})",
                    question_en=f"The ___ pillar reduces spend ({n})",
                    options_es=None,
                    options_en=None,
                    correct_answer_es="coste",
                    correct_answer_en="cost",
                    explanation_es="porque si",
                    explanation_en="because",
                    expected_time_ms=20000,
                    source="test fixture",
                )
            )
    await db_session.flush()

    attempt = await mock_exam_service.start_attempt(
        db_session, user, cert_seed["track_id"], rng=random.Random(11)
    )

    drawn_without_options = [qid for qid in attempt.question_ids if qid.startswith("qfb_")]
    assert drawn_without_options == [], (
        "the exam drew questions it cannot render or score: "
        f"{drawn_without_options}"
    )

    mix: dict[str, int] = {}
    for qid in attempt.question_ids:
        mix[qid.split("_")[1]] = mix.get(qid.split("_")[1], 0) + 1
    assert mix == _EXPECTED_MIX
