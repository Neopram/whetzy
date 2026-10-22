"""Unit tests for the beta-binomial exam-pass predictor (14.8).

Pure math over caller-supplied counts — no DB, no app state. One test
(`test_p_pass_matches_monte_carlo_simulation`) cross-checks the analytic
Beta-Binomial formula against an independent Monte Carlo simulation with a
fixed seed, so a mistake in the formula (wrong cutoff, off-by-one in the
survival function, swapped alpha/beta) would show up as a real numeric
mismatch, not just a type error.
"""

from __future__ import annotations

import random

import pytest

from app.ml.exam_pass_predictor import (
    DEFAULT_PRIOR_ALPHA,
    DEFAULT_PRIOR_BETA,
    predict_pass_probability,
    update_posterior,
)

# ── update_posterior ─────────────────────────────────────────────────────────


def test_update_posterior_is_the_conjugate_beta_update() -> None:
    alpha, beta_param = update_posterior(correct=7, incorrect=3, prior_alpha=1.0, prior_beta=1.0)
    assert alpha == pytest.approx(8.0)
    assert beta_param == pytest.approx(4.0)


def test_update_posterior_with_no_observations_returns_the_prior() -> None:
    alpha, beta_param = update_posterior(0, 0, prior_alpha=2.5, prior_beta=3.5)
    assert (alpha, beta_param) == (2.5, 3.5)


def test_update_posterior_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        update_posterior(-1, 0)
    with pytest.raises(ValueError):
        update_posterior(0, -1)


# ── predict_pass_probability: input validation ──────────────────────────────


def test_rejects_non_positive_exam_length() -> None:
    with pytest.raises(ValueError):
        predict_pass_probability(10, 2, n_exam_questions=0, pass_pct=70)


def test_rejects_pass_pct_out_of_range() -> None:
    with pytest.raises(ValueError):
        predict_pass_probability(10, 2, n_exam_questions=50, pass_pct=0)
    with pytest.raises(ValueError):
        predict_pass_probability(10, 2, n_exam_questions=50, pass_pct=101)


# ── predict_pass_probability: behaviour ──────────────────────────────────────


def test_no_practice_data_centers_on_the_symmetric_jeffreys_prior() -> None:
    """With zero observations the posterior IS the Jeffreys prior
    (0.5, 0.5), which is symmetric — theta_mean must be exactly 0.5, not
    skewed toward "probably passes" or "probably fails"."""
    pred = predict_pass_probability(0, 0, n_exam_questions=50, pass_pct=70)
    assert pred.theta_mean == pytest.approx(0.5)
    assert pred.posterior_alpha == DEFAULT_PRIOR_ALPHA
    assert pred.posterior_beta == DEFAULT_PRIOR_BETA
    # Wide uncertainty with no evidence: the 90% interval should span most
    # of [0, 1], not collapse to a point.
    assert pred.theta_ci_high - pred.theta_ci_low > 0.8


def test_strong_practice_record_above_cutoff_gives_high_p_pass() -> None:
    pred = predict_pass_probability(180, 20, n_exam_questions=50, pass_pct=70)
    assert pred.theta_mean == pytest.approx(0.9, abs=0.01)
    assert pred.p_pass > 0.95


def test_strong_practice_record_below_cutoff_gives_low_p_pass() -> None:
    pred = predict_pass_probability(40, 160, n_exam_questions=50, pass_pct=70)
    assert pred.theta_mean == pytest.approx(0.2, abs=0.01)
    assert pred.p_pass < 0.05


def test_pass_cutoff_rounds_up_fractional_question_counts() -> None:
    # 70% of 50 = 35.0 exactly.
    pred = predict_pass_probability(10, 2, n_exam_questions=50, pass_pct=70)
    assert pred.pass_cutoff_questions == 35
    # 72.5% of 65 = 47.125 -> ceil to 48: 47/65 would be UNDER 72.5%, so
    # "pass" must require at least 48, not 47.
    pred2 = predict_pass_probability(10, 2, n_exam_questions=65, pass_pct=72.5)
    assert pred2.pass_cutoff_questions == 48


def test_credible_interval_is_well_ordered() -> None:
    pred = predict_pass_probability(37, 13, n_exam_questions=50, pass_pct=70)
    assert pred.theta_ci_low < pred.theta_mean < pred.theta_ci_high


def test_more_practice_at_the_same_ratio_narrows_the_interval() -> None:
    """70% accuracy from 10, 100, and 1000 answers: same point estimate,
    shrinking uncertainty — this is the entire reason to use a
    distribution over theta instead of reporting theta_hat alone."""
    small = predict_pass_probability(7, 3, n_exam_questions=50, pass_pct=70)
    medium = predict_pass_probability(70, 30, n_exam_questions=50, pass_pct=70)
    large = predict_pass_probability(700, 300, n_exam_questions=50, pass_pct=70)

    width_small = small.theta_ci_high - small.theta_ci_low
    width_medium = medium.theta_ci_high - medium.theta_ci_low
    width_large = large.theta_ci_high - large.theta_ci_low

    assert width_small > width_medium > width_large
    # All three should agree on roughly the same accuracy...
    for pred in (small, medium, large):
        assert pred.theta_mean == pytest.approx(0.7, abs=0.02)
    # ...but confidence of actually passing a 70%-cutoff exam should climb
    # as the uncertainty that drags down the survival-function tail shrinks.
    assert small.p_pass < medium.p_pass < large.p_pass


def test_p_pass_matches_monte_carlo_simulation() -> None:
    """Cross-check the closed-form Beta-Binomial survival function against
    an independent Monte Carlo simulation (fixed seed): draw theta from the
    posterior, then an exam score from Binomial(n_exam, theta), and compare
    the simulated pass rate to the analytic p_pass. This would catch an
    off-by-one in the cutoff or a swapped alpha/beta that unit tests on
    "is it high/low" alone would not."""
    pred = predict_pass_probability(37, 13, n_exam_questions=50, pass_pct=70)

    rng = random.Random(20261002)
    n_sims = 200_000
    passes = 0
    for _ in range(n_sims):
        theta = rng.betavariate(pred.posterior_alpha, pred.posterior_beta)
        score = sum(1 for _ in range(pred.n_exam_questions) if rng.random() < theta)
        if score >= pred.pass_cutoff_questions:
            passes += 1
    simulated_p_pass = passes / n_sims

    # Monte Carlo standard error at n=200k for p~0.6-0.8 is well under 0.2pp;
    # 1.5 percentage points of tolerance is generous headroom, not a loose bar.
    assert simulated_p_pass == pytest.approx(pred.p_pass, abs=0.015)
