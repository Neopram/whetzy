"""Timed certification mock exam: question selection and per-domain report (10.3).

Two decisions in here are about honesty rather than mechanics, and both follow
from red line 1 - never overstate what someone knows.

**No predicted scaled score.** A real CLF-C02 result is a scaled score from 100
to 1,000 with 700 to pass, computed by AWS from item statistics we do not have,
over 50 scored questions mixed with 15 unscored ones that are not identified.
Mapping a raw percentage onto that scale would produce a number that looks
official and is invented. The report gives the raw percentage, says plainly what
the real scoring model is, and refuses to translate between them.

**Per-domain figures come with their sample size.** The exam guide itself warns
to "use caution when you interpret section-level feedback", and the arithmetic
says why: Domain 4 is 12 % of the exam, so about 8 questions. Getting 6 of 8
right is 75 %, and the difference between 75 % and 88 % there is one question.
Every per-domain row therefore carries its correct/total, and rows too small to
support a judgement are marked as such instead of being quietly reported.
"""

from __future__ import annotations

import random
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import Domain, Module, Question, Skill, Track
from app.models.exam import MockExamAttempt
from app.models.user import User

# Below this many questions in a domain, a percentage says more about the draw
# than about the learner, so the report says so instead of implying precision.
MIN_QUESTIONS_FOR_DOMAIN_VERDICT = 10

# Per-provider scoring notes. Only include text that is verifiable from the
# official exam guide; never invent a scale. Unknown providers fall back to
# the "_generic" entry. Keys are lowercase cert_provider values.
_SCORING_NOTES: dict[str, tuple[str, str]] = {
    "aws": (
        (
            "El examen real se puntua en una escala de 100 a 1.000 y se aprueba con 700, "
            "calculada por AWS sobre 50 preguntas puntuadas mezcladas con 15 sin puntuar que "
            "no se identifican. Este simulacro te da el porcentaje bruto de aciertos: no lo "
            "convertimos a esa escala porque no tenemos con que hacerlo, y un numero inventado "
            "que parece oficial es peor que ninguno."
        ),
        (
            "The real exam is reported as a scaled score from 100 to 1,000, passing at 700, "
            "computed by AWS over 50 scored questions mixed with 15 unscored ones that are not "
            "identified. This mock gives you the raw percentage correct: we do not convert it to "
            "that scale because we have no basis to, and an invented number that looks official "
            "is worse than none."
        ),
    ),
    "_generic": (
        (
            "El examen real tiene su propio modelo de puntuacion con un umbral de aprobado "
            "publicado por el proveedor. Este simulacro te da el porcentaje bruto de aciertos: "
            "no lo convertimos en la escala del proveedor porque no tenemos con que hacerlo."
        ),
        (
            "The real exam has its own scoring model with a passing threshold published by the "
            "provider. This mock gives you the raw percentage correct: we do not convert it to "
            "the provider's scale because we have no basis to do so."
        ),
    ),
}


class MockExamError(Exception):
    """Raised for conditions the caller should turn into a 4xx response."""


def _as_utc(moment: datetime) -> datetime:
    """Normalises a stored timestamp to an aware UTC one.

    The columns are `DateTime(timezone=True)`, which Postgres honours and
    SQLite does not: reading back under SQLite yields a naive datetime, so any
    arithmetic against `datetime.now(UTC)` raises. Tests run on SQLite and
    production on Postgres, so without this the clock logic would work in one
    and break in the other - and it would break at submit time, after the
    learner had spent 90 minutes.
    """
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def _domain_allocation(weights: dict[str, float], total: int) -> dict[str, int]:
    """Splits `total` questions across domains by published weight.

    Uses largest-remainder so the parts always sum to exactly `total`: naive
    rounding of 24/30/34/12 over 65 gives 64, and an exam that is one question
    short of the real one is a small lie told every single sitting.
    """
    exact = {d: total * w / 100 for d, w in weights.items()}
    allocation = {d: int(v) for d, v in exact.items()}
    remainder = total - sum(allocation.values())
    # Hand out the leftovers to the largest fractional parts, ties by domain id
    # so the split is deterministic rather than dict-order dependent.
    by_fraction = sorted(exact, key=lambda d: (-(exact[d] - int(exact[d])), d))
    for domain_id in by_fraction[:remainder]:
        allocation[domain_id] += 1
    return allocation


