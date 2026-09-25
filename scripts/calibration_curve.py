#!/usr/bin/env python3
"""calibration_curve.py — 32.1: reliability curve for BKT p_known.

Generates synthetic learners, runs BKT updates, and measures calibration:
how well does p_known predict actual correctness?

The output is 5 buckets of p_known with the predicted vs observed accuracy
and the absolute calibration error per bucket.  Target: |error| < 0.10 per
bucket.

With real data (H.10): pass --db to read from the production/dev database
instead of synthetic generation.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.engine.bkt import BKTModel, SkillParams, SkillState

BINS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
BIN_LABELS = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]


def generate_synthetic(n_users: int = 200, n_questions: int = 30, seed: int = 42) -> list[tuple[float, bool]]:
    """Returns (p_known_before_answer, actually_correct) pairs.

    Simulates learners whose true mastery evolves following the same HMM
    that BKT models: initially unknown with P(L0), learning per opportunity
    with P(T), guessing with P(G), and slipping with P(S).  This is the
    ideal scenario — real learners won't match perfectly.
    """
    rng = random.Random(seed)
    params = SkillParams()
    bkt = BKTModel(params)
    observations: list[tuple[float, bool]] = []

    for _ in range(n_users):
        truly_known = rng.random() < params.p_l0
        state = SkillState(skill_id="synthetic", p_known=params.p_l0)

        for _ in range(n_questions):
            if truly_known:
                correct = rng.random() >= params.p_s
            else:
                correct = rng.random() < params.p_g

            observations.append((state.p_known, correct))
            state = bkt.update(state, correct)

            if not truly_known and rng.random() < params.p_t:
                truly_known = True

    return observations


def _predicted_accuracy(p_known: float, params: SkillParams) -> float:
    """BKT prediction: P(correct) = p_known*(1-slip) + (1-p_known)*guess."""
    return p_known * (1 - params.p_s) + (1 - p_known) * params.p_g


def compute_calibration(
    observations: list[tuple[float, bool]],
    params: SkillParams | None = None,
) -> list[dict]:
    if params is None:
        params = SkillParams()

    buckets: list[list[tuple[float, bool]]] = [[] for _ in BINS]

    for p_known, correct in observations:
        for i, (lo, hi) in enumerate(BINS):
            if lo <= p_known < hi:
                buckets[i].append((p_known, correct))
                break

    results = []
    for i, bucket in enumerate(buckets):
        if not bucket:
            results.append({
                "bin": BIN_LABELS[i],
                "n": 0,
                "mean_predicted": None,
                "observed_accuracy": None,
                "error": None,
            })
            continue

        mean_p = sum(_predicted_accuracy(p, params) for p, _ in bucket) / len(bucket)
        accuracy = sum(1 for _, c in bucket if c) / len(bucket)
        error = abs(mean_p - accuracy)
        results.append({
            "bin": BIN_LABELS[i],
            "n": len(bucket),
            "mean_predicted": round(mean_p, 4),
            "observed_accuracy": round(accuracy, 4),
            "error": round(error, 4),
        })

    return results


def print_table(results: list[dict]) -> bool:
    print(f"{'Bin':>10}  {'N':>6}  {'Predicted':>10}  {'Observed':>10}  {'|Error|':>8}  {'OK?':>4}")
    print("-" * 60)
    all_ok = True
    for r in results:
        if r["n"] == 0:
            print(f"{r['bin']:>10}  {'—':>6}  {'—':>10}  {'—':>10}  {'—':>8}  {'—':>4}")
            continue
        ok = r["error"] < 0.10
        if not ok:
            all_ok = False
        print(
            f"{r['bin']:>10}  {r['n']:>6}  {r['mean_predicted']:>10.4f}  "
            f"{r['observed_accuracy']:>10.4f}  {r['error']:>8.4f}  "
            f"{'OK' if ok else 'FAIL':>4}"
        )
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="BKT p_known calibration curve (32.1)")
    parser.add_argument("--users", type=int, default=200)
    parser.add_argument("--questions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", action="store_true", help="Use real DB data (requires DB connection)")
    args = parser.parse_args()

    if args.db:
        print("Real DB mode not yet implemented (needs H.10 — 30 beta users).")
        print("Falling back to synthetic data.\n")

    print(f"Generating synthetic data: {args.users} users x {args.questions} questions (seed={args.seed})")
    observations = generate_synthetic(args.users, args.questions, args.seed)
    print(f"Total observations: {len(observations)}\n")

    results = compute_calibration(observations)
    all_ok = print_table(results)

    print()
    if all_ok:
        print("RESULT: PASS — all buckets within 0.10 calibration error")
    else:
        print("RESULT: FAIL — one or more buckets exceed 0.10 calibration error")
        sys.exit(1)


if __name__ == "__main__":
    main()
