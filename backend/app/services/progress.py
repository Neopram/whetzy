"""Dashboard, per-skill mastery breakdown, and completion-time predictions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.content import Module, Question, Skill, Track
from app.models.session import Response, StudySession
from app.models.user import User, UserSkillState
from app.services import dkt as dkt_service
from app.schemas.progress import (
    CurriculumModule,
    CurriculumResponse,
    CurriculumSkill,
    DashboardResponse,
    PredictionResponse,
    SkillMasteryDetail,
    TrackMastery,
)
from app.services.quiz import count_due_reviews

MASTERY_THRESHOLD = settings.MASTERY_THRESHOLD


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_dashboard(db: AsyncSession, user: User) -> DashboardResponse:
    tracks_result = await db.execute(
        select(Track).options(selectinload(Track.modules).selectinload(Module.skills)).order_by(Track.order)
    )
    tracks = tracks_result.scalars().all()

    states_result = await db.execute(
        select(UserSkillState.skill_id, UserSkillState.p_known).where(UserSkillState.user_id == user.id)
    )
    mastery_by_skill = {row[0]: row[1] for row in states_result.all()}

    track_masteries: list[TrackMastery] = []
    for track in tracks:
        skill_ids = [s.id for m in track.modules for s in m.skills]
        if skill_ids:
            values = [mastery_by_skill.get(sid, 0.0) for sid in skill_ids]
            avg_mastery = sum(values) / len(values)
            mastered = sum(1 for v in values if v >= MASTERY_THRESHOLD)
        else:
            avg_mastery = 0.0
            mastered = 0
        track_masteries.append(
            TrackMastery(
                track_id=track.id,
                name_es=track.name_es,
                name_en=track.name_en,
                icon=track.icon,
                color=track.color,
                average_mastery=round(avg_mastery, 4),
                skills_mastered=mastered,
                total_skills=len(skill_ids),
            )
        )

    reviews_due = await count_due_reviews(db, user)

    sessions_result = await db.execute(
        select(
            func.count(StudySession.id),
            func.coalesce(func.sum(StudySession.questions_answered), 0),
            func.coalesce(func.sum(StudySession.correct_count), 0),
        ).where(StudySession.user_id == user.id)
    )
    total_sessions, total_answered, total_correct = sessions_result.one()
    overall_accuracy = (total_correct / total_answered) if total_answered else 0.0

    return DashboardResponse(
        level=user.level,
        total_xp=user.total_xp,
        current_streak=user.current_streak,
        max_streak=user.max_streak,
        streak_freeze_available=user.streak_freeze_available,
        last_active=user.last_active,
        reviews_due=reviews_due,
        tracks=track_masteries,
        total_sessions=int(total_sessions),
        total_questions_answered=int(total_answered),
        overall_accuracy=round(overall_accuracy, 4),
    )


async def get_skill_breakdown(
    db: AsyncSession, user: User, track_id: str | None = None, module_id: str | None = None
) -> list[SkillMasteryDetail]:
    query = select(Skill).options(selectinload(Skill.module))
    if module_id:
        query = query.where(Skill.module_id == module_id)
    elif track_id:
        query = query.join(Module, Module.id == Skill.module_id).where(Module.track_id == track_id)
    query = query.order_by(Skill.module_id, Skill.order)

    skills_result = await db.execute(query)
    skills = skills_result.scalars().all()

    states_by_skill: dict[str, UserSkillState] = {}
    if skills:
        states_result = await db.execute(
            select(UserSkillState).where(
                UserSkillState.user_id == user.id,
                UserSkillState.skill_id.in_([s.id for s in skills]),
            )
        )
        states_by_skill = {s.skill_id: s for s in states_result.scalars().all()}

    # Build response history for DKT (last 200 responses, chronological)
    history_result = await db.execute(
        select(Question.skill_id, Response.correct)
        .join(Response, Response.question_id == Question.id)
        .join(StudySession, StudySession.id == Response.session_id)
        .where(StudySession.user_id == user.id)
        .order_by(Response.created_at)
        .limit(200)
    )
    dkt_history = [
        {"skill_id": row[0], "correct": row[1]}
        for row in history_result.all()
    ]
    skill_index = {s.id: i for i, s in enumerate(skills)}
    dkt_probs = dkt_service.predict(dkt_history, skill_index) if dkt_history else {}

    breakdown: list[SkillMasteryDetail] = []
    for skill in skills:
        state = states_by_skill.get(skill.id)
        p_known = state.p_known if state else 0.0
        attempts = state.attempts if state else 0
        correct_count = state.correct_count if state else 0
        breakdown.append(
            SkillMasteryDetail(
                skill_id=skill.id,
                name_es=skill.name_es,
                name_en=skill.name_en,
                module_id=skill.module_id,
                p_known=round(p_known, 4),
                elo_rating=state.elo_rating if state else 1500.0,
                attempts=attempts,
                correct_count=correct_count,
                accuracy=round(correct_count / attempts, 4) if attempts else 0.0,
                mastered=p_known >= MASTERY_THRESHOLD,
                fsrs_due=state.fsrs_due if state else None,
                dkt_probability=dkt_probs.get(skill.id),
            )
        )
    return breakdown


async def get_curriculum(db: AsyncSession, user: User, track_id: str) -> CurriculumResponse:
    """Gated curriculum for a track: modules in order, each with a lock state
    derived from the BKT-mastery prerequisite spine.

    A module unlocks once the *previous* module's average per-skill mastery
    (`UserSkillState.p_known`) reaches that previous module's
    `min_mastery_to_unlock`. The first module is always available. A module is
    'completed' when its own average mastery clears its own threshold."""
    track = await db.get(Track, track_id)
    if track is None:
        return CurriculumResponse(
            track_id=track_id, name_es="", name_en="", icon="📘",
            color="#1CB0F6", mastery_threshold=MASTERY_THRESHOLD, modules=[],
        )

    modules_result = await db.execute(
        select(Module)
        .options(selectinload(Module.skills))
        .where(Module.track_id == track_id)
        .order_by(Module.order)
    )
    modules = list(modules_result.scalars().all())

    all_skill_ids = [s.id for m in modules for s in m.skills]
    mastery_by_skill: dict[str, float] = {}
    attempts_by_skill: dict[str, int] = {}
    if all_skill_ids:
        states_result = await db.execute(
            select(UserSkillState.skill_id, UserSkillState.p_known, UserSkillState.attempts).where(
                UserSkillState.user_id == user.id,
                UserSkillState.skill_id.in_(all_skill_ids),
            )
        )
        for skill_id, p_known, attempts in states_result.all():
            mastery_by_skill[skill_id] = p_known
            attempts_by_skill[skill_id] = attempts

    def module_avg(module: Module) -> float:
        skills = sorted(module.skills, key=lambda s: s.order)
        if not skills:
            return 0.0
        return sum(mastery_by_skill.get(s.id, 0.0) for s in skills) / len(skills)

    out_modules: list[CurriculumModule] = []
    prev_module: Module | None = None
    prev_avg = 0.0
    for module in modules:
        avg = module_avg(module)
        if prev_module is None:
            prerequisite_id = None
            prerequisite_met = True
        else:
            prerequisite_id = prev_module.id
            prerequisite_met = prev_avg >= prev_module.min_mastery_to_unlock

        if not prerequisite_met:
            module_status = "locked"
        elif avg >= module.min_mastery_to_unlock:
            module_status = "completed"
        else:
            module_status = "available"

        skills = [
            CurriculumSkill(
                skill_id=s.id,
                name_es=s.name_es,
                name_en=s.name_en,
                order=s.order,
                p_known=round(mastery_by_skill.get(s.id, 0.0), 4),
                mastered=mastery_by_skill.get(s.id, 0.0) >= MASTERY_THRESHOLD,
                attempts=attempts_by_skill.get(s.id, 0),
            )
            for s in sorted(module.skills, key=lambda s: s.order)
        ]

        out_modules.append(
            CurriculumModule(
                id=module.id,
                name_es=module.name_es,
                name_en=module.name_en,
                order=module.order,
                description_es=module.description_es,
                description_en=module.description_en,
                min_mastery_to_unlock=module.min_mastery_to_unlock,
                average_mastery=round(avg, 4),
                status=module_status,
                prerequisite_id=prerequisite_id,
                prerequisite_met=prerequisite_met,
                skills=skills,
            )
        )
        prev_module = module
        prev_avg = avg

    return CurriculumResponse(
        track_id=track.id,
        name_es=track.name_es,
        name_en=track.name_en,
        icon=track.icon,
        color=track.color,
        mastery_threshold=MASTERY_THRESHOLD,
        modules=out_modules,
    )


async def get_predictions(db: AsyncSession, user: User, track_id: str) -> PredictionResponse:
    skills_result = await db.execute(
        select(Skill.id)
        .join(Module, Module.id == Skill.module_id)
        .where(Module.track_id == track_id)
    )
    skill_ids = [row[0] for row in skills_result.all()]

    mastery_by_skill: dict[str, float] = {}
    if skill_ids:
        states_result = await db.execute(
            select(UserSkillState.skill_id, UserSkillState.p_known).where(
                UserSkillState.user_id == user.id,
                UserSkillState.skill_id.in_(skill_ids),
            )
        )
        mastery_by_skill = {row[0]: row[1] for row in states_result.all()}
    mastered = sum(1 for sid in skill_ids if mastery_by_skill.get(sid, 0.0) >= MASTERY_THRESHOLD)
    remaining = len(skill_ids) - mastered

    window_start = _now() - timedelta(days=14)
    xp_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.xp_earned), 0), func.count(func.distinct(func.date(StudySession.started_at))))
        .where(StudySession.user_id == user.id, StudySession.started_at >= window_start)
    )
    total_xp_14d, active_days = xp_result.one()
    avg_xp_per_day = (total_xp_14d / active_days) if active_days else 0.0

    xp_per_skill_to_master = 180  # empirical rule-of-thumb XP cost to master one skill
    estimated_xp_needed = remaining * xp_per_skill_to_master

    if avg_xp_per_day > 0:
        estimated_days = round(estimated_xp_needed / avg_xp_per_day, 1)
        confidence = "high" if active_days and active_days >= 7 else "medium"
    else:
        estimated_days = None
        confidence = "low"

    return PredictionResponse(
        track_id=track_id,
        skills_remaining=remaining,
        avg_xp_per_day=round(avg_xp_per_day, 1),
        estimated_xp_needed=estimated_xp_needed,
        estimated_days_to_completion=estimated_days,
        confidence=confidence,
    )
