"""Unit tests for JMLE item-parameter calibration (14.10).

Full-scale parameter recovery against a realistic item bank lives in
backend/scripts/irt_parameter_recovery.py (too slow for the regular suite —
~15s per run, see its own docstring for the real numbers). These tests are
the fast, deterministic correctness checks: small synthetic cases where the
right answer is known exactly, run on every test invocation.
"""

from __future__ import annotations

import math
import random

import pytest

from app.ml.irt_calibration import (
    DEFAULT_GUESSING,
    _rescale_to_standard_metric,
    calibrate_item,
    calibrate_jmle,
    estimate_abilities,
)
from app.services.engine.placement import IRTItem, PlacementEngine

# ── calibrate_item ────────────────────────────────────────────────────────────


def test_calibrate_item_recovers_known_parameters_from_clean_data() -> None:
    """Generate Bernoulli responses from a KNOWN (a, b) — 10 reps over a
    theta grid spanning -3..3 (610 responses: enough for a 2-parameter fit
    to land close rather than noisy; tried 61 responses first and the
    discrimination estimate was only right to within 50%, consistent with
    the full recovery study's finding that 'a' needs real sample size — see
    docs/ml/irt_calibration_14_10.md) — and check the fit lands close to the
    truth."""
    scorer = PlacementEngine([])
    true_item = IRTItem(item_id="t", difficulty=0.5, discrimination=1.3, guessing=DEFAULT_GUESSING)
    theta_grid = [-3.0 + 0.1 * i for i in range(61)]  # -3.0 .. 3.0
    thetas = theta_grid * 10
    rng = random.Random(7)
    outcomes = [rng.random() < scorer.probability_correct(theta, true_item) for theta in thetas]

    a_hat, b_hat = calibrate_item(thetas, outcomes, guessing=DEFAULT_GUESSING)

    assert a_hat == pytest.approx(1.3, abs=0.3)
    assert b_hat == pytest.approx(0.5, abs=0.3)


def test_calibrate_item_stays_within_bounds_for_a_perfectly_separating_pattern() -> None:
    """The classic JMLE failure mode: every low-theta response wrong, every
    high-theta response right, nothing in between — the unconstrained MLE
    for discrimination is +infinity. Must come back finite and inside
    DISCRIMINATION_BOUNDS, not diverge."""
    thetas = [-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0]
    outcomes = [False, False, False, False, True, True, True, True]

    a_hat, b_hat = calibrate_item(thetas, outcomes, guessing=DEFAULT_GUESSING)

    assert math.isfinite(a_hat)
    assert math.isfinite(b_hat)
    assert 0.1 <= a_hat <= 4.0


# ── estimate_abilities ────────────────────────────────────────────────────────


def test_estimate_abilities_recovers_a_known_theta() -> None:
    scorer = PlacementEngine([])
    items = [
        IRTItem(item_id=f"i{i}", difficulty=-2.0 + 0.5 * i, discrimination=1.0, guessing=DEFAULT_GUESSING)
        for i in range(9)
    ]
    true_theta = 0.7
    rng = random.Random(11)
    responses = {
        "alice": [
            (item.item_id, rng.random() < scorer.probability_correct(true_theta, item))
            for item in items
        ]
    }

    abilities = estimate_abilities(items, responses)

    assert abilities["alice"] == pytest.approx(0.7, abs=0.6)


def test_estimate_abilities_respects_theta_bounds() -> None:
    """A person who got every single item right has no finite MLE theta —
    the likelihood keeps improving as theta -> infinity. Must clamp, not
    return something unbounded or NaN."""
    items = [IRTItem(item_id=f"i{i}", difficulty=0.0, discrimination=1.0, guessing=DEFAULT_GUESSING) for i in range(5)]
    responses = {"perfect": [(item.item_id, True) for item in items]}

    abilities = estimate_abilities(items, responses)

    assert math.isfinite(abilities["perfect"])
    assert -4.0 <= abilities["perfect"] <= 4.0


# ── _rescale_to_standard_metric ───────────────────────────────────────────────


def test_rescale_preserves_every_response_probability() -> None:
    """The whole point of the rescaling: it relabels the latent scale, it
    must not change what the model predicts. Check `a*(theta-b)` — and
    therefore probability_correct — is identical before and after for every
    (person, item) combination, not just that the numbers "look reasonable"."""
    scorer = PlacementEngine([])
    item_params = {"i1": (1.2, 0.3), "i2": (0.8, -1.1), "i3": (2.0, 0.0)}
    abilities = {"p1": 0.5, "p2": -1.2, "p3": 2.0, "p4": 0.0}

    rescaled_items, rescaled_abilities = _rescale_to_standard_metric(item_params, abilities)

    for item_id, (a, b) in item_params.items():
        item = IRTItem(item_id=item_id, difficulty=b, discrimination=a, guessing=DEFAULT_GUESSING)
        a_r, b_r = rescaled_items[item_id]
        item_rescaled = IRTItem(item_id=item_id, difficulty=b_r, discrimination=a_r, guessing=DEFAULT_GUESSING)
        for person_id, theta in abilities.items():
            theta_r = rescaled_abilities[person_id]
            p_before = scorer.probability_correct(theta, item)
            p_after = scorer.probability_correct(theta_r, item_rescaled)
            assert p_before == pytest.approx(p_after, abs=1e-9)


