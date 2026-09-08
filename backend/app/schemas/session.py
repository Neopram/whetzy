from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.content import QuestionPublic


class StudySessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None = None
    questions_answered: int
    correct_count: int
    xp_earned: int
    max_combo: int
    mode: str


class ResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    question_id: str
    correct: bool
    grade: int
    response_time_ms: int
    created_at: datetime


class QuizStartRequest(BaseModel):
    track_id: str | None = None
    skill_id: str | None = None
    mode: str = Field(default="study", pattern="^(study|review|placement|exam)$")
    # Dev/E2E only: serve this exact question instead of running selection.
    # Rejected outside ENVIRONMENT != "production" (see quiz.py start_session).
    force_question_id: str | None = None


class QuizStartResponse(BaseModel):
    session_id: uuid.UUID
    mode: str
    question: QuestionPublic | None = None
    reviews_due: int = 0


class QuizAnswerRequest(BaseModel):
    session_id: uuid.UUID
    question_id: str
    selected_index: int | None = None
    response_time_ms: int = Field(ge=0)


class QuizAnswerResponse(BaseModel):
    correct: bool
    correct_index: int | None = None
    explanation_es: str
    explanation_en: str
    source: str | None = None
    grade: int
    xp_earned: int
    combo: int
    user_elo: float
    next_review: str | None = None
    skill_mastery: dict[str, float]
    session_accuracy: float
    next_question: QuestionPublic | None = None


class QuizEndRequest(BaseModel):
    session_id: uuid.UUID


class QuizEndResponse(BaseModel):
    total_questions: int
    correct: int
    accuracy: float
    max_combo: int
    xp_earned: int
    duration_seconds: int


class ReviewDueResponse(BaseModel):
    due_count: int