async def _questions_by_domain(db: AsyncSession, track_id: str) -> dict[str, list[str]]:
    """Answerable questions per domain, keyed by domain id.

    Only option-bearing questions qualify. The exam screen renders the draw as a
    radiogroup and scores it by `correct_index`, so a `fill_blank` pulled into an
    exam paints an *empty* radiogroup: the sitting cannot answer it, and
    `_grade` still counts it as failed. That is a score the candidate did not
    earn, which is red line 1 in the one place that is meant to predict a real
    exam result. Both languages must carry options or the same exam would be
    answerable in Spanish and not in English (red line 3).

    Behind `MOCK_EXAM_RESERVED_POOL_ENABLED` (37.18, ADR-53 §4), draws only
    from `pool == "simulacro"` — the bank reserved so a score does not
    partly measure questions the learner already memorized from practice.
    Flag off = today's behavior: the same bank practice serves.
    """
    conditions = [Module.track_id == track_id, Skill.domain_id.is_not(None)]
    if settings.MOCK_EXAM_RESERVED_POOL_ENABLED:
        conditions.append(Question.pool == "simulacro")
    rows = (
        await db.execute(
            select(Skill.domain_id, Question.id, Question.options_es, Question.options_en)
            .join(Question, Question.skill_id == Skill.id)
            .join(Module, Skill.module_id == Module.id)
            .where(*conditions)
        )
    ).all()
    by_domain: dict[str, list[str]] = {}
    for domain_id, question_id, options_es, options_en in rows:
        # JSON null decodes to None and an authored-but-empty list is just as
        # unanswerable, so both are dropped by the same falsy check.
        if not options_es or not options_en:
            continue
        by_domain.setdefault(str(domain_id), []).append(str(question_id))
    return by_domain


