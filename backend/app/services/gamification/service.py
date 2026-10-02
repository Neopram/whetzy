"""Leagues, badges, and daily missions business logic."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import Referral
from app.models.gamification import Badge, League, LeagueEntry, Mission, UserMission
from app.models.session import Response, StudySession
from app.models.user import User, UserBadge, UserSkillState
from app.schemas.gamification import (
    BadgeRead,
    LeagueHistoryEntry,
    LeagueRead,
    LeagueStandingEntry,
    LeagueStandingsResponse,
    MissionRead,
    UserBadgeWithDetail,
    UserMissionRead,
)
from app.services.blocklist import blocked_user_ids

PROMOTION_ZONE_SIZE = 5
DEMOTION_ZONE_SIZE = 5
MIN_LEAGUE_SIZE_FOR_ZONES = 10
DEFAULT_DAILY_MISSION_COUNT = 3


def week_start_of(d: date) -> date:
    """Monday of the ISO week containing `d`."""
    return d - timedelta(days=d.weekday())


async def _lowest_tier_league(db: AsyncSession) -> League | None:
    result = await db.execute(select(League).order_by(League.min_xp.asc()).limit(1))
    return result.scalar_one_or_none()


async def get_or_create_current_entry(db: AsyncSession, user: User) -> LeagueEntry | None:
    today_week = week_start_of(date.today())

    result = await db.execute(
        select(LeagueEntry).where(
            LeagueEntry.user_id == user.id, LeagueEntry.week_start == today_week
        )
    )
    entry = result.scalar_one_or_none()
    if entry is not None:
        return entry

    # Carry over the league from the most recent prior week, if any; else start
    # at the lowest tier.
    prev_result = await db.execute(
        select(LeagueEntry)
        .where(LeagueEntry.user_id == user.id, LeagueEntry.week_start < today_week)
        .order_by(LeagueEntry.week_start.desc())
        .limit(1)
    )
    prev_entry = prev_result.scalar_one_or_none()
    league_id = prev_entry.league_id if prev_entry else None

    if league_id is None:
        league = await _lowest_tier_league(db)
        if league is None:
            return None
        league_id = league.id

    entry = LeagueEntry(user_id=user.id, league_id=league_id, week_start=today_week, xp_earned=0)
    db.add(entry)
    await db.flush()
    return entry


async def _opted_out_view(db: AsyncSession, user: User) -> LeagueStandingsResponse | None:
    """Lo que ve quien salió de las ligas: su última liga (o la primera), sin
    clasificación. Volver a entrar la retoma desde ahí."""
    prev = await db.execute(
        select(League)
        .join(LeagueEntry, LeagueEntry.league_id == League.id)
        .where(LeagueEntry.user_id == user.id)
        .order_by(LeagueEntry.week_start.desc())
        .limit(1)
    )
    league = prev.scalar_one_or_none() or await _lowest_tier_league(db)
    if league is None:
        return None
    return LeagueStandingsResponse(
        league=LeagueRead.model_validate(league),
        week_start=week_start_of(date.today()),
        standings=[],
        promotion_zone=0,
        demotion_zone=0,
        participating=False,
    )


async def set_league_participation(
    db: AsyncSession, user: User, participate: bool
) -> LeagueStandingsResponse | None:
    user.leagues_opt_out = not participate
    await db.flush()
    return await get_current_standings(db, user)


async def get_current_standings(db: AsyncSession, user: User) -> LeagueStandingsResponse | None:
    if user.leagues_opt_out:
        view = await _opted_out_view(db, user)
        await db.commit()
        return view
    entry = await get_or_create_current_entry(db, user)
    if entry is None:
        return None

    league_result = await db.execute(select(League).where(League.id == entry.league_id))
    league = league_result.scalar_one()

    entries_result = await db.execute(
        select(LeagueEntry, User)
        .join(User, User.id == LeagueEntry.user_id)
        .where(
            LeagueEntry.league_id == entry.league_id,
            LeagueEntry.week_start == entry.week_start,
            # Quien salió a mitad de semana deja de aparecer en la de los demás.
            User.leagues_opt_out.is_(False),
        )
        .order_by(LeagueEntry.xp_earned.desc())
    )
    rows = entries_result.all()
    # 19.11: quien bloqueó a quien no se ve en la liga del otro, aunque el
    # rango real (abajo) sigue contando a todo el mundo para el ascenso/descenso.
    hidden = await blocked_user_ids(db, user.id)

    standings: list[LeagueStandingEntry] = []
    for idx, (league_entry, member) in enumerate(rows, start=1):
        if member.id not in hidden:
            standings.append(
                LeagueStandingEntry(
                    rank=idx,
                    user_id=member.id,
                    username=member.username,
                    display_name=member.display_name,
                    avatar_emoji=member.avatar_emoji,
                    xp_earned=league_entry.xp_earned,
                    is_current_user=member.id == user.id,
                )
            )
        if league_entry.rank != idx:
            league_entry.rank = idx

    await db.commit()

    zone_size = PROMOTION_ZONE_SIZE if len(standings) >= MIN_LEAGUE_SIZE_FOR_ZONES else 0
    demotion_size = DEMOTION_ZONE_SIZE if len(standings) >= MIN_LEAGUE_SIZE_FOR_ZONES else 0

    return LeagueStandingsResponse(
        league=LeagueRead.model_validate(league),
        week_start=entry.week_start,
        standings=standings,
        promotion_zone=zone_size,
        demotion_zone=demotion_size,
    )


async def get_league_history(db: AsyncSession, user: User) -> list[LeagueHistoryEntry]:
    current_week = week_start_of(date.today())
    result = await db.execute(
        select(LeagueEntry, League)
        .join(League, League.id == LeagueEntry.league_id)
        .where(LeagueEntry.user_id == user.id, LeagueEntry.week_start < current_week)
        .order_by(LeagueEntry.week_start.desc())
    )
    return [
        LeagueHistoryEntry(
            league=LeagueRead.model_validate(league),
            week_start=entry.week_start,
            xp_earned=entry.xp_earned,
            rank=entry.rank,
        )
        for entry, league in result.all()
    ]


async def get_user_badges(db: AsyncSession, user: User) -> list[UserBadgeWithDetail]:
    result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, Badge.id == UserBadge.badge_id)
        .where(UserBadge.user_id == user.id)
        .order_by(UserBadge.earned_at.desc())
    )
    return [
        UserBadgeWithDetail(badge=BadgeRead.model_validate(badge), earned_at=ub.earned_at)
        for ub, badge in result.all()
    ]


async def _todays_missions(
    db: AsyncSession, user: User, today: date
) -> list[tuple[UserMission, Mission]]:
    """Today's (UserMission, Mission) pairs as they currently stand in the DB."""
    result = await db.execute(
        select(UserMission, Mission)
        .join(Mission, Mission.id == UserMission.mission_id)
        .where(UserMission.user_id == user.id, UserMission.date == today)
    )
    return list(result.all())


