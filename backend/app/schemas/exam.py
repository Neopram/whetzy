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


class MockExamSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    status: str
    expired: bool
    report: MockExamReport


# ── Track final exam and module test-out (17.2) ─────────────────────────────


class TrackExamBlueprint(BaseModel):
    """What a sitting will look like, published before the learner commits."""

    track_id: str
    skills: int
    questions: int
    duration_minutes: int
    pass_pct: float


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
