from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from app.schemas.content import QuestionPublic

WIDGET_STATE_MAX_CHARS = 20_000


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
    # For `interactive` (40.1): the widget's serialized state. The server grades
    # it against the stored `target` with the question's checker; without it the
    # answer is wrong.
    widget_state: JsonValue | None = None
    # Client-generated UUID for offline queue idempotency (33.2).
    # La columna es String(64): más largo debe ser 422, no un 500 de la base.
    event_id: str | None = Field(default=None, max_length=64)

    @field_validator("widget_state")
    @classmethod
    def _widget_state_size(cls, v: JsonValue | None) -> JsonValue | None:
        # Same ceiling as exec_output: the checkers walk the whole value.
        if v is not None and len(json.dumps(v, ensure_ascii=False)) > WIDGET_STATE_MAX_CHARS:
            raise ValueError(f"widget_state over {WIDGET_STATE_MAX_CHARS} characters")
        return v


class FxEvent(BaseModel):
    """Un hito que cruzó esta respuesta (46.1b, `docs/PLAN_UI_AVANZADA.md` §6.3).

    El cliente lo celebra (`lib/feedbackFx.ts`); no lo adivina. `payload`:
    level_up {level_before, level} · badge_earned {badge_id} ·
    mission_completed {mission_id} · combo_multiplier {multiplier: 2|3|5} ·
    streak_milestone {days: 7|30|100} · streak_freeze_used {days} (46.11).
    """

    type: Literal[
        "level_up", "badge_earned", "mission_completed", "combo_multiplier", "streak_milestone", "streak_freeze_used"
    ]
    payload: dict[str, Any]


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
    # Hitos de esta respuesta, sin repetidos (46.1b). Vacío en la reentrega idempotente.
    events: list[FxEvent] = Field(default_factory=list)
    # `interactive` (40.1): the target, once answered, so the client re-checks
    # with its own checker and flags a disagreement. Null for every other type.
    widget_target: JsonValue | None = None


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
