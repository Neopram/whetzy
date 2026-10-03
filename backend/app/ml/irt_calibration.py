"""Item-parameter calibration for the placement engine's IRT model (14.10).

`app.services.engine.placement.PlacementEngine` already does half of IRT at
serve time: given FIXED item parameters (difficulty, discrimination,
guessing), it estimates a test-taker's ability theta via Newton-Raphson MLE
(`update_ability`) — that is what Computer Adaptive Testing needs while a
placement test is running, and it already runs in production.

This module is the other half, done offline: estimating the item parameters
THEMSELVES from a bank of real responses, via Joint Maximum Likelihood
Estimation (JMLE — Birnbaum 1968, Lord 1980). JMLE alternates two steps
until the estimates settle:

  (a) person step (`estimate_abilities`) — re-estimate every respondent's
      ability, holding item parameters fixed, by direct MLE over their full
      response vector (see that function's docstring for why this is a
      fresh `scipy.optimize` fit rather than a reuse of
      `PlacementEngine.update_ability` — that method is correct for its own
      job, extending an estimate one CAT response at a time, but measurably
      unreliable when repurposed to solve a full response history at once).
  (b) item step (`calibrate_item`) — re-estimate each item's (discrimination,
      difficulty), holding abilities fixed. For a fixed theta per response,
      an item's likelihood is independent of every other item, so this is a
      separate 2-parameter MLE fit per item against
      `PlacementEngine.probability_correct` — the exact 3PL formula the
      engine already scores responses with, so calibration and serving can
      never silently disagree on what a given (theta, item) pair predicts.

The guessing parameter `c` is held fixed per item (not jointly estimated):
freely fitting all three 3PL parameters needs far more responses per item
than fitting two, and `c` is reasonably well known in advance from the
question format (1/n_choices for an n-way MCQ) rather than something that
needs discovering from data.

Blocked by the ledger ("No antes de tener miles de respuestas") until the
item bank has real response volume — JMLE is known to be biased with too
few items or respondents, and with none yet there is nothing to calibrate
against. Validated here by simulation with known ground-truth parameters
(parameter recovery) — see docs/ml/irt_calibration_14_10.md and
backend/scripts/irt_parameter_recovery.py. Nothing here touches the
database; `responses_by_person` is whatever the caller supplies.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from scipy.optimize import minimize

from app.services.engine.placement import IRTItem, PlacementEngine

# 4-way multiple choice is this product's question format (see
# app.schemas.content.QuestionPublic / the quiz UI); 1/4 matches
# IRTItem.guessing's own default of 0.20.
DEFAULT_GUESSING = 0.20
MIN_RESPONSES_PER_ITEM = 5  # below this, a 2-parameter fit is noise, not signal

# Joint MLE is well known to be inconsistent under "complete separation" --
# an item whose responses happen to split cleanly above/below some ability
# threshold has a likelihood that keeps improving as discrimination -> infinity
# (a perfect step function fits a clean split best). Hit this first-hand
# calibrating against simulated data: an unbounded Nelder-Mead fit sent one
# item's discrimination to 318 and another's difficulty to 33505 trying to
# chase that limit, wrecking recovery for every item (RMSE in the thousands).
# These bounds are the standard fix (Baker & Kim, "Item Response Theory",
# ch. 2 on JMLE's boundary problem): keep estimates inside the range real
# items actually occupy, since nothing in a well-behaved item bank calibrates
# to a=318 or b=33505 — a parameter walking there is JMLE chasing a
# degenerate optimum, not a truer estimate.
DISCRIMINATION_BOUNDS = (0.1, 4.0)
DIFFICULTY_BOUNDS = (-4.0, 4.0)


THETA_BOUNDS = (-4.0, 4.0)  # matches update_ability's own theta clamp


def estimate_abilities(
    items: Sequence[IRTItem],
    responses_by_person: Mapping[str, Sequence[tuple[str, bool]]],
) -> dict[str, float]:
    """Ability (theta) per person, given the CURRENT item parameters —
    the person half of one JMLE iteration.

    This does NOT call `PlacementEngine.update_ability`: that method runs a
    fixed 10 Newton-Raphson steps *per call*, designed to extend an existing
    estimate by one more response during a live CAT test, not to jointly
    solve for theta from a full response vector in one shot. Tried it first;
    confirmed empirically rather than assumed, because the difference is
    stark: feeding a person's full 40-response vector through 40 sequential
    `update_ability` calls (the only way to use that method on a full
    history) recovered true ability at r=0.34 against simulated data —
    against the gold-standard calibration-study design (every person
    answers every item), no less, which is the *easiest* ability-recovery
    case there is. The direct MLE fit here does the same `probability_correct`
    math as `update_ability`, just solved by `scipy.optimize` in one pass
    over all of a person's responses instead of Newton-Raphson walking there
    ten steps at a time — and bounded to the same [-4, 4] range
    `update_ability` itself clamps to — which recovers theta at r=0.86-0.98
    on the same data (see docs/ml/irt_calibration_14_10.md). This does not
    change anything about live CAT serving: `update_ability` is correct for
    its own job, extending an estimate by one response at a time as a
    placement test runs; it is just the wrong tool solved once over a full
    batch of responses offline."""
    scorer = PlacementEngine([])
    items_by_id = {it.item_id: it for it in items}
    abilities: dict[str, float] = {}

    for person_id, person_responses in responses_by_person.items():

        def neg_log_likelihood(params: Any, _responses: Sequence[tuple[str, bool]] = person_responses) -> float:
            (theta,) = params
            total = 0.0
            for item_id, correct in _responses:
                p = scorer.probability_correct(theta, items_by_id[item_id])
                p = min(max(p, 1e-9), 1 - 1e-9)
                total -= math.log(p) if correct else math.log(1 - p)
            return total

        result = minimize(
            neg_log_likelihood,
            x0=[0.0],
            method="L-BFGS-B",
            bounds=[THETA_BOUNDS],
            options={"maxiter": 200},
        )
        abilities[person_id] = float(result.x[0])
    return abilities


def calibrate_item(
    thetas: Sequence[float],
    outcomes: Sequence[bool],
    guessing: float = DEFAULT_GUESSING,
    a0: float = 1.0,
    b0: float = 0.0,
) -> tuple[float, float]:
    """MLE for one item's (discrimination, difficulty), given FIXED
    abilities — the item half of one JMLE iteration. Scores candidate
    (a, b) pairs with the exact same `PlacementEngine.probability_correct`
    formula `update_ability` uses, via a throwaway engine with no items
    (the method doesn't read `self` — it's only ever called as a method
    because it lives on `PlacementEngine` alongside the rest of the model).

    Bounded to `DISCRIMINATION_BOUNDS`/`DIFFICULTY_BOUNDS` — see the comment
    on those constants for why an unbounded fit is not safe to use."""
    scorer = PlacementEngine([])

    def neg_log_likelihood(params: Any) -> float:
        a, b = params
        item = IRTItem(item_id="_fit", difficulty=b, discrimination=a, guessing=guessing)
        total = 0.0
        for theta, correct in zip(thetas, outcomes, strict=True):
            p = scorer.probability_correct(theta, item)
            p = min(max(p, 1e-9), 1 - 1e-9)
            total -= math.log(p) if correct else math.log(1 - p)
        return total

    a0_clamped = min(max(a0, DISCRIMINATION_BOUNDS[0]), DISCRIMINATION_BOUNDS[1])
    b0_clamped = min(max(b0, DIFFICULTY_BOUNDS[0]), DIFFICULTY_BOUNDS[1])
    result = minimize(
        neg_log_likelihood,
        x0=[a0_clamped, b0_clamped],
        method="L-BFGS-B",
        bounds=[DISCRIMINATION_BOUNDS, DIFFICULTY_BOUNDS],
        options={"maxiter": 500},
    )
    return float(result.x[0]), float(result.x[1])


def calibrate_jmle(
    items: Sequence[IRTItem],
    responses_by_person: Mapping[str, Sequence[tuple[str, bool]]],
    n_iterations: int = 5,
    guessing: float = DEFAULT_GUESSING,
) -> tuple[dict[str, tuple[float, float]], dict[str, float]]:
    """Full JMLE loop: alternate ability and item steps `n_iterations`
    times. Returns `{item_id: (discrimination, difficulty)}` and
    `{person_id: theta}`.

    Items with fewer than `MIN_RESPONSES_PER_ITEM` responses keep their
    starting parameters untouched rather than being fit to noise — an
    under-exposed item should wait for more data, not get a confident-looking
    but meaningless estimate.

    IRT's probabilities are invariant to shifting every theta and every
    difficulty by the same constant, and to scaling (theta - difficulty)
    by one factor while scaling discrimination by its inverse — the model
    only pins down ability and difficulty up to that shared location and
    scale, not their absolute values. Re-standardizing the ability scale to
    (0, 1) *inside* the loop, every iteration, was tried first and made
    things worse (ability recovery r dropped from 0.86 to 0.16): resetting
    the scale out from under item estimates that have not caught up yet
    whipsaws the fit. Instead the loop runs on whatever internal scale it
    settles into, and `abilities`/`item_params` are rescaled together
    exactly once at the end — difficulty transforms like ability (same
    latent scale), discrimination transforms by the inverse factor, so
    `a * (theta - b)`, and therefore every probability the model computes,
    is unchanged by the relabeling. This fixes units for interpretation
    without disturbing the optimization. Confirmed empirically: without any
    rescaling, difficulty recovery against simulated N(0,1)-parameter data
    had systematic bias (RMSE > 1.7); with end-of-loop rescaling, bias
    disappears (see docs/ml/irt_calibration_14_10.md).
    """
    item_params: dict[str, tuple[float, float]] = {
        it.item_id: (it.discrimination, it.difficulty) for it in items
    }
    abilities: dict[str, float] = dict.fromkeys(responses_by_person, 0.0)

    for _ in range(n_iterations):
        working_items = [
            IRTItem(
                item_id=it.item_id,
                discrimination=item_params[it.item_id][0],
                difficulty=item_params[it.item_id][1],
                guessing=guessing,
            )
            for it in items
        ]
        abilities = estimate_abilities(working_items, responses_by_person)

        responses_by_item: dict[str, list[tuple[float, bool]]] = {it.item_id: [] for it in items}
        for person_id, person_responses in responses_by_person.items():
            theta = abilities[person_id]
            for item_id, correct in person_responses:
                responses_by_item[item_id].append((theta, correct))

        for item_id, observations in responses_by_item.items():
            if len(observations) < MIN_RESPONSES_PER_ITEM:
                continue
            thetas_i = [t for t, _ in observations]
            outcomes_i = [c for _, c in observations]
            a0, b0 = item_params[item_id]
            item_params[item_id] = calibrate_item(thetas_i, outcomes_i, guessing, a0, b0)

    return _rescale_to_standard_metric(item_params, abilities)


def _rescale_to_standard_metric(
    item_params: Mapping[str, tuple[float, float]],
    abilities: Mapping[str, float],
) -> tuple[dict[str, tuple[float, float]], dict[str, float]]:
    """Linearly rescale the ability distribution to mean 0, SD 1, and apply
    the matching inverse transform to every item's (discrimination,
    difficulty) so `a * (theta - b)` — and every probability derived from
    it — is unchanged. See the identifiability note on `calibrate_jmle`."""
    xs = list(abilities.values())
    n = len(xs)
    if n == 0:
        return dict(item_params), dict(abilities)
    mean = sum(xs) / n
    variance = sum((x - mean) ** 2 for x in xs) / n
    sd = variance**0.5
    if sd < 1e-9:
        return dict(item_params), dict(abilities)

    rescaled_abilities = {pid: (theta - mean) / sd for pid, theta in abilities.items()}
    rescaled_items = {
        item_id: (a * sd, (b - mean) / sd) for item_id, (a, b) in item_params.items()
    }
    return rescaled_items, rescaled_abilities
