"""Final exams for the non-certification tracks, and module test-out (17.2).

`mock_exam.py` rehearses a *real* exam that exists in the world: its blueprint,
its clock and its pass mark are published by AWS, and our job is to mirror them
without inventing anything. Here there is no external exam to mirror. The
blueprint is ours, so the honesty problem is the opposite one: every number has
to be derived from something defensible and stated out loud, or the certificate
at the end means nothing.

Three decisions, each of which could have been faked and is not:

**The size of the exam is derived from the track, not chosen.** One question per
skill, so a 24-skill track sits 24 questions and a 52-skill track sits 50 (the
cap). A fixed "30 questions for every track" would mean the track01 certificate
covers a third of what it claims and the track05 one over-tests. The allocation
across modules uses largest-remainder, so the parts sum to exactly the total
instead of drifting by one or two.

**Test-out does not grant mastery.** Duolingo's test-out skips the unit; the
temptation is to write `p_known = 1.0` for every skill in the module and move
on. That is red line 1 with extra steps: it would put "100 % dominado" on a
screen for a skill the learner may never have been asked about. Instead every
answer is fed through **the same BKT/Elo/FSRS update a quiz answer gets**
(`quiz.apply_exam_evidence`), so passing a test-out raises mastery exactly as
far as the evidence supports and not one point further. A learner who answers
all 15 correctly ends up above the module's `min_mastery_to_unlock` on the
skills that were actually tested, which *is* the test-out — earned, not granted.
Skills the draw never touched keep the mastery they had.

**The pass mark is frozen into the attempt.** `pass_pct` is copied onto the row
at start. If a later session decides 70 % was too lenient, yesterday's passes
stay passes: a certificate that can be revoked retroactively by a config change
is not a certificate.
"""

from __future__ import annotations

import random
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Module, Question, Skill, Track
from app.models.exam import Certificate, MockExamAttempt
from app.models.user import User

# One question per skill, bounded at both ends. The floor keeps a small module's
# test-out from being decided by four questions; the ceiling keeps track01's 52
# skills from becoming a 52-question sitting nobody finishes in one go.
QUESTIONS_PER_SKILL = 1
MIN_TRACK_EXAM_QUESTIONS = 20
MAX_TRACK_EXAM_QUESTIONS = 50

# A test-out is sized per *skill*, not per module, and the number is not a
# preference — it is read off the BKT curve the engine actually runs. From a
# cold skill (p_known 0.10), consecutive correct answers give:
#
#     1 correct -> 0.43      2 correct -> 0.78      3 correct -> 0.94
#
# The module unlock bar is `min_mastery_to_unlock`, 0.70 by default. So a
# test-out that asks **one** question per skill cannot lift a cold skill past
# the bar no matter how well it is answered: the learner passes the exam, the
# module stays locked, and the feature is theatre. Two is the smallest number
# that makes passing mean what the screen says it means.
#
# This was not reasoned out in advance — the first version drew questions at
# random across the module, some skills got one and some got three, and the test
# that asserts a passed test-out actually unlocks the module caught it.
TEST_OUT_QUESTIONS_PER_SKILL = 2
MIN_TEST_OUT_QUESTIONS = 8

# 90 seconds per question, rounded up to a whole multiple of 5 minutes so the
# clock the learner sees is a round number.
SECONDS_PER_QUESTION = 90

DEFAULT_PASS_PCT = 70.0

KIND_TRACK_FINAL = "track_final"
KIND_TEST_OUT = "test_out"
KIND_CERTIFYING = "certifying"
# Sittings that earn a certificate when passed on time: a track final, and the
# paid certifying exam of a certification track (38.7, `services/certification`).
CERTIFYING_KINDS = frozenset({KIND_TRACK_FINAL, KIND_CERTIFYING})


class TrackExamError(Exception):
    """Raised for conditions the caller should turn into a 4xx response."""


