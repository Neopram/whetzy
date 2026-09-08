"""Tests for app/services/gamification/service.py

Coverage target: >=85% of app/services/gamification/
No SQLAlchemy mocks — uses the real db_session (SQLite in-memory) from conftest.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Badge, League, LeagueEntry, Mission
from app.models.user import User, UserBadge
from app.services.gamification.service import (
    apply_quiz_event,
    award_badges,
    get_current_standings,
    get_league_history,
    get_or_create_current_entry,
    get_today_missions,
    get_user_badges,
    week_start_of,
)


# ── Factories ─────────────────────────────────────────────────────────────────


def _league(tier: str = "bronze", min_xp: int = 0) -> League:
    return League(
        id=f"lg_{tier}_{uuid.uuid4().hex[:6]}",
        name=tier.capitalize(),
        tier=tier,
        min_xp=min_xp,
    )


def _badge(
    criteria_type: str = "total_xp",
    criteria_value: int = 100,
    bid: str | None = None,
) -> Badge:
    return Badge(
        id=bid or f"badge_{uuid.uuid4().hex[:8]}",
        name_es="Nombre",
        name_en="Name",
        icon="🏅",
        description_es="",
        description_en="",
        criteria_type=criteria_type,
        criteria_value=criteria_value,
    )


def _mission(mtype: str = "questions_answered", target: int = 5) -> Mission:
    return Mission(
        id=f"mis_{mtype}_{uuid.uuid4().hex[:6]}",
        type=mtype,
        target_value=target,
        xp_reward=10,
        name_es=f"Misión {mtype}",
        name_en=f"Mission {mtype}",
    )


def _user2(db_session: AsyncSession) -> User:
    """Return a second unsaved User (caller must add + commit)."""
    return User(
        id=uuid.uuid4(),
        email=f"u2-{uuid.uuid4().hex[:8]}@test.com",
        username=f"u2{uuid.uuid4().hex[:6]}",
        hashed_password="x",
        display_name="User Two",
    )


# ─────────────────────────────────────────────────────────────────────────────
# week_start_of — pure function
# ─────────────────────────────────────────────────────────────────────────────


class TestWeekStartOf:
    def test_monday_returns_same_date(self):
        monday = date(2024, 1, 1)  # weekday() == 0
        assert week_start_of(monday) == monday

    def test_wednesday_returns_monday(self):
        assert week_start_of(date(2024, 1, 3)) == date(2024, 1, 1)

    def test_sunday_returns_monday_of_same_week(self):
        assert week_start_of(date(2024, 1, 7)) == date(2024, 1, 1)

    def test_friday_returns_monday(self):
        assert week_start_of(date(2024, 1, 5)) == date(2024, 1, 1)

    def test_result_is_always_monday(self):
        """Every day in a 14-day window maps to a Monday."""
        start = date(2024, 6, 10)  # Known Monday
        for offset in range(14):
            d = start + timedelta(days=offset)
            ws = week_start_of(d)
            assert ws.weekday() == 0, f"week_start_of({d}) = {ws} is not Monday"

    def test_cross_month_boundary(self):
        # 2024-03-31 is a Sunday → week starts 2024-03-25 (Monday)
        assert week_start_of(date(2024, 3, 31)) == date(2024, 3, 25)


# ─────────────────────────────────────────────────────────────────────────────
# get_or_create_current_entry
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOrCreateCurrentEntry:
    async def test_no_league_returns_none(self, db_session: AsyncSession, user: User):
        result = await get_or_create_current_entry(db_session, user)
        assert result is None

    async def test_creates_entry_first_time(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)

        assert entry is not None
        assert entry.user_id == user.id
        assert entry.xp_earned == 0
        assert entry.week_start == week_start_of(date.today())

    async def test_second_call_returns_same_entry(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        entry1 = await get_or_create_current_entry(db_session, user)
        await db_session.commit()
        entry2 = await get_or_create_current_entry(db_session, user)

        assert entry1 is not None and entry2 is not None
        assert entry1.id == entry2.id

    async def test_uses_lowest_tier_when_no_prior_week(self, db_session: AsyncSession, user: User):
        gold = _league("gold", min_xp=500)
        bronze = _league("bronze", min_xp=0)
        db_session.add_all([gold, bronze])
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)

        assert entry is not None
        assert entry.league_id == bronze.id  # lowest min_xp

    async def test_carries_over_league_from_prior_week(self, db_session: AsyncSession, user: User):
        silver = _league("silver", min_xp=100)
        db_session.add(silver)
        await db_session.commit()

        prev_week = week_start_of(date.today()) - timedelta(weeks=1)
        prev_entry = LeagueEntry(
            user_id=user.id,
            league_id=silver.id,
            week_start=prev_week,
            xp_earned=300,
        )
        db_session.add(prev_entry)
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)

        assert entry is not None
        assert entry.league_id == silver.id

    async def test_does_not_duplicate_on_repeated_calls(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        await get_or_create_current_entry(db_session, user)
        await db_session.commit()
        await get_or_create_current_entry(db_session, user)
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(LeagueEntry).where(
                LeagueEntry.user_id == user.id,
                LeagueEntry.week_start == week_start_of(date.today()),
            )
        )
        rows = result.scalars().all()
        assert len(rows) == 1


# ─────────────────────────────────────────────────────────────────────────────
# XP weekly tracking
# ─────────────────────────────────────────────────────────────────────────────


class TestXpWeekly:
    async def test_xp_starts_at_zero(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)
        assert entry is not None
        assert entry.xp_earned == 0

    async def test_xp_update_persists(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)
        assert entry is not None
        entry.xp_earned = 150
        await db_session.commit()
        await db_session.refresh(entry)

        assert entry.xp_earned == 150

    async def test_xp_visible_in_standings(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        entry = await get_or_create_current_entry(db_session, user)
        assert entry is not None
        entry.xp_earned = 77
        await db_session.commit()

        standings = await get_current_standings(db_session, user)
        assert standings is not None
        assert standings.standings[0].xp_earned == 77


# ─────────────────────────────────────────────────────────────────────────────
# get_current_standings
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCurrentStandings:
    async def test_no_league_returns_none(self, db_session: AsyncSession, user: User):
        result = await get_current_standings(db_session, user)
        assert result is None

    async def test_single_user_is_rank_1(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert len(resp.standings) == 1
        assert resp.standings[0].rank == 1
        assert resp.standings[0].is_current_user is True

    async def test_no_zones_for_small_group(self, db_session: AsyncSession, user: User):
        """< 10 members → promotion_zone and demotion_zone are 0."""
        db_session.add(_league())
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert resp.promotion_zone == 0
        assert resp.demotion_zone == 0

    async def test_ranking_ordered_by_xp_desc(self, db_session: AsyncSession, user: User):
        league = _league()
        db_session.add(league)
        other = _user2(db_session)
        db_session.add(other)
        await db_session.commit()

        today_week = week_start_of(date.today())
        db_session.add_all([
            LeagueEntry(user_id=user.id, league_id=league.id, week_start=today_week, xp_earned=10),
            LeagueEntry(user_id=other.id, league_id=league.id, week_start=today_week, xp_earned=200),
        ])
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert resp.standings[0].user_id == other.id
        assert resp.standings[0].rank == 1
        assert resp.standings[1].is_current_user is True
        assert resp.standings[1].rank == 2

    async def test_week_start_is_current_week(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert resp.week_start == week_start_of(date.today())

    async def test_league_fields_populated(self, db_session: AsyncSession, user: User):
        db_session.add(_league("gold", min_xp=500))
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert resp.league.tier == "gold"
        assert resp.league.min_xp == 500

    async def test_zones_present_for_large_group(self, db_session: AsyncSession, user: User):
        """10 or more members → promotion_zone and demotion_zone > 0."""
        league = _league()
        db_session.add(league)
        await db_session.commit()

        today_week = week_start_of(date.today())
        # Add 9 extra users so total is 10
        extra_entries = []
        for _ in range(9):
            extra = _user2(db_session)
            db_session.add(extra)
            await db_session.flush()
            extra_entries.append(
                LeagueEntry(user_id=extra.id, league_id=league.id, week_start=today_week, xp_earned=5)
            )
        db_session.add_all(extra_entries)
        db_session.add(
            LeagueEntry(user_id=user.id, league_id=league.id, week_start=today_week, xp_earned=1)
        )
        await db_session.commit()

        resp = await get_current_standings(db_session, user)

        assert resp is not None
        assert len(resp.standings) == 10
        assert resp.promotion_zone > 0
        assert resp.demotion_zone > 0


# ─────────────────────────────────────────────────────────────────────────────
# get_league_history
# ─────────────────────────────────────────────────────────────────────────────


class TestGetLeagueHistory:
    async def test_empty_history(self, db_session: AsyncSession, user: User):
        result = await get_league_history(db_session, user)
        assert result == []

    async def test_prior_week_appears_in_history(self, db_session: AsyncSession, user: User):
        league = _league()
        db_session.add(league)
        await db_session.commit()

        prev_week = week_start_of(date.today()) - timedelta(weeks=1)
        db_session.add(
            LeagueEntry(user_id=user.id, league_id=league.id, week_start=prev_week, xp_earned=75, rank=3)
        )
        await db_session.commit()

        history = await get_league_history(db_session, user)

        assert len(history) == 1
        assert history[0].xp_earned == 75
        assert history[0].rank == 3
        assert history[0].week_start == prev_week

    async def test_current_week_excluded_from_history(self, db_session: AsyncSession, user: User):
        db_session.add(_league())
        await db_session.commit()

        await get_or_create_current_entry(db_session, user)
        await db_session.commit()

        history = await get_league_history(db_session, user)
        assert history == []

    async def test_history_ordered_newest_first(self, db_session: AsyncSession, user: User):
        league = _league()
        db_session.add(league)
        await db_session.commit()

        today_week = week_start_of(date.today())
        week1 = today_week - timedelta(weeks=2)
        week2 = today_week - timedelta(weeks=1)
        db_session.add_all([
            LeagueEntry(user_id=user.id, league_id=league.id, week_start=week1, xp_earned=10),
            LeagueEntry(user_id=user.id, league_id=league.id, week_start=week2, xp_earned=20),
        ])
        await db_session.commit()

        history = await get_league_history(db_session, user)

        assert len(history) == 2
        assert history[0].week_start == week2
        assert history[1].week_start == week1


# ─────────────────────────────────────────────────────────────────────────────
# get_user_badges
# ─────────────────────────────────────────────────────────────────────────────


class TestGetUserBadges:
    async def test_no_badges_returns_empty(self, db_session: AsyncSession, user: User):
        result = await get_user_badges(db_session, user)
        assert result == []

    async def test_earned_badge_appears(self, db_session: AsyncSession, user: User):
        badge = _badge("total_xp", 100)
        db_session.add(badge)
        await db_session.commit()
        db_session.add(UserBadge(user_id=user.id, badge_id=badge.id))
        await db_session.commit()

        result = await get_user_badges(db_session, user)

        assert len(result) == 1
        assert result[0].badge.id == badge.id
        assert result[0].badge.criteria_type == "total_xp"

    async def test_other_user_badge_not_visible(self, db_session: AsyncSession, user: User):
        badge = _badge("streak", 7)
        other = _user2(db_session)
        db_session.add_all([badge, other])
        await db_session.commit()
        db_session.add(UserBadge(user_id=other.id, badge_id=badge.id))
        await db_session.commit()

        result = await get_user_badges(db_session, user)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# award_badges
# ─────────────────────────────────────────────────────────────────────────────


class TestAwardBadges:
    async def test_no_badge_definitions_returns_empty(self, db_session: AsyncSession, user: User):
        result = await award_badges(db_session, user)
        assert result == []

    async def test_awards_when_total_xp_met(self, db_session: AsyncSession, user: User):
        user.total_xp = 500
        badge = _badge("total_xp", 100, bid="xp_badge_500")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert "xp_badge_500" in newly

    async def test_skips_when_criteria_not_met(self, db_session: AsyncSession, user: User):
        user.total_xp = 50
        badge = _badge("total_xp", 100, bid="xp_badge_high")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert newly == []

    async def test_idempotent_no_duplicate(self, db_session: AsyncSession, user: User):
        user.total_xp = 999
        badge = _badge("total_xp", 100, bid="idem_badge")
        db_session.add(badge)
        await db_session.commit()

        first = await award_badges(db_session, user)
        await db_session.commit()
        second = await award_badges(db_session, user)

        assert "idem_badge" in first
        assert second == []

    async def test_awards_streak_badge(self, db_session: AsyncSession, user: User):
        user.current_streak = 7
        badge = _badge("streak", 7, bid="streak_7")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert "streak_7" in newly

    async def test_awards_level_badge(self, db_session: AsyncSession, user: User):
        user.level = 5
        badge = _badge("level", 5, bid="level_5")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert "level_5" in newly

    async def test_exact_boundary_value_awarded(self, db_session: AsyncSession, user: User):
        user.total_xp = 100
        badge = _badge("total_xp", 100, bid="exact_100")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert "exact_100" in newly

    async def test_unknown_criteria_type_skipped(self, db_session: AsyncSession, user: User):
        badge = _badge("unknown_type", 0, bid="unknown_badge")
        db_session.add(badge)
        await db_session.commit()

        newly = await award_badges(db_session, user)
        assert newly == []


# ─────────────────────────────────────────────────────────────────────────────
# get_today_missions / _ensure_today_missions
# ─────────────────────────────────────────────────────────────────────────────


class TestGetTodayMissions:
    async def test_no_mission_templates_returns_empty(self, db_session: AsyncSession, user: User):
        result = await get_today_missions(db_session, user)
        assert result == []

    async def test_auto_assigns_on_first_call(self, db_session: AsyncSession, user: User):
        db_session.add_all([
            _mission("questions_answered", 5),
            _mission("correct_answers", 3),
        ])
        await db_session.commit()

        result = await get_today_missions(db_session, user)

        assert len(result) == 2
        types = {r.mission.type for r in result}
        assert "questions_answered" in types
        assert "correct_answers" in types

    async def test_second_call_is_idempotent(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("questions_answered", 5))
        await db_session.commit()

        result1 = await get_today_missions(db_session, user)
        result2 = await get_today_missions(db_session, user)

        assert len(result1) == len(result2) == 1
        assert result1[0].mission.id == result2[0].mission.id

    async def test_initial_progress_is_zero(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("xp_earned", 100))
        await db_session.commit()

        result = await get_today_missions(db_session, user)

        assert len(result) == 1
        assert result[0].progress == 0
        assert result[0].completed is False

    async def test_date_is_today(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("questions_answered", 3))
        await db_session.commit()

        result = await get_today_missions(db_session, user)

        assert result[0].date == date.today()


# ─────────────────────────────────────────────────────────────────────────────
# apply_quiz_event
# ─────────────────────────────────────────────────────────────────────────────


class TestApplyQuizEvent:
    async def test_questions_answered_increments(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("questions_answered", 10))
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=False, xp_earned=5, combo=0)
        await db_session.commit()

        result = await get_today_missions(db_session, user)
        assert result[0].progress == 1

    async def test_correct_answers_only_on_correct(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("correct_answers", 5))
        await db_session.commit()

        # Wrong answer — no progress
        await apply_quiz_event(db_session, user, correct=False, xp_earned=0, combo=0)
        await db_session.commit()
        result = await get_today_missions(db_session, user)
        assert result[0].progress == 0

        # Correct answer — progresses
        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=1)
        await db_session.commit()
        result = await get_today_missions(db_session, user)
        assert result[0].progress == 1

    async def test_xp_earned_adds_xp_amount(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("xp_earned", 100))
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=30, combo=1)
        await db_session.commit()

        result = await get_today_missions(db_session, user)
        assert result[0].progress == 30

    async def test_perfect_combo_tracks_max(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("perfect_combo", 10))
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=5)
        await db_session.commit()
        result = await get_today_missions(db_session, user)
        assert result[0].progress == 5

        # Lower combo → no change
        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=2)
        await db_session.commit()
        result = await get_today_missions(db_session, user)
        assert result[0].progress == 5

        # Higher combo → updates
        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=9)
        await db_session.commit()
        result = await get_today_missions(db_session, user)
        assert result[0].progress == 9

    async def test_mission_completes_at_target(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("questions_answered", 2))
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=1)
        await db_session.commit()
        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=1)
        await db_session.commit()

        result = await get_today_missions(db_session, user)
        assert result[0].completed is True
        assert result[0].progress == 2

    async def test_completed_mission_not_advanced_further(self, db_session: AsyncSession, user: User):
        db_session.add(_mission("questions_answered", 1))
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=1)
        await db_session.commit()
        # Fire another event after completion
        await apply_quiz_event(db_session, user, correct=True, xp_earned=10, combo=1)
        await db_session.commit()

        result = await get_today_missions(db_session, user)
        assert result[0].completed is True
        assert result[0].progress == 1  # still capped

    async def test_apply_quiz_triggers_badge_award(self, db_session: AsyncSession, user: User):
        """apply_quiz_event calls award_badges internally."""
        user.total_xp = 999
        badge = _badge("total_xp", 999, bid="quiz_badge_trigger")
        db_session.add_all([badge, _mission("questions_answered", 100)])
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=1, combo=1)
        await db_session.commit()

        badges = await get_user_badges(db_session, user)
        assert any(b.badge.id == "quiz_badge_trigger" for b in badges)

    async def test_multiple_mission_types_updated_together(self, db_session: AsyncSession, user: User):
        db_session.add_all([
            _mission("questions_answered", 10),
            _mission("correct_answers", 10),
            _mission("xp_earned", 100),
        ])
        await db_session.commit()

        await apply_quiz_event(db_session, user, correct=True, xp_earned=20, combo=1)
        await db_session.commit()

        result = await get_today_missions(db_session, user)
        by_type = {r.mission.type: r.progress for r in result}
        assert by_type["questions_answered"] == 1
        assert by_type["correct_answers"] == 1
        assert by_type["xp_earned"] == 20