async def _ensure_today_missions(db: AsyncSession, user: User) -> list[tuple[UserMission, Mission]]:
    """Return today's (UserMission, Mission) pairs for the user, lazily
    auto-assigning a default set of missions the first time they're needed
    on a given day — whether that's a GET /missions call or the very first
    quiz answer of the day."""
    today = date.today()
    rows = await _todays_missions(db, user, today)
    if rows:
        return rows

    templates_result = await db.execute(
        select(Mission).order_by(Mission.id).limit(DEFAULT_DAILY_MISSION_COUNT)
    )
    templates = templates_result.scalars().all()
    if not templates:
        return []

    try:
        # A SAVEPOINT, not a bare flush: the first screen of the day fires
        # /progress/dashboard and /quiz/start almost together, both read "no
        # missions yet", and both insert — so the loser hit
        # uq_user_mission_date and the user got a 500 on their first action of
        # the day. Rolling back to the savepoint leaves the outer transaction
        # (XP, streak, the answer itself) intact, and the re-read below picks
        # up whichever request won.
        async with db.begin_nested():
            db.add_all(
                [
                    UserMission(
                        user_id=user.id,
                        mission_id=template.id,
                        progress=0,
                        completed=False,
                        date=today,
                    )
                    for template in templates
                ]
            )
    except IntegrityError:
        pass

    return await _todays_missions(db, user, today)


