"""Pydantic schemas for project endpoints (18.8 / 19.6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.sql_sandbox import MAX_CODE_CHARS


class ProjectStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    title_es: str
    title_en: str
    instructions_es: str
    instructions_en: str
    starter_code: str
    test_code: str


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    track_id: str
    runtime: str
    name_es: str
    name_en: str
    description_es: str
    description_en: str
    difficulty: int
    source_url: str
    source_license: str
    order: int


class ProjectDetail(ProjectRead):
    steps: list[ProjectStepRead]


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    current_step: int
    completed: bool
    started_at: datetime
    completed_at: datetime | None
    step_code: dict[str, str] = {}
    verified: bool = False


class StepSubmitRequest(BaseModel):
    step_number: int
    code: str = Field(default="", max_length=MAX_CODE_CHARS)
    # Solo cuenta en Python/JS (navegador). En SQL lo decide el servidor (43.6).
    passed: bool = False


class StepSubmitResult(SubmissionRead):
    step_passed: bool
    error: str | None = None
    timed_out: bool = False
