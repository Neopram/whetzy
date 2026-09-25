from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LeagueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tier: str
    min_xp: int


class LeagueEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    league_id: str
    week_start: date
    xp_earned: int
    rank: int | None = None


class LeagueStandingEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    display_name: str
    avatar_emoji: str
    xp_earned: int
    is_current_user: bool = False


class LeagueStandingsResponse(BaseModel):
    league: LeagueRead
    week_start: date
    standings: list[LeagueStandingEntry]
    promotion_zone: int
    demotion_zone: int
    # False = el usuario salió de las ligas (35.4): standings vacío.
    participating: bool = True


class LeagueHistoryEntry(BaseModel):
    league: LeagueRead
    week_start: date
    xp_earned: int
    rank: int | None = None


class BadgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name_es: str
    name_en: str
    icon: str
    description_es: str
    description_en: str
    criteria_type: str
    criteria_value: int


class UserBadgeWithDetail(BaseModel):
    badge: BadgeRead
    earned_at: datetime


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    target_value: int
    xp_reward: int
    name_es: str
    name_en: str


class UserMissionRead(BaseModel):
    mission: MissionRead
    progress: int
    completed: bool
    date: date
