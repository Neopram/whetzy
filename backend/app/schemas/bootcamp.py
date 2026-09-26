"""Pydantic schemas for bootcamp endpoints (19.4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BootcampWeekRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    week_number: int
    track_id: str
    title_es: str
    title_en: str


class BootcampRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name_es: str
    name_en: str
    description_es: str
    description_en: str
    duration_weeks: int
    daily_goal_minutes: int
    icon: str
    color: str
    order: int


class BootcampDetail(BootcampRead):
    weeks: list[BootcampWeekRead]


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bootcamp_id: uuid.UUID
    started_at: datetime
    current_week: int
    completed_at: datetime | None
