"""Schemas for the CAT-based placement test flow (see
`app.services.placement` and `app.services.engine.placement`)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas.content import QuestionPublic


class PlacementStartRequest(BaseModel):
    track_id: str


class PlacementStartResponse(BaseModel):
    session_id: uuid.UUID
    track_id: str
    question: QuestionPublic | None = None
    questions_answered: int = 0


class PlacementAnswerRequest(BaseModel):
    session_id: uuid.UUID
    question_id: str
    selected_index: int | None = None
    response_time_ms: int = Field(ge=0)


class PlacementAnswerResponse(BaseModel):
    correct: bool
    ability_estimate: float
    ability_se: float
    questions_answered: int
    finished: bool
    next_question: QuestionPublic | None = None


class ModuleSkipRecommendation(BaseModel):
    module_id: str
    module_name_es: str
    module_name_en: str
    accuracy: float
    questions_seen: int
    can_skip: bool


class PlacementResultResponse(BaseModel):
    session_id: uuid.UUID
    track_id: str
    ability_estimate: float
    ability_se: float
    total_questions: int
    correct: int
    accuracy: float
    reliability: float
    skill_mastery: dict[str, float]
    module_recommendations: list[ModuleSkipRecommendation]
