"""Pydantic schemas for duel endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.content import QuestionPublic


class DuelChallengeRequest(BaseModel):
    opponent_username: str
    skill_id: str | None = None


class DuelChallengeResponse(BaseModel):
    duel_id: str
    skill_id: str
    questions: list[QuestionPublic]
    opponent_username: str
    # 42.5: quien vuelve a un duelo a medias sigue por la siguiente pregunta.
    answered_question_ids: list[str] = []


class DuelAnswerRequest(BaseModel):
    question_id: str
    # The upper bound of `selected_index` depends on the question; the endpoint
    # checks it against its options (42.4).
    selected_index: int = Field(ge=0)
    # Only shown to the rival and fed to FSRS; the winner is decided on the
    # server's clock. Bounded so no one can write a negative or absurd time.
    response_time_ms: int = Field(ge=0, le=300_000)


class DuelRivalAnswer(BaseModel):
    """Lo que hizo el rival en esta misma pregunta (su partida ya grabada)."""

    correct: bool
    response_time_ms: int


class DuelAnswerResponse(BaseModel):
    duel_id: str
    answers_so_far: int
    completed: bool
    opponent_completed: bool
    # 42.4: feedback right after answering, as in practice.
    correct: bool
    correct_index: int | None
    explanation_es: str = ""
    explanation_en: str = ""
    # Solo si el rival ya terminó: quien juega segundo ve, tras contestar cada
    # pregunta, cómo le fue al otro en ella. Nunca antes de contestarla.
    rival: DuelRivalAnswer | None = None


class DuelPlayerResult(BaseModel):
    user_id: str
    username: str
    display_name: str
    avatar_emoji: str
    correct: int
    total_time_ms: int


class DuelResultResponse(BaseModel):
    duel_id: str
    status: str
    skill_id: str
    challenger: DuelPlayerResult
    opponent: DuelPlayerResult
    winner_id: str | None
    is_draw: bool
    created_at: datetime
    weak_skill_id: str | None = None


class DuelSummary(BaseModel):
    duel_id: str
    status: str
    skill_id: str
    opponent_username: str
    opponent_avatar: str
    your_correct: int | None
    opponent_correct: int | None
    winner_id: str | None
    is_your_turn: bool
    created_at: datetime
