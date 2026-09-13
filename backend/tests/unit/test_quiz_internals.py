"""Unit tests for the quiz service internals.

The integration tests exercise the endpoints; these pin the decision logic the
endpoints delegate to — the BKT prerequisite gate that enforces "7 tracks
lineales, no hay atajos", the streak rules (which must never punish unfairly),
and the FSRS grade/XP mapping.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.content import Module, Skill, Track
from app.models.user import User, UserSkillState
from app.services.quiz import (
    _calculate_xp,
    _candidate_skill_ids,
    _current_combo,
    _ensure_aware,
    _grade_from_response,
    _is_module_unlocked,
    _level_from_xp,
    _select_skill,
    _update_streak,
    _weighted_choice,
)

NOW = datetime(2026, 3, 10, 9, 0, 0, tzinfo=UTC)


# ── fixtures ──────────────────────────────────────────────────────────────────


async def build_track(
    db,
    track_id: str = "trkA",
    *,
    n_modules: int = 2,
    skills_per_module: int = 2,
    unlock: float = 0.7,
) -> list[Module]:
    track = Track(id=track_id, name_es="T", name_en="T", order=1)
    db.add(track)
    modules: list[Module] = []
    for m in range(n_modules):
        module = Module(
            id=f"{track_id}_m{m}",
            track_id=track_id,
            name_es="M",
            name_en="M",
            order=m,
            min_mastery_to_unlock=unlock,
        )
        db.add(module)
        modules.append(module)
        for s in range(skills_per_module):
            db.add(
                Skill(
                    id=f"{track_id}_m{m}_s{s}",
                    module_id=module.id,
                    name_es="S",
                    name_en="S",
                    order=s,
                )
            )
    await db.commit()
    return modules


async def set_mastery(db, user_id: uuid.UUID, skill_id: str, p_known: float) -> None:
    db.add(UserSkillState(user_id=user_id, skill_id=skill_id, p_known=p_known))
    await db.commit()


# ── _ensure_aware ─────────────────────────────────────────────────────────────


class TestEnsureAware:
    def test_none_passes_through(self) -> None:
        assert _ensure_aware(None) is None

    def test_naive_becomes_utc(self) -> None:
        got = _ensure_aware(datetime(2026, 1, 1, 12, 0, 0))  # noqa: DTZ001 — a naive datetime is the input under test
        assert got is not None
        assert got.tzinfo is UTC

    def test_aware_is_left_alone(self) -> None:
        original = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert _ensure_aware(original) is original

    def test_result_is_subtractable_from_an_aware_now(self) -> None:
        # The exact crash this helper exists to prevent (SQLite returns naive).
        delta = NOW - _ensure_aware(datetime(2026, 3, 9, 9, 0, 0))  # type: ignore[operator]  # noqa: DTZ001 — naive on purpose
        assert delta == timedelta(days=1)


# ── _grade_from_response ──────────────────────────────────────────────────────


class TestGradeFromResponse:
    def test_wrong_is_always_again(self) -> None:
        assert _grade_from_response(False, 1, 15000) == 1
        assert _grade_from_response(False, 999999, 15000) == 1

    def test_fast_correct_is_easy(self) -> None:
        assert _grade_from_response(True, 4_000, 15_000) == 4  # ratio 0.27

    def test_within_expected_is_good(self) -> None:
        assert _grade_from_response(True, 4_500, 15_000) == 3  # ratio 0.30
        assert _grade_from_response(True, 14_999, 15_000) == 3

    def test_slow_correct_is_hard(self) -> None:
        assert _grade_from_response(True, 15_000, 15_000) == 2
        assert _grade_from_response(True, 60_000, 15_000) == 2

    def test_zero_expected_time_does_not_divide_by_zero(self) -> None:
        assert _grade_from_response(True, 5_000, 0) == 2

    def test_negative_expected_time_is_clamped(self) -> None:
        assert _grade_from_response(True, 5_000, -100) == 2


# ── _calculate_xp / _level_from_xp ────────────────────────────────────────────


class TestCalculateXp:
    def test_wrong_answer_still_earns_a_little(self) -> None:
        assert _calculate_xp(False, 20, 4) == 3

    @pytest.mark.parametrize(
        ("combo", "expected"), [(0, 10), (2, 10), (3, 20), (6, 20), (7, 30), (14, 30), (15, 50)]
    )
    def test_combo_tiers(self, combo: int, expected: int) -> None:
        assert _calculate_xp(True, combo, 3) == expected

    def test_easy_grade_adds_speed_bonus(self) -> None:
        assert _calculate_xp(True, 0, 4) == 15
        assert _calculate_xp(True, 15, 4) == 55

    def test_no_bonus_for_grades_other_than_easy(self) -> None:
        assert _calculate_xp(True, 0, 2) == 10
        assert _calculate_xp(True, 0, 3) == 10


class TestLevelFromXp:
    @pytest.mark.parametrize(
        ("xp", "level"), [(0, 1), (1, 1), (499, 1), (500, 2), (999, 2), (1000, 3), (5000, 11)]
    )
    def test_levels(self, xp: int, level: int) -> None:
        assert _level_from_xp(xp) == level

    def test_never_below_one(self) -> None:
        assert _level_from_xp(-100) >= 1


# ── _update_streak ────────────────────────────────────────────────────────────


def make_user(**over: object) -> User:
    u = User(
        id=uuid.uuid4(),
        email="s@w.test",
        username="s",
        hashed_password="x",
        display_name="S",
        language="es",
    )
    u.current_streak = 0
    u.max_streak = 0
    u.streak_freeze_available = 0
    u.last_active = None
    for k, v in over.items():
        setattr(u, k, v)
    return u


class TestUpdateStreak:
    def test_first_ever_session_starts_at_one(self) -> None:
        u = make_user()
        _update_streak(u, NOW)
        assert u.current_streak == 1
        assert u.max_streak == 1
        assert u.last_active == NOW

    def test_second_session_same_day_does_not_double_count(self) -> None:
        u = make_user(last_active=NOW - timedelta(hours=3), current_streak=4, max_streak=4)
        _update_streak(u, NOW)
        assert u.current_streak == 4

    def test_consecutive_day_increments(self) -> None:
        u = make_user(last_active=NOW - timedelta(days=1), current_streak=4, max_streak=4)
        _update_streak(u, NOW)
        assert u.current_streak == 5
        assert u.max_streak == 5

    def test_two_day_gap_without_freeze_resets(self) -> None:
        u = make_user(last_active=NOW - timedelta(days=2), current_streak=9, max_streak=9)
        _update_streak(u, NOW)
        assert u.current_streak == 1
        assert u.max_streak == 9  # the record is kept, not erased

    def test_two_day_gap_spends_a_freeze_and_keeps_the_streak(self) -> None:
        u = make_user(
            last_active=NOW - timedelta(days=2),
            current_streak=9,
            max_streak=9,
            streak_freeze_available=1,
        )
        _update_streak(u, NOW)
        assert u.current_streak == 10
        assert u.streak_freeze_available == 0

    def test_freeze_does_not_cover_a_three_day_gap(self) -> None:
        u = make_user(
            last_active=NOW - timedelta(days=3),
            current_streak=9,
            max_streak=9,
            streak_freeze_available=1,
        )
        _update_streak(u, NOW)
        assert u.current_streak == 1
        assert u.streak_freeze_available == 1  # not spent on a lost cause

    def test_max_streak_never_decreases(self) -> None:
        u = make_user(last_active=NOW - timedelta(days=30), current_streak=30, max_streak=30)
        _update_streak(u, NOW)
        assert u.max_streak == 30


# ── _weighted_choice ──────────────────────────────────────────────────────────


class TestWeightedChoice:
    def test_single_item(self) -> None:
        assert _weighted_choice(["a"], [1.0]) == "a"

    def test_zero_weights_fall_back_to_uniform(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        assert _weighted_choice(["a", "b"], [0.0, 0.0]) == "a"

    def test_negative_total_falls_back_to_uniform(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(random, "choice", lambda seq: seq[-1])
        assert _weighted_choice(["a", "b"], [-1.0, -1.0]) == "b"

    def test_first_bucket_selected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(random, "random", lambda: 0.0)
        assert _weighted_choice(["a", "b", "c"], [1.0, 1.0, 1.0]) == "a"

    def test_last_bucket_selected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(random, "random", lambda: 0.999999)
        assert _weighted_choice(["a", "b", "c"], [1.0, 1.0, 1.0]) == "c"

    def test_heavier_weight_wins_more_often(self) -> None:
        random.seed(1234)
        picks = [_weighted_choice(["rare", "common"], [1.0, 9.0]) for _ in range(400)]
        assert picks.count("common") > picks.count("rare")

    def test_always_returns_a_member_of_items(self) -> None:
        random.seed(7)
        for _ in range(100):
            assert _weighted_choice(["a", "b", "c"], [0.1, 0.5, 0.4]) in {"a", "b", "c"}


# ── _is_module_unlocked — the "no hay atajos" gate ────────────────────────────


class TestIsModuleUnlocked:
    @pytest.mark.asyncio
    async def test_first_module_is_always_open(self, db_session, user: User) -> None:
        modules = await build_track(db_session)
        assert await _is_module_unlocked(db_session, user.id, modules[0]) is True

    @pytest.mark.asyncio
    async def test_second_module_is_locked_for_a_new_user(self, db_session, user: User) -> None:
        modules = await build_track(db_session)
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is False

    @pytest.mark.asyncio
    async def test_unlocks_when_previous_average_clears_threshold(
        self, db_session, user: User
    ) -> None:
        modules = await build_track(db_session, unlock=0.7)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.8)
        await set_mastery(db_session, user.id, "trkA_m0_s1", 0.9)
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is True

    @pytest.mark.asyncio
    async def test_stays_locked_when_average_falls_short(self, db_session, user: User) -> None:
        modules = await build_track(db_session, unlock=0.7)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.6)
        await set_mastery(db_session, user.id, "trkA_m0_s1", 0.6)
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is False

    @pytest.mark.asyncio
    async def test_unattempted_skills_count_as_zero(self, db_session, user: User) -> None:
        """One mastered skill must not unlock a module whose other skill was
        never touched — that would be the shortcut the design forbids."""
        modules = await build_track(db_session, unlock=0.7)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 1.0)
        # s1 has no state at all -> padded to 0.0 -> average 0.5 < 0.7
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is False

    @pytest.mark.asyncio
    async def test_threshold_is_inclusive(self, db_session, user: User) -> None:
        modules = await build_track(db_session, unlock=0.7)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.7)
        await set_mastery(db_session, user.id, "trkA_m0_s1", 0.7)
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is True

    @pytest.mark.asyncio
    async def test_missing_previous_module_opens_the_gate(self, db_session, user: User) -> None:
        # order 5 with no order-4 sibling: don't strand the user behind a hole.
        track = Track(id="trkB", name_es="T", name_en="T", order=2)
        db_session.add(track)
        orphan = Module(
            id="trkB_m5", track_id="trkB", name_es="M", name_en="M", order=5,
            min_mastery_to_unlock=0.7,
        )
        db_session.add(orphan)
        await db_session.commit()
        assert await _is_module_unlocked(db_session, user.id, orphan) is True

    @pytest.mark.asyncio
    async def test_previous_module_without_skills_opens_the_gate(
        self, db_session, user: User
    ) -> None:
        track = Track(id="trkC", name_es="T", name_en="T", order=3)
        db_session.add(track)
        empty = Module(
            id="trkC_m0", track_id="trkC", name_es="M", name_en="M", order=0,
            min_mastery_to_unlock=0.7,
        )
        second = Module(
            id="trkC_m1", track_id="trkC", name_es="M", name_en="M", order=1,
            min_mastery_to_unlock=0.7,
        )
        db_session.add_all([empty, second])
        await db_session.commit()
        assert await _is_module_unlocked(db_session, user.id, second) is True

    @pytest.mark.asyncio
    async def test_negative_order_is_treated_as_first(self, db_session, user: User) -> None:
        track = Track(id="trkD", name_es="T", name_en="T", order=4)
        db_session.add(track)
        weird = Module(
            id="trkD_mneg", track_id="trkD", name_es="M", name_en="M", order=-1,
            min_mastery_to_unlock=0.7,
        )
        db_session.add(weird)
        await db_session.commit()
        assert await _is_module_unlocked(db_session, user.id, weird) is True

    @pytest.mark.asyncio
    async def test_another_users_mastery_does_not_unlock_your_module(
        self, db_session, user: User
    ) -> None:
        modules = await build_track(db_session, unlock=0.7)
        stranger = uuid.uuid4()
        await set_mastery(db_session, stranger, "trkA_m0_s0", 1.0)
        await set_mastery(db_session, stranger, "trkA_m0_s1", 1.0)
        assert await _is_module_unlocked(db_session, user.id, modules[1]) is False


# ── _candidate_skill_ids ──────────────────────────────────────────────────────


class TestCandidateSkillIds:
    @pytest.mark.asyncio
    async def test_explicit_skill_short_circuits(self, db_session, user: User) -> None:
        got = await _candidate_skill_ids(db_session, user, "study", None, "whatever")
        assert got == ["whatever"]

    @pytest.mark.asyncio
    async def test_study_mode_returns_only_unlocked_skills(
        self, db_session, user: User
    ) -> None:
        await build_track(db_session)
        got = await _candidate_skill_ids(db_session, user, "study", "trkA", None)
        assert set(got) == {"trkA_m0_s0", "trkA_m0_s1"}  # module 1 still locked

    @pytest.mark.asyncio
    async def test_no_content_returns_empty(self, db_session, user: User) -> None:
        assert await _candidate_skill_ids(db_session, user, "study", None, None) == []

    @pytest.mark.asyncio
    async def test_track_filter_excludes_other_tracks(self, db_session, user: User) -> None:
        await build_track(db_session, "trkA")
        await build_track(db_session, "trkB")
        got = await _candidate_skill_ids(db_session, user, "study", "trkB", None)
        assert all(sid.startswith("trkB") for sid in got)

    @pytest.mark.asyncio
    async def test_mastered_skills_are_dropped(self, db_session, user: User) -> None:
        await build_track(db_session)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.99)
        got = await _candidate_skill_ids(db_session, user, "study", "trkA", None)
        assert got == ["trkA_m0_s1"]

    @pytest.mark.asyncio
    async def test_all_mastered_falls_back_to_everything(self, db_session, user: User) -> None:
        """Never hand the selector an empty pool just because the user is good."""
        await build_track(db_session, n_modules=1)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.99)
        await set_mastery(db_session, user.id, "trkA_m0_s1", 0.99)
        got = await _candidate_skill_ids(db_session, user, "study", "trkA", None)
        assert set(got) == {"trkA_m0_s0", "trkA_m0_s1"}

    @pytest.mark.asyncio
    async def test_review_mode_returns_due_skills(self, db_session, user: User) -> None:
        await build_track(db_session)
        db_session.add(
            UserSkillState(
                user_id=user.id,
                skill_id="trkA_m0_s0",
                p_known=0.5,
                fsrs_due=datetime.now(UTC) - timedelta(days=1),
            )
        )
        await db_session.commit()
        got = await _candidate_skill_ids(db_session, user, "review", None, None)
        assert got == ["trkA_m0_s0"]

    @pytest.mark.asyncio
    async def test_review_mode_falls_through_when_nothing_is_due(
        self, db_session, user: User
    ) -> None:
        await build_track(db_session)
        got = await _candidate_skill_ids(db_session, user, "review", "trkA", None)
        assert set(got) == {"trkA_m0_s0", "trkA_m0_s1"}

    @pytest.mark.asyncio
    async def test_review_mode_ignores_future_due_dates(self, db_session, user: User) -> None:
        await build_track(db_session)
        db_session.add(
            UserSkillState(
                user_id=user.id,
                skill_id="trkA_m0_s0",
                p_known=0.5,
                fsrs_due=datetime.now(UTC) + timedelta(days=5),
            )
        )
        await db_session.commit()
        got = await _candidate_skill_ids(db_session, user, "review", "trkA", None)
        assert set(got) == {"trkA_m0_s0", "trkA_m0_s1"}  # fell through to study


# ── _select_skill ─────────────────────────────────────────────────────────────


class TestSelectSkill:
    @pytest.mark.asyncio
    async def test_empty_pool_returns_none(self, db_session, user: User) -> None:
        assert await _select_skill(db_session, user, []) is None

    @pytest.mark.asyncio
    async def test_single_candidate_short_circuits(self, db_session, user: User) -> None:
        assert await _select_skill(db_session, user, ["only"]) == "only"

    @pytest.mark.asyncio
    async def test_returns_a_candidate(self, db_session, user: User) -> None:
        await build_track(db_session)
        got = await _select_skill(db_session, user, ["trkA_m0_s0", "trkA_m0_s1"])
        assert got in {"trkA_m0_s0", "trkA_m0_s1"}

    @pytest.mark.asyncio
    async def test_weaker_skill_is_favoured(self, db_session, user: User) -> None:
        await build_track(db_session)
        await set_mastery(db_session, user.id, "trkA_m0_s0", 0.05)
        await set_mastery(db_session, user.id, "trkA_m0_s1", 0.95)
        random.seed(99)
        picks = [
            await _select_skill(db_session, user, ["trkA_m0_s0", "trkA_m0_s1"])
            for _ in range(60)
        ]
        assert picks.count("trkA_m0_s0") > picks.count("trkA_m0_s1")


# ── _current_combo ────────────────────────────────────────────────────────────


class TestCurrentCombo:
    @pytest.mark.asyncio
    async def test_no_responses_is_zero(self, db_session) -> None:
        assert await _current_combo(db_session, uuid.uuid4()) == 0
