"""Unit tests for the unified AdaptiveScheduler (FSRS + Elo + BKT + bandits)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import pytest

from app.services.engine.bkt import SkillState
from app.services.engine.elo import EloEntity
from app.services.engine.fsrs import Card
from app.services.engine.scheduler import (
    AdaptiveScheduler,
    QuestionCandidate,
    SessionConfig,
    SessionState,
)

# Naive UTC: matches the codebase convention (`datetime.utcnow()` in the engine).
NOW = datetime(2026, 1, 15, 12, 0, 0)  # noqa: DTZ001


def make_candidate(
    qid: str,
    *,
    skill_ids: list[str] | None = None,
    rating: float = 1500.0,
    is_new: bool = True,
    due: datetime | None = None,
    reps: int = 0,
) -> QuestionCandidate:
    card = Card(due=due, reps=reps)
    if reps > 0:
        card.state = "review"
        card.stability = 5.0
        card.difficulty = 5.0
    return QuestionCandidate(
        question_id=qid,
        skill_ids=skill_ids if skill_ids is not None else ["sk01"],
        elo_entity=EloEntity(rating=rating),
        fsrs_card=card,
        is_new=is_new,
    )


@pytest.fixture
def scheduler() -> AdaptiveScheduler:
    return AdaptiveScheduler()


@pytest.fixture
def user() -> EloEntity:
    return EloEntity(rating=1500.0)


@pytest.fixture
def session() -> SessionState:
    return SessionState()


@pytest.fixture
def config() -> SessionConfig:
    return SessionConfig()


class TestSessionState:
    def test_defaults(self, session: SessionState) -> None:
        assert session.questions_answered == 0
        assert session.correct_count == 0
        assert session.combo == 0
        assert session.max_combo == 0
        assert session.xp_earned == 0
        assert session.recent_accuracy == []

    def test_accuracy_empty_is_neutral(self, session: SessionState) -> None:
        assert session.accuracy == 0.5

    def test_accuracy_all_correct(self) -> None:
        s = SessionState(recent_accuracy=[True, True, True])
        assert s.accuracy == pytest.approx(1.0)

    def test_accuracy_mixed(self) -> None:
        s = SessionState(recent_accuracy=[True, False, True, False])
        assert s.accuracy == pytest.approx(0.5)

    def test_rolling_accuracy_empty_is_neutral(self, session: SessionState) -> None:
        assert session.rolling_accuracy == 0.5

    def test_rolling_accuracy_uses_last_eight_only(self) -> None:
        # 10 wrong then 8 right -> rolling looks only at the recent window.
        s = SessionState(recent_accuracy=[False] * 10 + [True] * 8)
        assert s.rolling_accuracy == pytest.approx(1.0)
        assert s.accuracy == pytest.approx(8 / 18)

    def test_rolling_accuracy_partial_window(self) -> None:
        s = SessionState(recent_accuracy=[True, False, True])
        assert s.rolling_accuracy == pytest.approx(2 / 3)


class TestSessionConfig:
    def test_defaults(self, config: SessionConfig) -> None:
        assert config.target_p == 0.75
        assert config.frustration_threshold == 0.50
        assert config.boredom_threshold == 0.92
        assert config.min_questions == 5
        assert config.max_questions == 20
        assert config.time_limit_minutes == 30


class TestQuestionCandidate:
    def test_defaults(self) -> None:
        c = make_candidate("q1")
        assert c.question_id == "q1"
        assert c.is_new is True
        assert c.expected_p == 0.5
        assert c.priority_score == 0.0


class TestAdjustTarget:
    def test_frustrated_user_gets_easier_questions(
        self, scheduler: AdaptiveScheduler, config: SessionConfig
    ) -> None:
        s = SessionState(recent_accuracy=[False] * 8)
        assert scheduler._adjust_target(config, s) == pytest.approx(0.85)

    def test_bored_user_gets_harder_questions(
        self, scheduler: AdaptiveScheduler, config: SessionConfig
    ) -> None:
        s = SessionState(recent_accuracy=[True] * 8)
        assert scheduler._adjust_target(config, s) == pytest.approx(0.65)

    def test_in_the_zone_keeps_target(
        self, scheduler: AdaptiveScheduler, config: SessionConfig
    ) -> None:
        s = SessionState(recent_accuracy=[True, True, True, False])  # 0.75
        assert scheduler._adjust_target(config, s) == pytest.approx(0.75)

    def test_empty_session_keeps_target(
        self, scheduler: AdaptiveScheduler, config: SessionConfig, session: SessionState
    ) -> None:
        assert scheduler._adjust_target(config, session) == pytest.approx(0.75)

    def test_easier_target_is_capped_at_ninety(self, scheduler: AdaptiveScheduler) -> None:
        cfg = SessionConfig(target_p=0.95, frustration_threshold=0.50)
        s = SessionState(recent_accuracy=[False] * 8)
        assert scheduler._adjust_target(cfg, s) == pytest.approx(0.90)

    def test_harder_target_is_floored_at_sixty(self, scheduler: AdaptiveScheduler) -> None:
        cfg = SessionConfig(target_p=0.62, boredom_threshold=0.92)
        s = SessionState(recent_accuracy=[True] * 8)
        assert scheduler._adjust_target(cfg, s) == pytest.approx(0.60)


class TestCorrectnessToGrade:
    def test_wrong_answer_is_again(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._correctness_to_grade(False, 1) == 1
        assert scheduler._correctness_to_grade(False, 999_999) == 1

    def test_fast_correct_is_easy(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._correctness_to_grade(True, 2_999) == 4

    def test_medium_correct_is_good(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._correctness_to_grade(True, 3_000) == 3
        assert scheduler._correctness_to_grade(True, 9_999) == 3

    def test_slow_correct_is_hard(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._correctness_to_grade(True, 10_000) == 2


class TestCalculateXp:
    def test_wrong_answer_still_earns_a_little(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._calculate_xp(False, combo=20, grade=4) == 3

    def test_no_combo_base_xp(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._calculate_xp(True, combo=0, grade=3) == 10

    def test_fast_answer_gets_speed_bonus(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._calculate_xp(True, combo=0, grade=4) == 15

    @pytest.mark.parametrize(
        ("combo", "expected"),
        [(2, 10), (3, 20), (6, 20), (7, 30), (14, 30), (15, 50), (99, 50)],
    )
    def test_combo_multiplier_tiers(
        self, scheduler: AdaptiveScheduler, combo: int, expected: int
    ) -> None:
        assert scheduler._calculate_xp(True, combo=combo, grade=3) == expected

    def test_unknown_grade_gets_no_bonus(self, scheduler: AdaptiveScheduler) -> None:
        assert scheduler._calculate_xp(True, combo=0, grade=9) == 10


class TestSelectNextQuestion:
    def test_no_candidates_returns_none(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        assert scheduler.select_next_question(user, {}, [], session, config, now=NOW) is None

    def test_single_candidate_is_returned(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        c = make_candidate("q1")
        got = scheduler.select_next_question(user, {}, [c], session, config, now=NOW)
        assert got is c

    def test_selection_registers_bandit_arms(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        cands = [make_candidate(f"q{i}") for i in range(3)]
        scheduler.select_next_question(user, {}, cands, session, config, now=NOW)
        for c in cands:
            assert c.question_id in scheduler.question_bandit.arms

    def test_selection_computes_expected_p_from_elo(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        easy = make_candidate("easy", rating=1200.0)
        hard = make_candidate("hard", rating=1800.0)
        scheduler.select_next_question(user, {}, [easy, hard], session, config, now=NOW)
        assert easy.expected_p > 0.5
        assert hard.expected_p < 0.5

    def test_selection_assigns_priority_scores(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        cands = [make_candidate(f"q{i}", rating=1400.0 + 100 * i) for i in range(4)]
        scheduler.select_next_question(user, {}, cands, session, config, now=NOW)
        assert all(c.priority_score > 0 for c in cands)

    def test_returned_candidate_is_from_the_input(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        cands = [make_candidate(f"q{i}") for i in range(10)]
        for _ in range(25):
            got = scheduler.select_next_question(user, {}, cands, session, config, now=NOW)
            assert got in cands

    def test_prefers_due_reviews_when_bandit_says_review(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(scheduler.mode_bandit, "should_review", lambda **kw: True)
        due = make_candidate("due", is_new=False, due=NOW - timedelta(days=3), reps=2)
        fresh = make_candidate("fresh")
        got = scheduler.select_next_question(user, {}, [due, fresh], session, config, now=NOW)
        assert got is due

    def test_falls_back_to_new_when_no_due_reviews(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(scheduler.mode_bandit, "should_review", lambda **kw: True)
        not_due = make_candidate("later", is_new=False, due=NOW + timedelta(days=5), reps=2)
        fresh = make_candidate("fresh")
        got = scheduler.select_next_question(user, {}, [not_due, fresh], session, config, now=NOW)
        assert got is fresh

    def test_falls_back_to_all_candidates_when_nothing_new_or_due(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(scheduler.mode_bandit, "should_review", lambda **kw: False)
        not_due = make_candidate("later", is_new=False, due=NOW + timedelta(days=5), reps=2)
        got = scheduler.select_next_question(user, {}, [not_due], session, config, now=NOW)
        assert got is not_due

    def test_overdue_review_scores_urgency(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(scheduler.mode_bandit, "should_review", lambda **kw: True)
        monkeypatch.setattr(random, "random", lambda: 0.0)
        for arm_id in ("slightly", "very"):
            scheduler.question_bandit.add_arm(arm_id)
            monkeypatch.setattr(scheduler.question_bandit.arms[arm_id], "sample", lambda: 0.5)
        slightly = make_candidate("slightly", is_new=False, due=NOW - timedelta(days=1), reps=2)
        very = make_candidate("very", is_new=False, due=NOW - timedelta(days=14), reps=2)
        scheduler.select_next_question(user, {}, [slightly, very], session, config, now=NOW)
        assert very.priority_score > slightly.priority_score

    def test_weak_skill_scores_higher_than_mastered_skill(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(random, "random", lambda: 0.0)
        for arm_id in ("weak", "strong"):
            scheduler.question_bandit.add_arm(arm_id)
            monkeypatch.setattr(scheduler.question_bandit.arms[arm_id], "sample", lambda: 0.5)
        states = {
            "weak_skill": SkillState(skill_id="weak_skill", p_known=0.05),
            "strong_skill": SkillState(skill_id="strong_skill", p_known=0.98),
        }
        weak = make_candidate("weak", skill_ids=["weak_skill"])
        strong = make_candidate("strong", skill_ids=["strong_skill"])
        scheduler.select_next_question(user, states, [weak, strong], session, config, now=NOW)
        assert weak.priority_score > strong.priority_score

    def test_unknown_skill_contributes_no_need(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        c = make_candidate("q1", skill_ids=["never_seen"])
        got = scheduler.select_next_question(user, {}, [c], session, config, now=NOW)
        assert got is c

    def test_candidate_without_skills_does_not_divide_by_zero(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        c = make_candidate("q1", skill_ids=[])
        got = scheduler.select_next_question(user, {}, [c], session, config, now=NOW)
        assert got is c

    def test_selection_pool_is_capped_at_five(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # With r=0 the first element of the (sorted) top-5 pool always wins,
        # so the pick must be one of the five highest-priority candidates.
        monkeypatch.setattr(random, "random", lambda: 0.0)
        cands = [make_candidate(f"q{i}", rating=1000.0 + 50 * i) for i in range(20)]
        got = scheduler.select_next_question(user, {}, cands, session, config, now=NOW)
        assert got is not None
        ranked = sorted(cands, key=lambda c: c.priority_score, reverse=True)[:5]
        assert got in ranked

    def test_zero_total_weight_returns_first(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        c1, c2 = make_candidate("q1"), make_candidate("q2")
        scheduler.question_bandit.add_arm("q1")
        scheduler.question_bandit.add_arm("q2")
        for arm in scheduler.question_bandit.arms.values():
            monkeypatch.setattr(arm, "sample", lambda: 0.0)
        # Force every score component to 0 so the guard `total <= 0` fires.
        monkeypatch.setattr(scheduler, "_adjust_target", lambda cfg, s: 1.0)
        monkeypatch.setattr(scheduler.elo, "expected_score", lambda u, i: 0.0)
        got = scheduler.select_next_question(user, {}, [c1, c2], session, config, now=NOW)
        assert got in (c1, c2)

    def test_now_defaults_to_utcnow(
        self,
        scheduler: AdaptiveScheduler,
        user: EloEntity,
        session: SessionState,
        config: SessionConfig,
    ) -> None:
        c = make_candidate("q1")
        assert scheduler.select_next_question(user, {}, [c], session, config) is c


class TestProcessAnswer:
    def test_correct_answer_updates_session_counters(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert session.questions_answered == 1
        assert session.correct_count == 1
        assert session.combo == 1
        assert session.max_combo == 1
        assert session.recent_accuracy == [True]
        assert session.xp_earned > 0

    def test_wrong_answer_resets_combo_but_keeps_max(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        for _ in range(3):
            scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert session.combo == 3
        scheduler.process_answer(c, user, {}, False, 2_000, session, now=NOW)
        assert session.combo == 0
        assert session.max_combo == 3
        assert session.correct_count == 3

    def test_result_payload_shape(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1", skill_ids=["sk01"])
        states: dict[str, SkillState] = {}
        out = scheduler.process_answer(c, user, states, True, 1_500, session, now=NOW)
        assert out["correct"] is True
        assert out["grade"] == 4
        assert out["xp_earned"] == 15
        assert out["combo"] == 1
        assert isinstance(out["user_elo"], float)
        assert out["next_review"] is not None
        assert "sk01" in out["skill_mastery"]
        assert out["session_accuracy"] == pytest.approx(1.0)

    def test_creates_missing_skill_state(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1", skill_ids=["brand_new"])
        states: dict[str, SkillState] = {}
        scheduler.process_answer(c, user, states, True, 2_000, session, now=NOW)
        assert "brand_new" in states

    def test_correct_answer_raises_skill_mastery(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1", skill_ids=["sk01"])
        states = {"sk01": SkillState(skill_id="sk01", p_known=0.2)}
        before = states["sk01"].p_known
        scheduler.process_answer(c, user, states, True, 2_000, session, now=NOW)
        assert states["sk01"].p_known > before

    def test_wrong_answer_lowers_skill_mastery(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1", skill_ids=["sk01"])
        states = {"sk01": SkillState(skill_id="sk01", p_known=0.8)}
        before = states["sk01"].p_known
        scheduler.process_answer(c, user, states, False, 2_000, session, now=NOW)
        assert states["sk01"].p_known < before

    def test_multi_skill_question_updates_every_skill(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1", skill_ids=["a", "b", "c"])
        states: dict[str, SkillState] = {}
        out = scheduler.process_answer(c, user, states, True, 2_000, session, now=NOW)
        assert set(states) == {"a", "b", "c"}
        assert set(out["skill_mastery"]) == {"a", "b", "c"}

    def test_wrong_answer_lowers_question_elo(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        before = c.elo_entity.rating
        scheduler.process_answer(c, user, {}, False, 2_000, session, now=NOW)
        assert c.elo_entity.rating > before  # the item "won" -> its rating rises

    def test_correct_answer_lowers_question_elo(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        before = c.elo_entity.rating
        scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert c.elo_entity.rating < before

    def test_fsrs_card_is_advanced(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        assert c.fsrs_card.due is None
        scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert c.fsrs_card.due is not None
        assert c.fsrs_card.due > NOW

    def test_bandit_arm_is_updated_when_registered(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        arm = scheduler.question_bandit.add_arm("q1")
        alpha_before, beta_before = arm.alpha, arm.beta
        scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert (arm.alpha, arm.beta) != (alpha_before, beta_before)

    def test_unregistered_arm_is_skipped_without_error(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("never_registered")
        out = scheduler.process_answer(c, user, {}, True, 2_000, session, now=NOW)
        assert out["correct"] is True
        assert "never_registered" not in scheduler.question_bandit.arms

    def test_slow_correct_answer_grades_hard(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        out = scheduler.process_answer(c, user, {}, True, 30_000, session, now=NOW)
        assert out["grade"] == 2

    def test_now_defaults_to_utcnow(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        out = scheduler.process_answer(c, user, {}, True, 2_000, session)
        assert out["next_review"] is not None


class TestGetSessionSummary:
    def test_empty_session(self, scheduler: AdaptiveScheduler, session: SessionState) -> None:
        out = scheduler.get_session_summary(session)
        assert out == {
            "total_questions": 0,
            "correct": 0,
            "accuracy": 50.0,
            "max_combo": 0,
            "xp_earned": 0,
        }

    def test_summary_after_a_run(
        self, scheduler: AdaptiveScheduler, user: EloEntity, session: SessionState
    ) -> None:
        c = make_candidate("q1")
        for correct in (True, True, False, True):
            scheduler.process_answer(c, user, {}, correct, 2_000, session, now=NOW)
        out = scheduler.get_session_summary(session)
        assert out["total_questions"] == 4
        assert out["correct"] == 3
        assert out["accuracy"] == 75.0
        assert out["max_combo"] == 2
        assert out["xp_earned"] > 0

    def test_accuracy_is_rounded_to_one_decimal(
        self, scheduler: AdaptiveScheduler, session: SessionState
    ) -> None:
        session.recent_accuracy = [True, False, False]  # 33.33…%
        assert scheduler.get_session_summary(session)["accuracy"] == 33.3


class TestSchedulerWiring:
    def test_default_components_are_constructed(self) -> None:
        s = AdaptiveScheduler()
        assert s.fsrs is not None
        assert s.elo is not None
        assert s.bkt is not None
        assert s.question_bandit.arms == {}

    def test_injected_components_are_used(self) -> None:
        from app.services.engine.bkt import BKTModel
        from app.services.engine.elo import EloRating
        from app.services.engine.fsrs import FSRSScheduler

        fsrs, elo, bkt = FSRSScheduler(), EloRating(), BKTModel()
        s = AdaptiveScheduler(fsrs=fsrs, elo=elo, bkt=bkt)
        assert s.fsrs is fsrs
        assert s.elo is elo
        assert s.bkt is bkt


class TestEndToEndLoop:
    def test_full_session_stays_consistent(
        self, scheduler: AdaptiveScheduler, user: EloEntity, config: SessionConfig
    ) -> None:
        session = SessionState()
        states: dict[str, SkillState] = {}
        cands = [make_candidate(f"q{i}", skill_ids=[f"sk{i % 3}"]) for i in range(12)]

        for i in range(config.max_questions):
            picked = scheduler.select_next_question(user, states, cands, session, config, now=NOW)
            assert picked is not None
            scheduler.process_answer(picked, user, states, i % 3 != 0, 4_000, session, now=NOW)

        summary = scheduler.get_session_summary(session)
        assert summary["total_questions"] == config.max_questions
        assert 0 <= summary["correct"] <= config.max_questions
        assert 0.0 <= summary["accuracy"] <= 100.0
        assert summary["xp_earned"] > 0
        assert all(0.0 <= s.p_known <= 1.0 for s in states.values())
