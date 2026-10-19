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


class TestUpdateUnknown:
    """Explicit "I don't know" — a cleaner observation than a wrong answer.

    A wrong answer is confounded twice: a quarter of lucky guesses on a
    four-option question look like knowledge, and someone who does know can
    slip. Declaring ignorance carries neither confound, so it should move the
    posterior further down than a wrong answer does.
    """

    def test_drops_mastery_harder_than_a_wrong_answer(self, model: BKTModel) -> None:
        wrong = SkillState(skill_id="sk01", p_known=0.5)
        unknown = SkillState(skill_id="sk01", p_known=0.5)

        model.update(wrong, correct=False)
        model.update_unknown(unknown)

        assert unknown.p_known < wrong.p_known

    def test_guess_rate_does_not_affect_the_posterior(self) -> None:
        # Nobody guesses their way into saying "I don't know", so P(G) must
        # drop out entirely. Two models differing only in guess rate have to
        # agree — which is exactly what a wrong answer cannot do.
        low_guess = BKTModel(SkillParams(p_g=0.05))
        high_guess = BKTModel(SkillParams(p_g=0.90))

        a = SkillState(skill_id="sk01", p_known=0.5)
        b = SkillState(skill_id="sk01", p_known=0.5)
        low_guess.update_unknown(a)
        high_guess.update_unknown(b)
        assert a.p_known == pytest.approx(b.p_known)

        c = SkillState(skill_id="sk01", p_known=0.5)
        d = SkillState(skill_id="sk01", p_known=0.5)
        low_guess.update(c, correct=False)
        high_guess.update(d, correct=False)
        assert c.p_known != pytest.approx(d.p_known)

    def test_counts_the_attempt_but_never_as_correct(self, model: BKTModel) -> None:
        state = SkillState(skill_id="sk01", p_known=0.5, attempts=3, correct=2)
        model.update_unknown(state)
        assert state.attempts == 4
        assert state.correct == 2

    def test_learning_transition_still_applies(self) -> None:
        # The learner goes on to read the explanation, so the opportunity to
        # learn is real. With p_t at zero the posterior must be strictly lower
        # than with a learn rate.
        no_learning = BKTModel(SkillParams(p_t=0.0))
        learning = BKTModel(SkillParams(p_t=0.3))

        a = SkillState(skill_id="sk01", p_known=0.5)
        b = SkillState(skill_id="sk01", p_known=0.5)
        no_learning.update_unknown(a)
        learning.update_unknown(b)

        assert b.p_known > a.p_known

    def test_stays_within_bounds_at_the_extremes(self) -> None:
        for prior in (0.0, 1.0):
            state = SkillState(skill_id="sk01", p_known=prior)
            BKTModel().update_unknown(state)
            assert 0.0 <= state.p_known <= 1.0

    def test_degenerate_likelihoods_leave_mastery_untouched(self) -> None:
        # Both likelihoods at zero make the denominator vanish; the posterior
        # has to fall back to the prior rather than divide by zero.
        model = BKTModel(SkillParams(p_t=0.0, p_dk_known=0.0, p_dk_unknown=0.0))
        state = SkillState(skill_id="sk01", p_known=0.42)
        model.update_unknown(state)
        assert state.p_known == pytest.approx(0.42)

    def test_repeated_admissions_converge_toward_not_knowing(self, model: BKTModel) -> None:
        state = SkillState(skill_id="sk01", p_known=0.9)
        for _ in range(5):
            model.update_unknown(state)
        assert state.p_known < 0.35


class TestRecencyOverAccuracy:
    """BKT estima el estado de AHORA, no la precisión acumulada. Con los
    parámetros por defecto (p_t = 0,2) una racha de fallos solo baja p_known
    hasta ~0,23, y tres aciertos seguidos lo suben por encima de 0,95. Es el
    caso medido en local el 2026-10-18 («Fuerte — 10 respuestas · 4
    aciertos», p_known 0,971): no es un parámetro roto, es el modelo. Por eso
    la banda «Fuerte» (frontend/src/lib/evidenceBand.ts) exige además
    precisión; si esto deja de ser cierto, ese suelo se puede revisar."""

    @staticmethod
    def _run(model: BKTModel, answers: list[bool]) -> SkillState:
        state = model.init_state("sk01")
        for correct in answers:
            model.update(state, correct, p_guess=0.25)
        return state

    def test_four_of_ten_with_correct_answers_last_crosses_mastery(self, model: BKTModel) -> None:
        f, c = False, True
        state = self._run(model, [f, f, f, c, f, f, f, c, c, c])
        assert (state.attempts, state.correct) == (10, 4)
        assert state.p_known == pytest.approx(0.972, abs=1e-3)
        assert model.is_mastered(state)

    def test_six_failures_then_four_correct_crosses_mastery(self, model: BKTModel) -> None:
        state = self._run(model, [False] * 6 + [True] * 4)
        assert state.correct == 4
        assert state.p_known >= 0.95

    def test_failures_floor_at_the_learn_rate(self, model: BKTModel) -> None:
        # Tras un fallo el posterior cae cerca de 0, pero la transición suma
        # p_t: por mucho que falle, p_known no baja de ~0,2.
        state = self._run(model, [False] * 20)
        assert 0.2 < state.p_known < 0.25
