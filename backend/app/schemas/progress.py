"""Schemas for the progress/analytics endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TrackMastery(BaseModel):
    track_id: str
    name_es: str
    name_en: str
    icon: str
    color: str
    average_mastery: float
    skills_mastered: int
    total_skills: int


class DashboardResponse(BaseModel):
    level: int
    total_xp: int
    current_streak: int
    max_streak: int
    streak_freeze_available: int
    last_active: datetime | None = None
    reviews_due: int
    tracks: list[TrackMastery]
    total_sessions: int
    total_questions_answered: int
    overall_accuracy: float


class SkillMasteryDetail(BaseModel):
    skill_id: str
    name_es: str
    name_en: str
    module_id: str
    p_known: float
    elo_rating: float
    attempts: int
    correct_count: int
    accuracy: float
    mastered: bool
    fsrs_due: datetime | None = None


class CurriculumSkill(BaseModel):
    skill_id: str
    name_es: str
    name_en: str
    order: int
    p_known: float
    mastered: bool
    attempts: int


class CurriculumModule(BaseModel):
    id: str
    name_es: str
    name_en: str
    order: int
    description_es: str
    description_en: str
    min_mastery_to_unlock: float
    average_mastery: float
    # 'locked' | 'available' | 'completed'
    status: str
    # id of the module whose mastery gates this one (None for the first module)
    prerequisite_id: str | None = None
    prerequisite_met: bool
    skills: list[CurriculumSkill]


class CurriculumResponse(BaseModel):
    track_id: str
    name_es: str
    name_en: str
    icon: str
    color: str
    mastery_threshold: float
    modules: list[CurriculumModule]


class PredictionResponse(BaseModel):
    track_id: str
    skills_remaining: int
    avg_xp_per_day: float
    estimated_xp_needed: int
    estimated_days_to_completion: float | None = None
    confidence: str  # low | medium | high
