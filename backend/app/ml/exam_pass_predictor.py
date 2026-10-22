"""Beta-binomial predictor for certification exam pass probability (14.8).

A learner's true per-question accuracy on exam-style questions is modelled as
an unknown probability theta with a Beta(alpha, beta) prior, updated from
observed practice-question outcomes (independent Bernoulli trials: correct or
not). The score on an `n_exam`-question real exam is then a draw from a
Beta-Binomial(n_exam, alpha, beta) distribution — not a Binomial(n_exam,
theta_hat) at a single point estimate of theta — which is what lets `p_pass`
fold in how UNCERTAIN the estimate of theta still is, not just where it is
centered. Two learners both estimated at theta_hat=0.85 but one from 10
practice answers and the other from 500 get different `p_pass`: the first
has a wide theta posterior, so the Beta-Binomial spreads probability across a
wider range of possible exam scores, some below the cutoff.

Calibration against REAL exam outcomes needs a real beta cohort (ledger H.10,
blocked: "sin datos reales no se puede calibrar"). Until then, this module is
validated by simulation with known ground truth (parameter recovery +
calibration curve + Brier score) — see
docs/ml/beta_binomial_calibration_14_8.md and
backend/scripts/beta_binomial_calibration.py. Nothing here reads from or
writes to the database; it is pure math over counts the caller supplies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import beta as beta_dist
from scipy.stats import betabinom

# Jeffreys prior, Beta(0.5, 0.5): the standard minimally-informative prior for
# a Bernoulli rate — unlike Beta(1,1) (uniform), it does not treat an
# untested learner as "uniformly likely to have any accuracy from 0% to
# 100%" (which overweights extreme values once you integrate), and unlike a
# prior centered on some assumed pass rate, it does not bias the very first
# predictions toward "will pass" before any evidence exists.
DEFAULT_PRIOR_ALPHA = 0.5
DEFAULT_PRIOR_BETA = 0.5


@dataclass(frozen=True)
class PassPrediction:
    """Everything `predict_pass_probability` computes, kept together so a
    caller never reports `p_pass` without also being able to show the
    interval it came from."""

    posterior_alpha: float
    posterior_beta: float
    theta_mean: float  # posterior mean accuracy estimate (point estimate)
    theta_ci_low: float  # credible interval for the *true* accuracy theta
    theta_ci_high: float
    p_pass: float  # P(score on an n_exam-question exam >= cutoff)
    n_exam_questions: int
    pass_cutoff_questions: int  # ceil(pass_pct/100 * n_exam_questions)
    n_practice: int  # correct + incorrect observations behind this estimate


def update_posterior(
    correct: int,
    incorrect: int,
    prior_alpha: float = DEFAULT_PRIOR_ALPHA,
    prior_beta: float = DEFAULT_PRIOR_BETA,
) -> tuple[float, float]:
    """Beta posterior (alpha, beta) after `correct`/`incorrect` i.i.d.
    Bernoulli observations — the standard Beta-Bernoulli conjugate update."""
    if correct < 0 or incorrect < 0:
        raise ValueError(f"correct/incorrect must be >= 0, got {correct}/{incorrect}")
    return prior_alpha + correct, prior_beta + incorrect


def predict_pass_probability(
    correct: int,
    incorrect: int,
    n_exam_questions: int,
    pass_pct: float,
    prior_alpha: float = DEFAULT_PRIOR_ALPHA,
    prior_beta: float = DEFAULT_PRIOR_BETA,
    credible_mass: float = 0.90,
) -> PassPrediction:
    """P(pass) for an `n_exam_questions`-question exam at a `pass_pct`%
    cutoff, given `correct`/`incorrect` observed practice answers so far.

    `pass_pct`/`n_exam_questions` are meant to come straight from the
    `Track` row (`passing_score_pct`, `exam_question_count`) so the
    prediction always matches the exam the learner will actually sit, not a
    generic "70% of 50" default.
    """
    if n_exam_questions <= 0:
        raise ValueError(f"n_exam_questions must be > 0, got {n_exam_questions}")
    if not (0 < pass_pct <= 100):
        raise ValueError(f"pass_pct must be in (0, 100], got {pass_pct}")

    alpha, beta_param = update_posterior(correct, incorrect, prior_alpha, prior_beta)

    cutoff = math.ceil(pass_pct / 100 * n_exam_questions)
    # P(X >= cutoff) = survival function evaluated at cutoff - 1 (scipy's
    # `sf` is P(X > x), so `sf(cutoff - 1)` is P(X >= cutoff)).
    p_pass = float(betabinom.sf(cutoff - 1, n_exam_questions, alpha, beta_param))

    theta_mean = alpha / (alpha + beta_param)
    lo_q, hi_q = (1 - credible_mass) / 2, 1 - (1 - credible_mass) / 2
    theta_ci_low = float(beta_dist.ppf(lo_q, alpha, beta_param))
    theta_ci_high = float(beta_dist.ppf(hi_q, alpha, beta_param))

    return PassPrediction(
        posterior_alpha=alpha,
        posterior_beta=beta_param,
        theta_mean=theta_mean,
        theta_ci_low=theta_ci_low,
        theta_ci_high=theta_ci_high,
        p_pass=p_pass,
        n_exam_questions=n_exam_questions,
        pass_cutoff_questions=cutoff,
        n_practice=correct + incorrect,
    )