async def start_attempt(
    db: AsyncSession,
    user: User,
    track_id: str,
    *,
    rng: random.Random | None = None,
    kind: str = "certification",
    pass_pct: float | None = None,
) -> MockExamAttempt:
    """Draws a weighted question set and starts the clock.

    `kind`/`pass_pct` let the paid certifying exam (38.7) reuse the same
    blueprint draw; the mock itself keeps no pass mark.
    """
    track = await db.get(Track, track_id)
    if track is None or not track.is_certification:
        raise MockExamError(f"{track_id} is not a certification track")
    if not track.exam_question_count or not track.exam_duration_minutes:
        raise MockExamError(f"{track_id} has no exam blueprint (question count / duration)")

    domains = (
        await db.scalars(select(Domain).where(Domain.track_id == track_id).order_by(Domain.order))
    ).all()
    if not domains:
        raise MockExamError(f"{track_id} has no exam domains")

    by_domain = await _questions_by_domain(db, track_id)
    allocation = _domain_allocation({d.id: d.weight_pct for d in domains}, track.exam_question_count)

    picker = rng or random.Random()
    selected: list[str] = []
    short: list[str] = []
    for domain in domains:
        want = allocation[domain.id]
        available = by_domain.get(domain.id, [])
        if len(available) < want:
            short.append(f"{domain.name_en}: {len(available)} available, {want} needed")
        selected.extend(picker.sample(available, min(want, len(available))))

    if short:
        # Silently serving a shorter exam would make every later score
        # incomparable with the real one without anybody noticing.
        raise MockExamError("not enough questions to mirror the exam blueprint - " + "; ".join(short))

    picker.shuffle(selected)
    now = datetime.now(UTC)
    attempt = MockExamAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        track_id=track_id,
        kind=kind,
        pass_pct=pass_pct,
        question_ids=selected,
        duration_minutes=track.exam_duration_minutes,
        started_at=now,
        expires_at=now + timedelta(minutes=track.exam_duration_minutes),
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
    """Grades a sitting and builds the per-domain report.

    Unanswered questions count as incorrect, which is what the real exam does:
    "Unanswered questions are scored as incorrect; there is no penalty for
    guessing." Leaving them out of the denominator would flatter the learner.
    """
    moment = now or datetime.now(UTC)
    questions = (
        await db.scalars(select(Question).where(Question.id.in_(attempt.question_ids)))
    ).all()
    by_id = {q.id: q for q in questions}

    skill_ids = {q.skill_id for q in questions}
    skill_rows = (
        await db.execute(select(Skill.id, Skill.domain_id).where(Skill.id.in_(skill_ids)))
    ).all()
    domain_of_skill = {str(s): (str(d) if d else None) for s, d in skill_rows}

    domains = (
        await db.scalars(
            select(Domain).where(Domain.track_id == attempt.track_id).order_by(Domain.order)
        )
    ).all()

    tally: dict[str, list[int]] = {d.id: [0, 0] for d in domains}
    correct_total = 0
    answered = 0
    for question_id in attempt.question_ids:
        question = by_id.get(question_id)
        if question is None:
            continue
        domain_id = domain_of_skill.get(question.skill_id)
        chosen = answers.get(question_id)
        if chosen is not None:
            answered += 1
        is_correct = chosen is not None and chosen == question.correct_index
        correct_total += int(is_correct)
        if domain_id in tally:
            tally[domain_id][0] += int(is_correct)
            tally[domain_id][1] += 1

    track = await db.get(Track, attempt.track_id)
    provider_key = (track.cert_provider or "").lower() if track else ""
    note_es, note_en = _SCORING_NOTES.get(provider_key, _SCORING_NOTES["_generic"])

    total = len(attempt.question_ids)
    per_domain = []
    for domain in domains:
        got, asked = tally[domain.id]
        per_domain.append(
            {
                "domain_id": domain.id,
                "name_es": domain.name_es,
                "name_en": domain.name_en,
                "weight_pct": domain.weight_pct,
                "correct": got,
                "total": asked,
                "pct": round(100 * got / asked, 1) if asked else None,
                # The guide's own warning, made machine-readable so the UI can
                # show it rather than leaving the caveat to a footnote.
                "enough_questions_to_judge": asked >= MIN_QUESTIONS_FOR_DOMAIN_VERDICT,
            }
        )

    return {
        "track_id": attempt.track_id,
        "questions": total,
        "answered": answered,
        "unanswered": total - answered,
        "correct": correct_total,
        "raw_pct": round(100 * correct_total / total, 1) if total else 0.0,
        "per_domain": per_domain,
        "elapsed_seconds": int((moment - _as_utc(attempt.started_at)).total_seconds()),
        "duration_minutes": attempt.duration_minutes,
        # Deliberately NOT a predicted scaled score - see the module docstring.
        "scoring_note_es": note_es,
        "scoring_note_en": note_en,
        "per_domain_caveat_es": (
            "La guia oficial pide cautela al interpretar el detalle por dominio: los dominios "
            "pequenos traen pocas preguntas, y ahi una respuesta cambia el porcentaje varios "
            "puntos. Por eso cada fila lleva sus aciertos sobre el total."
        ),
        "per_domain_caveat_en": (
            "The official guide asks for caution when interpreting section-level feedback: small "
            "domains carry few questions, and there one answer moves the percentage by several "
            "points. That is why every row carries its correct-out-of-total."
        ),
    }


def is_expired(attempt: MockExamAttempt, *, now: datetime | None = None) -> bool:
    return (now or datetime.now(UTC)) > _as_utc(attempt.expires_at)


def public_question_ids(attempt: MockExamAttempt) -> Sequence[str]:
    return list(attempt.question_ids)
