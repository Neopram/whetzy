"""Unit tests for Thompson Sampling Bandit."""

from __future__ import annotations

import pytest

from app.services.engine.bandit import Arm, NewVsReviewBandit, ThompsonBandit


class TestArm:
    def test_mean_uniform_prior(self) -> None:
        arm = Arm(arm_id="a", alpha=1.0, beta=1.0)
        assert arm.mean == pytest.approx(0.5)

    def test_mean_high_alpha(self) -> None:
        arm = Arm(arm_id="a", alpha=9.0, beta=1.0)
        assert arm.mean == pytest.approx(0.9)

    def test_update_reward_increases_alpha(self) -> None:
        arm = Arm(arm_id="a", alpha=1.0, beta=1.0)
        arm.update(1.0)
        assert arm.alpha == pytest.approx(2.0)
        assert arm.beta == pytest.approx(1.0)

    def test_update_no_reward_increases_beta(self) -> None:
        arm = Arm(arm_id="a", alpha=1.0, beta=1.0)
        arm.update(0.0)
        assert arm.alpha == pytest.approx(1.0)
        assert arm.beta == pytest.approx(2.0)

    def test_update_increments_pulls(self) -> None:
        arm = Arm(arm_id="a")
        arm.update(1.0)
        assert arm.total_pulls == 1

    def test_sample_returns_float_in_range(self) -> None:
        arm = Arm(arm_id="a", alpha=2.0, beta=2.0)
        samples = [arm.sample() for _ in range(100)]
        assert all(0.0 <= s <= 1.0 for s in samples)


class TestThompsonBandit:
    def test_add_and_select_single_arm(self) -> None:
        bandit = ThompsonBandit()
        bandit.add_arm("q1")
        result = bandit.select()
        assert result == "q1"

    def test_select_empty_returns_none(self) -> None:
        bandit = ThompsonBandit()
        assert bandit.select() is None

    def test_select_with_eligible_ids(self) -> None:
        bandit = ThompsonBandit()
        bandit.add_arm("q1")
        bandit.add_arm("q2")
        result = bandit.select(eligible_ids=["q1"])
        assert result == "q1"

    def test_select_eligible_ids_empty_list(self) -> None:
        bandit = ThompsonBandit()
        bandit.add_arm("q1")
        assert bandit.select(eligible_ids=[]) is None

    def test_select_top_n(self) -> None:
        bandit = ThompsonBandit()
        for i in range(5):
            bandit.add_arm(f"q{i}")
        result = bandit.select_top_n(3)
        assert len(result) == 3

    def test_select_top_n_more_than_arms(self) -> None:
        bandit = ThompsonBandit()
        bandit.add_arm("q1")
        result = bandit.select_top_n(10)
        assert len(result) == 1

    def test_select_top_n_empty(self) -> None:
        bandit = ThompsonBandit()
        assert bandit.select_top_n(3) == []

    def test_update_arm_adjusts_posterior(self) -> None:
        bandit = ThompsonBandit()
        bandit.add_arm("q1", prior_alpha=1.0, prior_beta=1.0)
        for _ in range(10):
            bandit.update("q1", 1.0)
        assert bandit.arms["q1"].mean > 0.8

    def test_update_nonexistent_arm_no_error(self) -> None:
        bandit = ThompsonBandit()
        bandit.update("missing", 1.0)  # should not raise

    def test_compute_reward_correct_normal_timing(self) -> None:
        bandit = ThompsonBandit()
        reward = bandit.compute_reward(
            correct=True,
            response_time_ms=10_000,
            expected_time_ms=15_000,
            difficulty_match=0.75,
        )
        assert 0.0 < reward <= 1.0

    def test_compute_reward_incorrect(self) -> None:
        bandit = ThompsonBandit()
        reward = bandit.compute_reward(
            correct=False,
            response_time_ms=5_000,
            expected_time_ms=10_000,
            difficulty_match=0.75,
        )
        assert reward < 0.5

    def test_compute_reward_correct_too_fast_penalized(self) -> None:
        bandit = ThompsonBandit()
        fast_reward = bandit.compute_reward(
            correct=True, response_time_ms=100, expected_time_ms=15_000, difficulty_match=0.75
        )
        normal_reward = bandit.compute_reward(
            correct=True, response_time_ms=10_000, expected_time_ms=15_000, difficulty_match=0.75
        )
        assert fast_reward < normal_reward

    def test_compute_reward_incorrect_good_engagement(self) -> None:
        bandit = ThompsonBandit()
        reward = bandit.compute_reward(
            correct=False,
            response_time_ms=20_000,
            expected_time_ms=10_000,
            difficulty_match=0.75,
        )
        assert reward > 0.0


class TestNewVsReviewBandit:
    def test_review_when_no_new_content(self) -> None:
        bandit = NewVsReviewBandit()
        assert bandit.should_review(has_due_reviews=True, has_new_content=False) is True

    def test_new_when_no_due_reviews(self) -> None:
        bandit = NewVsReviewBandit()
        assert bandit.should_review(has_due_reviews=False, has_new_content=True) is False

    def test_update_review_arm(self) -> None:
        bandit = NewVsReviewBandit()
        alpha_before = bandit.review_arm.alpha
        bandit.update(was_review=True, reward=1.0)
        assert bandit.review_arm.alpha > alpha_before

    def test_update_new_arm(self) -> None:
        bandit = NewVsReviewBandit()
        alpha_before = bandit.new_arm.alpha
        bandit.update(was_review=False, reward=1.0)
        assert bandit.new_arm.alpha > alpha_before

    def test_both_arms_returns_bool(self) -> None:
        bandit = NewVsReviewBandit()
        result = bandit.should_review(has_due_reviews=True, has_new_content=True)
        assert isinstance(result, bool)
