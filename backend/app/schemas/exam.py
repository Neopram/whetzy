"""Schemas for the timed certification mock exam (10.3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.content import QuestionPublic


class MockExamStartRequest(BaseModel):
    track_id: str = Field(min_length=1, max_length=64)


class MockExamStartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    track_id: str
    duration_minutes: int
    started_at: datetime
    expires_at: datetime
    questions: list[QuestionPublic]


class MockExamAnswer(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    selected_index: int = Field(ge=0, le=9)


class MockExamSubmitRequest(BaseModel):
    # Answers may be partial: unanswered questions are scored as incorrect, the
    # same way the real exam treats them.
    answers: list[MockExamAnswer] = Field(default_factory=list)


class MockExamDomainResult(BaseModel):
    domain_id: str
    name_es: str
    name_en: str
    weight_pct: float
    correct: int
    total: int
    pct: float | None
    enough_questions_to_judge: bool


class MockExamReport(BaseModel):
    track_id: str
    questions: int
    answered: int
    unanswered: int
    correct: int
    raw_pct: float
    per_domain: list[MockExamDomainResult]
    elapsed_seconds: int
    duration_minutes: int
    scoring_note_es: str
    scoring_note_en: str
    per_domain_caveat_es: str
    per_domain_caveat_en: str
    # Only the paid certifying exam (38.7) declares a pass; the mock never does.
    pass_pct: float | None = None
    passed: bool | None = None
    pass_note_es: str | None = None
    pass_note_en: str | None = None


class MockExamSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    status: str
    expired: bool
    report: MockExamReport
    # Present only when a certifying exam was passed on time.
    certificate: CertificatePublic | None = None


class CertificationAccess(BaseModel):
    """Whether the learner can sit a track's certifying exam (38.7, ADR-49)."""

    track_id: str
    price_usd: float
    paywall_enabled: bool
    purchased: bool
    can_start: bool


# ── Certification readiness (18.1) ───────────────────────────────────────────


class DomainReadiness(BaseModel):
    """BKT-based readiness score for one exam domain.

    `p_known_mean=None` means "sin datos": no skill in this domain has been
    attempted yet (C.2, 2026-10-04) - distinct from a low but measured
    score. `ready` is always `False` when there is no data; it is not a
    second way of saying the same thing as `p_known_mean is None`, since a
    domain CAN have data and still not clear the ready bar."""

    domain_id: str
    name_es: str
    name_en: str
    weight_pct: float
    p_known_mean: float | None
    skills_assessed: int
    skills_total: int
    ready: bool


class CertificationReadiness(BaseModel):
    """Per-domain BKT readiness for a certification track.

    `overall_p_known=None` means every domain is "sin datos" - the learner
    has not attempted a single skill in this track yet. `ready_for_simulacro`
    (B.11, 2026-10-04) is true only when EVERY domain is individually ready
    (see `DomainReadiness.ready`) - the explicit "take the mock exam now?"
    answer, not left for each screen to derive from the per-domain list."""

    track_id: str
    domains: list[DomainReadiness]
    overall_p_known: float | None
    ready_for_simulacro: bool


# ── Track final exam and module test-out (17.2) ─────────────────────────────


class TrackExamBlueprint(BaseModel):
    """What a sitting will look like, published before the learner commits."""

    track_id: str
    skills: int
    questions: int
    duration_minutes: int
    pass_pct: float


class TestOutBlueprint(BaseModel):
    """A module test-out before committing; `available` False = not enough questions."""

    module_id: str
    skills: int
    questions: int
    duration_minutes: int
    pass_pct: float
    available: bool


class TrackExamStartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    track_id: str
    module_id: str | None
    kind: str
    duration_minutes: int
    pass_pct: float
    started_at: datetime
    expires_at: datetime
    questions: list[QuestionPublic]


class TrackExamSkillResult(BaseModel):
    skill_id: str
    name_es: str
    name_en: str
    correct: int
    total: int
    pct: float | None


class TrackExamReport(BaseModel):
    track_id: str
    module_id: str | None
    kind: str
    questions: int
    answered: int
    unanswered: int
    correct: int
    raw_pct: float
    pass_pct: float
    passed: bool
    per_skill: list[TrackExamSkillResult]
    elapsed_seconds: int
    duration_minutes: int
    scoring_note_es: str
    scoring_note_en: str


class CertificatePublic(BaseModel):
    """What the public verification page shows. Deliberately small."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    username: str
    track_id: str
    track_name_es: str
    track_name_en: str
    score_pct: float
    questions: int
    issued_at: datetime
    revoked: bool
    # A certification track's certificate is a "Whetzy preparation certificate"
    # (ADR-49); the card titles it differently from a track-completion one.
    is_certification: bool = False


class TrackExamSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    status: str
    expired: bool
    report: TrackExamReport
    # Present only when this sitting earned one (a passed track final).
    certificate: CertificatePublic | None = None
    # Skills whose mastery moved as a result of this sitting, and to what.
    # Empty for a track final: only a test-out feeds its answers to the engine.
    mastery_updated: dict[str, float] = Field(default_factory=dict)
