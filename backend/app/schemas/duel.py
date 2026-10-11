"""Pydantic schemas for duel endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.content import QuestionPublic


class DuelChallengeRequest(BaseModel):
    opponent_username: str
    skill_id: str | None = None


class DuelChallengeResponse(BaseModel):
    duel_id: str
    skill_id: str
    questions: list[QuestionPublic]
    opponent_username: str


class DuelAnswerRequest(BaseModel):
    question_id: str
    selected_index: int
    response_time_ms: int


class DuelAnswerResponse(BaseModel):
    duel_id: str
    answers_so_far: int
    completed: bool
    opponent_completed: bool


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
