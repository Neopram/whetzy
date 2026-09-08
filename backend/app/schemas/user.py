from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=100)
    language: str = Field(default="es", pattern="^(es|en)$")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_emoji: str | None = Field(default=None, max_length=16)
    language: str | None = Field(default=None, pattern="^(es|en)$")


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avatar_emoji: str
    level: int
    total_xp: int
    current_streak: int
    max_streak: int
    streak_freeze_available: int
    last_active: datetime | None = None
    created_at: datetime
    is_premium: bool
    email_verified: bool = False


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    exp: int | None = None
    iat: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserSkillStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: str
    p_known: float
    elo_rating: float
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_due: datetime | None = None
    attempts: int
    correct_count: int


class UserBadgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    badge_id: str
    earned_at: datetime