def _as_utc(moment: datetime) -> datetime:
    """SQLite hands back naive datetimes where Postgres hands back aware ones."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def blueprint_size(skill_count: int, *, minimum: int, maximum: int) -> int:
    """How many questions a unit of `skill_count` skills is worth."""
    return max(minimum, min(maximum, skill_count * QUESTIONS_PER_SKILL))


def test_out_questions_per_skill(skill_count: int) -> int:
    """Questions each skill is asked in a test-out of `skill_count` skills.

    Never below `TEST_OUT_QUESTIONS_PER_SKILL`, and raised further only to reach
    `MIN_TEST_OUT_QUESTIONS` on a module small enough that two-per-skill would
    make the whole thing a four-question formality. There is no ceiling on the
    total on purpose: skipping a fifteen-skill module *should* mean answering
    thirty questions. Capping it would mean under-sampling some skill, and an
    under-sampled skill is one the learner gets credited for without evidence.
    """
    if skill_count <= 0:
        return TEST_OUT_QUESTIONS_PER_SKILL
    needed = -(-MIN_TEST_OUT_QUESTIONS // skill_count)  # ceil
    return max(TEST_OUT_QUESTIONS_PER_SKILL, needed)


def duration_minutes_for(question_count: int) -> int:
    """Clock for a sitting, rounded up to the next whole 5 minutes."""
    raw = question_count * SECONDS_PER_QUESTION / 60
    return int(-(-raw // 5) * 5)


def allocate(weights: dict[str, int], total: int) -> dict[str, int]:
    """Splits `total` across keys in proportion to `weights`, summing exactly.

    Largest-remainder, ties broken by key so the split is deterministic instead
    of dependent on dict ordering — two sittings of the same exam should be
    drawn from the same shape.
    """
    pool = sum(weights.values())
    if pool <= 0:
        return {key: 0 for key in weights}
    exact = {key: total * value / pool for key, value in weights.items()}
    allocation = {key: int(value) for key, value in exact.items()}
    remainder = total - sum(allocation.values())
    by_fraction = sorted(exact, key=lambda k: (-(exact[k] - int(exact[k])), k))
    for key in by_fraction[:remainder]:
        allocation[key] += 1
    return allocation


async def _answerable_questions_by_skill(
    db: AsyncSession, skill_ids: list[str]
) -> dict[str, list[str]]:
    """Option-bearing questions per skill.

    Same rule as the certification mock, and for the same reason: the exam
    screen renders a radiogroup and scores by `correct_index`, so a `fill_blank`
    pulled into an exam paints an empty radiogroup that cannot be answered and
    is then counted wrong. Both languages must carry options, or the same exam
    would be sittable in Spanish and not in English (red line 3).
    """
    rows = (
        await db.execute(
            select(Question.skill_id, Question.id, Question.options_es, Question.options_en).where(
                Question.skill_id.in_(skill_ids)
            )
        )
    ).all()
    pool: dict[str, list[str]] = {}
    for skill_id, question_id, options_es, options_en in rows:
        if not options_es or not options_en:
            continue
        pool.setdefault(str(skill_id), []).append(str(question_id))
    # Sorted so a seeded RNG draws the same exam twice — the tests depend on it,
    # and so does being able to reproduce a learner's sitting from its seed.
    for question_ids in pool.values():
        question_ids.sort()
    return pool


async def _draw(
    db: AsyncSession,
    skills_by_group: dict[str, list[str]],
    total: int,
    picker: random.Random,
) -> list[str]:
    """Draws `total` questions spread across groups in proportion to their skills."""
    all_skill_ids = [skill_id for group in skills_by_group.values() for skill_id in group]
    pool = await _answerable_questions_by_skill(db, all_skill_ids)

    per_group = allocate({group: len(skills) for group, skills in skills_by_group.items()}, total)

    selected: list[str] = []
    short: list[str] = []
    for group, want in sorted(per_group.items()):
        available = [qid for skill_id in skills_by_group[group] for qid in pool.get(skill_id, [])]
        if len(available) < want:
            short.append(f"{group}: {len(available)} available, {want} needed")
            continue
        selected.extend(picker.sample(sorted(available), want))

    if short:
        # Quietly serving a shorter exam would make the certificate at the end
        # claim coverage the sitting never had.
        raise TrackExamError(
            "not enough answerable questions to fill the blueprint — " + "; ".join(short)
        )

    picker.shuffle(selected)
    return selected


async def start_track_final(
    db: AsyncSession,
    user: User,
    track_id: str,
    *,
    rng: random.Random | None = None,
) -> MockExamAttempt:
    """Starts the final exam for a non-certification track."""
    track = await db.get(Track, track_id)
    if track is None:
        raise TrackExamError(f"{track_id} does not exist")
    if track.is_certification:
        # Certification tracks have a published blueprint and their own clock;
        # routing them here would quietly replace it with our invented one.
        raise TrackExamError(
            f"{track_id} is a certification track — use POST /exams/mock/start, "
            "which mirrors the real exam blueprint"
        )

    modules = (
        await db.scalars(select(Module).where(Module.track_id == track_id).order_by(Module.order))
    ).all()
    if not modules:
        raise TrackExamError(f"{track_id} has no modules")

    skills_by_module: dict[str, list[str]] = {}
    for module in modules:
        skill_ids = list(
            await db.scalars(select(Skill.id).where(Skill.module_id == module.id).order_by(Skill.order))
        )
        if skill_ids:
            skills_by_module[module.id] = skill_ids
    if not skills_by_module:
        raise TrackExamError(f"{track_id} has no skills")

    skill_count = sum(len(s) for s in skills_by_module.values())
    total = blueprint_size(
        skill_count, minimum=MIN_TRACK_EXAM_QUESTIONS, maximum=MAX_TRACK_EXAM_QUESTIONS
    )
    picker = rng or random.Random()
    selected = await _draw(db, skills_by_module, total, picker)

    return await _persist_attempt(
        db,
        user=user,
        track_id=track_id,
        module_id=None,
        kind=KIND_TRACK_FINAL,
        question_ids=selected,
        pass_pct=track.passing_score_pct or DEFAULT_PASS_PCT,
    )


async def start_test_out(
    db: AsyncSession,
    user: User,
    module_id: str,
    *,
    rng: random.Random | None = None,
) -> MockExamAttempt:
    """Starts a module test-out: pass it and the module's skills count as shown."""
    module = await db.get(Module, module_id)
    if module is None:
        raise TrackExamError(f"{module_id} does not exist")

    skill_ids = list(
        await db.scalars(select(Skill.id).where(Skill.module_id == module_id).order_by(Skill.order))
    )
    if not skill_ids:
        raise TrackExamError(f"{module_id} has no skills")

    per_skill = test_out_questions_per_skill(len(skill_ids))
    total = per_skill * len(skill_ids)
    picker = rng or random.Random()
    # Grouped by **skill**, not by module. Drawing `total` at random from the
    # module's pool would leave some skills with one question and others with
    # three, and a skill asked once can never clear the unlock bar (see the
    # BKT curve above) — so passing would unlock some skills and silently not
    # others, which is the worst of both.
    selected = await _draw(db, {skill_id: [skill_id] for skill_id in skill_ids}, total, picker)

    return await _persist_attempt(
        db,
        user=user,
        track_id=module.track_id,
        module_id=module_id,
        kind=KIND_TEST_OUT,
        question_ids=selected,
        # The bar to skip a module is the bar the module itself sets to count as
        # unlocked, expressed as a percentage.
        pass_pct=round(module.min_mastery_to_unlock * 100, 1),
    )