async def get_today_missions(db: AsyncSession, user: User) -> list[UserMissionRead]:
    rows = await _ensure_today_missions(db, user)
    await db.commit()

    return [
        UserMissionRead(
            mission=MissionRead.model_validate(mission),
            progress=um.progress,
            completed=um.completed,
            date=um.date,
        )
        for um, mission in rows
    ]


# Criterios de insignia que `award_badges` sabe calcular. Un criterio del seed que
# no esté aquí es una insignia imposible; `test_gamification` lo vigila.
BADGE_CRITERIA_TYPES = frozenset(
    {
        "streak", "total_xp", "level", "questions_answered", "skills_mastered",
        "perfect_session", "referrals_credited",
    }
)
PERFECT_SESSION_MIN_ANSWERS = 10


async def award_badges(db: AsyncSession, user: User) -> list[str]:
    """Grant any badges whose criteria the user now satisfies. Idempotent —
    a UNIQUE (user_id, badge_id) constraint plus an earned-set guard prevents
    duplicates. Returns the list of newly-awarded badge ids."""
    badges = (await db.execute(select(Badge))).scalars().all()
    if not badges:
        return []
    # La sesión de la app no hace autoflush: sin esto las estadísticas de abajo leen
    # la base sin la respuesta que se acaba de contar (la sesión 10/10 sale 9/9).
    await db.flush()

    earned_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
    )
    earned = {row[0] for row in earned_result.all()}

    # Aggregate stats needed by the criteria types.
    total_questions = (
        await db.execute(
            select(func.count(Response.id))
            .join(StudySession, StudySession.id == Response.session_id)
            .where(StudySession.user_id == user.id)
        )
    ).scalar_one() or 0
    skills_mastered = (
        await db.execute(
            select(func.count(UserSkillState.id)).where(
                UserSkillState.user_id == user.id, UserSkillState.p_known >= 0.95
            )
        )
    ).scalar_one() or 0

    # «Sesión perfecta 10/10»: al menos 10 respuestas y todas correctas en una misma
    # sesión. Faltaba y la insignia «Perfeccionista» no se concedía nunca (39.5).
    perfect_sessions = (
        await db.execute(
            select(func.count(StudySession.id)).where(
                StudySession.user_id == user.id,
                StudySession.questions_answered >= PERFECT_SESSION_MIN_ANSWERS,
                StudySession.correct_count == StudySession.questions_answered,
            )
        )
    ).scalar_one() or 0

    # «Embajador» (ADR-35, ECONOMIA §3.3): referidos ya abonados.
    referrals_credited = (
        await db.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user.id, Referral.status == "credited"
            )
        )
    ).scalar_one() or 0

    stat_for = {
        "streak": user.current_streak,
        "total_xp": user.total_xp,
        "level": user.level,
        "questions_answered": int(total_questions),
        "skills_mastered": int(skills_mastered),
        "perfect_session": int(perfect_sessions),
        "referrals_credited": int(referrals_credited),
    }

    newly: list[str] = []
    for badge in badges:
        if badge.id in earned:
            continue
        value = stat_for.get(badge.criteria_type)
        if value is not None and value >= badge.criteria_value:
            db.add(UserBadge(user_id=user.id, badge_id=badge.id))
            newly.append(badge.id)
    return newly


async def apply_quiz_event(
    db: AsyncSession, user: User, correct: bool, xp_earned: int, combo: int
) -> None:
    """Advance today's mission progress after a quiz answer, auto-assigning
    today's missions first if this is the user's first event of the day."""
    rows = await _ensure_today_missions(db, user)
    for um, mission in rows:
        if um.completed:
            continue
        if mission.type == "questions_answered" or mission.type == "correct_answers" and correct:
            um.progress += 1
        elif mission.type == "xp_earned":
            um.progress += xp_earned
        elif mission.type == "perfect_combo":
            um.progress = max(um.progress, combo)
        else:
            continue

        if um.progress >= mission.target_value:
            um.progress = mission.target_value
            um.completed = True

    # Grant any badges the user just qualified for (streak, xp, level, etc.).
    await award_badges(db, user)
