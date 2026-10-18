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
    # Sin "placement": la prueba de nivel va por /placement/* (§7 de 43.5,
    # 2026-10-17). Un quiz «placement» abierto aquí no pasaba la puerta de
    # lección y, terminado, contaba como prueba para H.60.
    mode: str = Field(default="study", pattern="^(study|review|exam)$")
    # Dev/E2E only: serve this exact question instead of running selection.
    # Rejected outside ENVIRONMENT != "production" (see quiz.py start_session).
    force_question_id: str | None = None


class SelectionReason(BaseModel):
    pool: str
    skill_strategy: str | None = None
    difficulty_target: float | None = None
    expected_p: float | None = None


class QuizStartResponse(BaseModel):
    session_id: uuid.UUID
    mode: str
    question: QuestionPublic | None = None
    reviews_due: int = 0
    selection_reason: SelectionReason | None = None


class QuizAnswerRequest(BaseModel):
    session_id: uuid.UUID
    question_id: str
    # An explicit "I don't know", which is not the same as `selected_index=None`
    # (no answer sent). When true, `selected_index` is ignored.
    declared_unknown: bool = False
    selected_index: int | None = None
    response_time_ms: int = Field(ge=0)
    # For exec-type questions (fill_blank_exec, fix_bug): the actual stdout
    # produced by the client's Pyodide run.  Server validates against the stored
    # correct_answer to prevent the client from falsifying correctness.
    exec_output: str | None = Field(default=None, max_length=20_000)
    # For `fill_blank`: the text the learner typed. The server compares it with
    # the stored answer (trimmed, case-insensitive); without it the answer is wrong.
    answer_text: str | None = Field(default=None, max_length=2_000)
    # Client-generated UUID for offline queue idempotency (33.2).
    # La columna es String(64): más largo debe ser 422, no un 500 de la base.
    event_id: str | None = Field(default=None, max_length=64)


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
    next_selection_reason: SelectionReason | None = None
    # Cupo Free agotado (39.4): no hay `next_question` hasta mañana UTC.
    quota_reached: bool = False


class QuizEndRequest(BaseModel):
    session_id: uuid.UUID


class QuizEndResponse(BaseModel):
    total_questions: int
    correct: int
    accuracy: float
    max_combo: int
    xp_earned: int
    duration_seconds: int
    # Créditos que la sesión dejó ganados (módulo, racha, diagnóstico; §2.2).
    credits_earned: int = 0


class ReviewDueResponse(BaseModel):
    due_count: int