async def _persist_attempt(
    db: AsyncSession,
    *,
    user: User,
    track_id: str,
    module_id: str | None,
    kind: str,
    question_ids: list[str],
    pass_pct: float,
) -> MockExamAttempt:
    duration = duration_minutes_for(len(question_ids))
    now = datetime.now(UTC)
    attempt = MockExamAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        track_id=track_id,
        module_id=module_id,
        kind=kind,
        question_ids=question_ids,
        duration_minutes=duration,
        pass_pct=pass_pct,
        started_at=now,
        expires_at=now + timedelta(minutes=duration),
        status="in_progress",
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def score_attempt(
    db: AsyncSession,
    attempt: MockExamAttempt,
    answers: dict[str, int],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Grades a sitting and reports per skill.

    Unanswered counts as incorrect. There is no per-domain breakdown here
    because non-certification tracks have no domains; the useful breakdown for
    a learner is per skill, which is also the unit the engine reasons in.
    """
    moment = now or datetime.now(UTC)
    questions = (
        await db.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
    ).all()
    by_id = {q.id: q for q in questions}

    skill_ids = sorted({q.skill_id for q in questions})
    skills = (await db.scalars(select(Skill).where(Skill.id.in_(skill_ids)))).all()
    skill_by_id = {s.id: s for s in skills}

    tally: dict[str, list[int]] = {skill_id: [0, 0] for skill_id in skill_ids}
    correct_total = 0
    answered = 0
    for question_id in attempt.question_ids:
        question = by_id.get(question_id)
        if question is None:
            continue
        chosen = answers.get(question_id)
        if chosen is not None:
            answered += 1
        is_correct = chosen is not None and chosen == question.correct_index
        correct_total += int(is_correct)
        tally[question.skill_id][0] += int(is_correct)
        tally[question.skill_id][1] += 1

    total = len(attempt.question_ids)
    raw_pct = round(100 * correct_total / total, 1) if total else 0.0
    # `pass_pct` is nullable because the certification mock deliberately has no
    # pass mark. Attempts that reach here always carry one — the endpoint turns
    # a certification attempt away — but falling back rather than trusting that
    # keeps a routing mistake from grading against `None`, which raises at the
    # end of a sitting the learner has already spent half an hour on.
    pass_pct = attempt.pass_pct if attempt.pass_pct is not None else DEFAULT_PASS_PCT
    passed = raw_pct >= pass_pct

    per_skill = []
    for skill_id in skill_ids:
        got, asked = tally[skill_id]
        skill = skill_by_id.get(skill_id)
        per_skill.append(
            {
                "skill_id": skill_id,
                "name_es": skill.name_es if skill else skill_id,
                "name_en": skill.name_en if skill else skill_id,
                "correct": got,
                "total": asked,
                "pct": round(100 * got / asked, 1) if asked else None,
            }
        )

    return {
        "track_id": attempt.track_id,
        "module_id": attempt.module_id,
        "kind": attempt.kind,
        "questions": total,
        "answered": answered,
        "unanswered": total - answered,
        "correct": correct_total,
        "raw_pct": raw_pct,
        "pass_pct": pass_pct,
        "passed": passed,
        "per_skill": per_skill,
        "elapsed_seconds": int((moment - _as_utc(attempt.started_at)).total_seconds()),
        "duration_minutes": attempt.duration_minutes,
        "scoring_note_es": (
            "Las preguntas sin responder cuentan como falladas, igual que en el examen. "
            "El porcentaje es de aciertos brutos sobre el total sorteado; no lo convertimos "
            "a ninguna escala inventada. El desglose por skill lleva sus aciertos sobre el "
            "total preguntado: con dos o tres preguntas, un acierto mueve el porcentaje "
            "mucho mas de lo que dice de ti."
        ),
        "scoring_note_en": (
            "Unanswered questions count as incorrect, the same way the exam treats them. "
            "The percentage is raw correct over the questions drawn; we do not convert it to "
            "any invented scale. Each per-skill row carries its correct-out-of-total: with "
            "two or three questions, one answer moves the percentage far more than it says "
            "about you."
        ),
    }


def _new_certificate_code() -> str:
    """URL-safe, unguessable, and not derived from the holder or the attempt.

    The verification page is public and unauthenticated, so the code is the only
    thing standing between a certificate and anybody who wants to enumerate
    other people's. 32 hex chars is 128 bits.
    """
    return secrets.token_hex(16)


async def issue_certificate(
    db: AsyncSession,
    attempt: MockExamAttempt,
    report: dict[str, Any],
    *,
    expired: bool,
) -> Certificate | None:
    """Issues a certificate for a passed, on-time track final or certifying exam.

    Test-out passes do not earn a certificate: skipping a module is not
    finishing a track, and a certificate that means either is a certificate that
    means neither. Re-sitting a track you already passed does not mint a second
    certificate — the existing one is returned, so a shared URL never goes dead.

    `expired` is a parameter rather than something recomputed here because the
    caller has already decided it, and the two answers must not be able to
    disagree. An expired sitting is still *graded* — the learner did the work —
    but it cannot be cashed in: a timed exam whose certificate you can earn by
    submitting three days later is not a timed exam. The first version of this
    function checked only `report["passed"]`, and the test for a late submission
    is what caught it.
    """
    if expired or attempt.kind not in CERTIFYING_KINDS or not report["passed"]:
        return None

    existing = (
        await db.scalars(
            select(Certificate).where(
                Certificate.user_id == attempt.user_id,
                Certificate.track_id == attempt.track_id,
            )
        )
    ).first()
    if existing is not None:
        return existing

    certificate = Certificate(
        id=uuid.uuid4(),
        code=_new_certificate_code(),
        user_id=attempt.user_id,
        track_id=attempt.track_id,
        attempt_id=attempt.id,
        score_pct=report["raw_pct"],
        questions=report["questions"],
    )
    db.add(certificate)
    await db.flush()
    return certificate


async def track_exam_blueprint(db: AsyncSession, track_id: str) -> dict[str, Any]:
    """What a track's final exam will look like, without starting one.

    The catalogue screen states the number of questions and the time before the
    learner commits, and 17.4 reads the same numbers. Computing them in one
    place is what keeps the screen and the exam from drifting apart.
    """
    track = await db.get(Track, track_id)
    if track is None:
        raise TrackExamError(f"{track_id} does not exist")

    skill_count = (
        await db.scalar(
            select(func.count(Skill.id))
            .join(Module, Skill.module_id == Module.id)
            .where(Module.track_id == track_id)
        )
    ) or 0
    total = blueprint_size(
        int(skill_count), minimum=MIN_TRACK_EXAM_QUESTIONS, maximum=MAX_TRACK_EXAM_QUESTIONS
    )
    return {
        "track_id": track_id,
        "skills": int(skill_count),
        "questions": total,
        "duration_minutes": duration_minutes_for(total),
        "pass_pct": track.passing_score_pct or DEFAULT_PASS_PCT,
    }


def is_expired(attempt: MockExamAttempt, *, now: datetime | None = None) -> bool:
    return (now or datetime.now(UTC)) > _as_utc(attempt.expires_at)
