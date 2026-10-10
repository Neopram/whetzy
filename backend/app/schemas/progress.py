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


class DecayingSkill(BaseModel):
    """A skill whose spaced-repetition review is due, or about to be."""

    skill_id: str
    name_es: str
    name_en: str
    track_id: str
    p_known: float
    due_at: datetime
    # Negative when the review is already overdue. The client decides how to
    # phrase that; the server does not editorialise.
    days_until_due: int


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
    dkt_probability: float | None = None


class CurriculumSkill(BaseModel):
    skill_id: str
    name_es: str
    name_en: str
    order: int
    p_known: float
    mastered: bool
    attempts: int
    # 32.4: si el frontend debe dejar practicar este skill sin haber abierto
    # su lección primero (el backend igual lo exige en /quiz/start).
    lesson_seen: bool


class CurriculumModule(BaseModel):
    id: str
    name_es: str
    name_en: str
    order: int
    description_es: str
    description_en: str
    min_mastery_to_unlock: float
    level: int = 1
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


class DomainThresholds(BaseModel):
    """The motor's canonical domain thresholds (C.1, 2026-10-04) — served so
    a frontend screen reads these instead of hardcoding its own copy, the way
    `HomeScreen.tsx` (`MASTERED = 0.95`) and `EvidenceScreen.tsx`
    (`masteryThreshold: '0.95'`) each do today. See
    app.services.engine.domain_thresholds for why one copy matters."""

    mastery_threshold: float
    default_module_unlock_mastery: float
