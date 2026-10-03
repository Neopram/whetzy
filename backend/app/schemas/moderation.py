from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.moderation import VALID_REPORT_CONTEXTS, VALID_REPORT_REASONS


class UserReportRequest(BaseModel):
    reported_user_id: uuid.UUID
    reason: str
    context: str = "other"

    @field_validator("reason")
    @classmethod
    def _razon_valida(cls, value: str) -> str:
        if value not in VALID_REPORT_REASONS:
            raise ValueError(f"reason must be one of {sorted(VALID_REPORT_REASONS)}")
        return value

    @field_validator("context")
    @classmethod
    def _contexto_valido(cls, value: str) -> str:
        if value not in VALID_REPORT_CONTEXTS:
            raise ValueError(f"context must be one of {sorted(VALID_REPORT_CONTEXTS)}")
        return value


class UserReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reported_id: uuid.UUID
    reason: str
    context: str
    created_at: datetime


class UserBlockRequest(BaseModel):
    user_id: uuid.UUID


class BlockedUserRead(BaseModel):
    user_id: uuid.UUID
    username: str
    display_name: str
    blocked_at: datetime
