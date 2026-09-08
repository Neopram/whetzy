"""Unit tests for BKT (Bayesian Knowledge Tracing) engine."""

from __future__ import annotations

import pytest

from app.services.engine.bkt import BKTModel, SkillParams, SkillState


@pytest.fixture
def model() -> BKTModel:
    return BKTModel()


@pytest.fixture
def state() -> SkillState:
    return SkillState(skill_id="sk01", p_known=0.1)


class TestSkillState:
    def test_defaults(self, state: SkillState) -> None:
        assert state.p_known == 0.1
        assert state.attempts == 0
        assert state.correct == 0

    def test_skill_id(self) -> None:
        s = SkillState(skill_id="abc")
        assert s.skill_id == "abc"


class TestBKTModel:
    def test_init_state_uses_prior(self) -> None:
        model = BKTModel(SkillParams(p_l0=0.3))
        state = model.init_state("sk01")
        assert state.p_known == pytest.approx(0.3)

    def test_set_and_get_params(self, model: BKTModel) -> None:
        params = SkillParams(p_l0=0.5, p_t=0.3)
        model.set_params("sk01", params)
        assert model.get_params("sk01") is params

    def test_get_params_fallback(self, model: BKTModel) -> None:
        assert model.get_params("unknown") is model.default_params

    def test_correct_response_increases_p_known(self, model: BKTModel, state: SkillState) -> None:
        p_before = state.p_known
        model.update(state, correct=True)
        assert state.p_known > p_before

    def test_wrong_response_decreases_or_holds_p_known(self, model: BKTModel) -> None:
        state = SkillState(skill_id="sk01", p_known=0.8)
        p_before = state.p_known
        model.update(state, correct=False)
        assert state.p_known <= p_before

    def test_attempts_incremented_on_update(self, model: BKTModel, state: SkillState) -> None:
        model.update(state, correct=True)
        assert state.attempts == 1
        model.update(state, correct=False)
        assert state.attempts == 2

    def test_correct_count_only_increments_on_correct(self, model: BKTModel, state: SkillState) -> None:
        model.update(state, correct=True)
        assert state.correct == 1
        model.update(state, correct=False)
        assert state.correct == 1

    def test_p_known_clamped_to_one(self) -> None:
        model = BKTModel(SkillParams(p_l0=0.99, p_t=0.99, p_g=0.01, p_s=0.01))
        state = SkillState(skill_id="sk01", p_known=0.99)
        for _ in range(10):
            model.update(state, correct=True)
        assert state.p_known <= 1.0

    def test_p_known_clamped_to_zero(self) -> None:
        model = BKTModel(SkillParams(p_l0=0.01, p_t=0.0, p_g=0.01, p_s=0.99))
        state = SkillState(skill_id="sk01", p_known=0.01)
        for _ in range(10):
            model.update(state, correct=False)
        assert state.p_known >= 0.0

    def test_is_mastered_below_threshold(self, model: BKTModel, state: SkillState) -> None:
        assert not model.is_mastered(state)

    def test_is_mastered_above_threshold(self, model: BKTModel) -> None:
        state = SkillState(skill_id="sk01", p_known=0.96)
        assert model.is_mastered(state, threshold=0.95)

    def test_is_mastered_custom_threshold(self, model: BKTModel) -> None:
        state = SkillState(skill_id="sk01", p_known=0.5)
        assert model.is_mastered(state, threshold=0.4)
        assert not model.is_mastered(state, threshold=0.6)

    def test_predict_correct_formula(self) -> None:
        params = SkillParams(p_l0=0.5, p_t=0.2, p_g=0.25, p_s=0.1)
        model = BKTModel(params)
        state = SkillState(skill_id="sk01", p_known=0.5)
        expected = 0.5 * (1.0 - 0.1) + 0.5 * 0.25
        assert model.predict_correct(state) == pytest.approx(expected)

    def test_batch_mastery_empty(self, model: BKTModel) -> None:
        assert model.batch_mastery([]) == {}

    def test_batch_mastery_mixed(self, model: BKTModel) -> None:
        states = [
            SkillState(skill_id="a", p_known=0.99),
            SkillState(skill_id="b", p_known=0.1),
        ]
        result = model.batch_mastery(states, threshold=0.95)
        assert result == {"a": True, "b": False}

    def test_overall_mastery_empty(self, model: BKTModel) -> None:
        assert model.overall_mastery([]) == 0.0

    def test_overall_mastery_average(self, model: BKTModel) -> None:
        states = [
            SkillState(skill_id="a", p_known=0.8),
            SkillState(skill_id="b", p_known=0.4),
        ]
        assert model.overall_mastery(states) == pytest.approx(0.6)

    def test_zero_denominator_guard(self) -> None:
        """Extreme params that could produce denominator=0."""
        params = SkillParams(p_l0=0.0, p_t=0.0, p_g=0.0, p_s=1.0)
        model = BKTModel(params)
        state = SkillState(skill_id="sk01", p_known=0.0)
        # Should not raise; p_known should stay >= 0
        model.update(state, correct=True)
        assert 0.0 <= state.p_known <= 1.0
