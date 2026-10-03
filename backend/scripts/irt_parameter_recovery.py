#!/usr/bin/env python3
"""irt_parameter_recovery.py — 14.10: validate JMLE item calibration against
SIMULATED responses with known ground-truth item parameters and abilities.

Real calibration needs real response volume (ledger: "No antes de tener
miles de respuestas"). This is what runs instead: generate a bank of items
with KNOWN (difficulty, discrimination), KNOWN person abilities, simulate
responses from the exact 3PL model the engine already uses
(`PlacementEngine.probability_correct`), run `calibrate_jmle` on nothing but
those simulated responses, and check how well it recovers the parameters it
was never told.

Usage: python scripts/irt_parameter_recovery.py [--seed N] [--n-persons N]
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.irt_calibration import DEFAULT_GUESSING, calibrate_jmle
from app.services.engine.placement import IRTItem, PlacementEngine

N_ITEMS = 40
N_JMLE_ITERATIONS = 5


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return float("nan")
    return cov / (var_x * var_y) ** 0.5


def _rmse(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    return (sum((x - y) ** 2 for x, y in zip(xs, ys, strict=True)) / n) ** 0.5


def simulate_bank(rng: random.Random, n_items: int) -> list[IRTItem]:
    items = []
    for i in range(n_items):
        # b ~ N(0,1): the standard IRT difficulty scale, centered on an
        # "average" test-taker. a ~ lognormal around 1 (exp(N(0, 0.3))):
        # discrimination is strictly positive and usually falls in 0.5-2.5
        # for real item banks; this keeps nearly all draws in that range
        # without a hard clip that would distort the true distribution.
        b_true = rng.gauss(0.0, 1.0)
        a_true = math.exp(rng.gauss(0.0, 0.3))
        items.append(
            IRTItem(item_id=f"item_{i}", difficulty=b_true, discrimination=a_true, guessing=DEFAULT_GUESSING)
        )
    return items


def simulate_responses(
    rng: random.Random, items: list[IRTItem], n_persons: int
) -> tuple[dict[str, list[tuple[str, bool]]], dict[str, float]]:
    """Dense design: every person answers every item (the standard design
    for an item-calibration study). `n_persons` x `len(items)` total
    responses."""
    scorer = PlacementEngine([])
    thetas_true: dict[str, float] = {}
    responses: dict[str, list[tuple[str, bool]]] = {}
    for p in range(n_persons):
        person_id = f"person_{p}"
        theta_true = rng.gauss(0.0, 1.0)
        thetas_true[person_id] = theta_true
        person_responses = []
        for item in items:
            p_correct = scorer.probability_correct(theta_true, item)
            correct = rng.random() < p_correct
            person_responses.append((item.item_id, correct))
        responses[person_id] = person_responses
    return responses, thetas_true


def main() -> None:
    parser = argparse.ArgumentParser(description="JMLE item-parameter recovery (14.10)")
    parser.add_argument("--seed", type=int, default=20261002)
    # 1500 persons x 40 items = 60000 responses: "miles de respuestas", the
    # ledger's own stated bar for when this is worth running at all.
    parser.add_argument("--n-persons", type=int, default=1500)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    true_items = simulate_bank(rng, N_ITEMS)
    responses, thetas_true = simulate_responses(rng, true_items, args.n_persons)
    print(f"Simulated {args.n_persons} persons x {N_ITEMS} items = "
          f"{args.n_persons * N_ITEMS} responses (seed={args.seed})")

    # Calibration starts "blind": every item at the engine's own neutral
    # defaults (a=1.0, b=0.0), not seeded anywhere near the true values —
    # recovery has to come from the responses alone.
    blind_items = [IRTItem(item_id=it.item_id, difficulty=0.0, discrimination=1.0, guessing=DEFAULT_GUESSING)
                   for it in true_items]

    estimated_params, estimated_abilities = calibrate_jmle(
        blind_items, responses, n_iterations=N_JMLE_ITERATIONS, guessing=DEFAULT_GUESSING
    )

    true_b = [it.difficulty for it in true_items]
    true_a = [it.discrimination for it in true_items]
    est_a = [estimated_params[it.item_id][0] for it in true_items]
    est_b = [estimated_params[it.item_id][1] for it in true_items]

    print(f"\n=== Item parameter recovery ({N_JMLE_ITERATIONS} JMLE iterations) ===")
    print(f"difficulty (b):      r={_pearson(true_b, est_b):.3f}  RMSE={_rmse(true_b, est_b):.3f}")
    print(f"discrimination (a):  r={_pearson(true_a, est_a):.3f}  RMSE={_rmse(true_a, est_a):.3f}")

    true_theta = [thetas_true[pid] for pid in responses]
    est_theta = [estimated_abilities[pid] for pid in responses]
    print("\n=== Ability recovery (byproduct of the same run) ===")
    print(f"theta:               r={_pearson(true_theta, est_theta):.3f}  RMSE={_rmse(true_theta, est_theta):.3f}")

    print(f"\n{'item':>10}  {'b_true':>8}  {'b_hat':>8}  {'a_true':>8}  {'a_hat':>8}")
    for it in true_items[:8]:
        a_hat, b_hat = estimated_params[it.item_id]
        print(f"{it.item_id:>10}  {it.difficulty:>8.3f}  {b_hat:>8.3f}  {it.discrimination:>8.3f}  {a_hat:>8.3f}")
    print("  ... (full table in docs/ml/irt_calibration_14_10.md)")

    # Known limitation, not a bug: an item's discrimination is only
    # identifiable where enough respondents sit near its difficulty. Items
    # whose true difficulty is far in the tail of the (simulated) ability
    # distribution get much worse discrimination estimates even with plenty
    # of total responses — reported separately so it doesn't get averaged
    # away, and so real-data calibration knows to flag these the same way.
    near = [it for it in true_items if abs(it.difficulty) <= 1.5]
    far = [it for it in true_items if abs(it.difficulty) > 1.5]
    if far:
        near_a_true = [it.discrimination for it in near]
        near_a_est = [estimated_params[it.item_id][0] for it in near]
        print("\n=== Discrimination recovery by how well-covered the item's difficulty is ===")
        print(f"|difficulty| <= 1.5 ({len(near)} items): "
              f"r={_pearson(near_a_true, near_a_est):.3f}  RMSE={_rmse(near_a_true, near_a_est):.3f}")
        print(f"|difficulty| >  1.5 ({len(far)} items): too few respondents near these items' "
              f"difficulty for a reliable discrimination estimate — flag, don't trust, until more data arrives")

    b_ok = _pearson(true_b, est_b) > 0.9 and _rmse(true_b, est_b) < 0.3
    a_ok = _pearson(true_a, est_a) > 0.8 and _rmse(true_a, est_a) < 0.5
    theta_ok = _pearson(true_theta, est_theta) > 0.85 and _rmse(true_theta, est_theta) < 0.6

    print()
    if b_ok and a_ok and theta_ok:
        print("RESULT: PASS — difficulty, discrimination and ability all recovered within tolerance")
    else:
        print("RESULT: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