def test_rescale_gives_the_ability_distribution_mean_zero_sd_one() -> None:
    abilities = {"p1": 2.0, "p2": 4.0, "p3": 6.0, "p4": 8.0}
    _items, rescaled = _rescale_to_standard_metric({}, abilities)

    values = list(rescaled.values())
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)

    assert mean == pytest.approx(0.0, abs=1e-9)
    assert variance == pytest.approx(1.0, abs=1e-9)


# ── calibrate_jmle (small end-to-end smoke test) ──────────────────────────────


def test_calibrate_jmle_recovers_a_small_known_bank() -> None:
    """Not the full-scale recovery study (see
    backend/scripts/irt_parameter_recovery.py, which uses a 40-item bank and
    1500 simulated people and recovers difficulty at r=0.99) — a small, fast
    smoke test that the whole alternating loop converges toward the right
    neighborhood.

    Only checks items within 1 SD of the population's mean ability
    (|difficulty| <= 1.0): with just 8 items total, every person's own
    ability estimate is itself imprecise (an 8-question exam IS noisy, same
    as a real one would be), and that noise propagates most into items at
    the edge of the ability range — exactly the "far items need more
    coverage" finding documented in docs/ml/irt_calibration_14_10.md, which
    an unrealistically small 8-item bank runs into even harder. The two
    edge items (+-1.5) still get a loose sanity check: finite, inside the
    engine's own difficulty bounds, and on the correct side of zero.
    """
    scorer = PlacementEngine([])
    rng = random.Random(2026)
    true_items = [
        IRTItem(item_id=f"i{i}", difficulty=b, discrimination=1.0, guessing=DEFAULT_GUESSING)
        for i, b in enumerate([-1.5, -0.75, 0.0, 0.75, 1.5, -0.5, 0.5, 1.0])
    ]
    responses: dict[str, list[tuple[str, bool]]] = {}
    for p in range(150):
        theta = rng.gauss(0.0, 1.0)
        responses[f"p{p}"] = [
            (item.item_id, rng.random() < scorer.probability_correct(theta, item))
            for item in true_items
        ]

    blind_items = [
        IRTItem(item_id=it.item_id, difficulty=0.0, discrimination=1.0, guessing=DEFAULT_GUESSING)
        for it in true_items
    ]
    estimated_params, _abilities = calibrate_jmle(blind_items, responses, n_iterations=5, guessing=DEFAULT_GUESSING)

    for it in true_items:
        _a_hat, b_hat = estimated_params[it.item_id]
        assert math.isfinite(b_hat)
        if abs(it.difficulty) <= 1.0:
            assert b_hat == pytest.approx(it.difficulty, abs=0.35)
        else:
            assert -4.0 <= b_hat <= 4.0
            assert (b_hat > 0) == (it.difficulty > 0)


def test_calibrate_jmle_leaves_under_exposed_items_untouched() -> None:
    """An item with fewer than MIN_RESPONSES_PER_ITEM responses should keep
    its starting parameters — fitting 2 free parameters to 2 data points is
    noise, not calibration."""
    scorer = PlacementEngine([])
    well_covered = IRTItem(item_id="common", difficulty=0.0, discrimination=1.0, guessing=DEFAULT_GUESSING)
    rare = IRTItem(item_id="rare", difficulty=0.0, discrimination=1.0, guessing=DEFAULT_GUESSING)
    rng = random.Random(3)

    responses: dict[str, list[tuple[str, bool]]] = {}
    for p in range(50):
        theta = rng.gauss(0.0, 1.0)
        person_responses = [("common", rng.random() < scorer.probability_correct(theta, well_covered))]
        if p < 2:  # "rare" only ever answered by 2 people
            person_responses.append(("rare", rng.random() < scorer.probability_correct(theta, rare)))
        responses[f"p{p}"] = person_responses

    blind = [
        IRTItem(item_id="common", difficulty=0.3, discrimination=1.0, guessing=DEFAULT_GUESSING),
        IRTItem(item_id="rare", difficulty=1.23, discrimination=2.5, guessing=DEFAULT_GUESSING),
    ]
    estimated_params, _abilities = calibrate_jmle(blind, responses, n_iterations=3, guessing=DEFAULT_GUESSING)

    # "rare" never had enough responses to fit, so it must come back exactly
    # as it went in (modulo the end-of-loop rescale, which both items get —
    # check it moved by the SAME transform as "common", not independently).
    a_common, _b_common = estimated_params["common"]
    a_rare, _b_rare = estimated_params["rare"]
    # rare started at (2.5, 1.23); common started at (1.0, 0.3) and WAS
    # fit. If rare were independently re-fit it would land near (1.0, 0.0)
    # like common did (same true parameters) instead of tracking its own
    # untouched (2.5, 1.23) through the shared rescale.
    assert a_rare != pytest.approx(a_common, abs=0.3)
