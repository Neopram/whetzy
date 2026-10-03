#!/usr/bin/env python3
"""beta_binomial_calibration.py — 14.8: validate the beta-binomial exam-pass
predictor against SIMULATED learners with known ground truth.

Real calibration ("of those we told 90%, ~90% passed") needs a real beta
cohort — ledger H.10, blocked. This script is what runs instead, and what
keeps running alongside real data once it exists: it checks two separate
things a point-accuracy number can't show on its own —

  1. Parameter recovery: does the posterior's credible interval for theta
     actually contain the TRUE theta at (about) its nominal rate? A model
     can have a sane-looking `theta_mean` and still report overconfident
     (too narrow) or underconfident (too wide) intervals.
  2. Calibration + Brier score of `p_pass` itself: bucket predictions into
     deciles and compare the mean predicted probability to the empirical
     pass rate in that bucket — the actual "of those we told 90%, ~90%
     passed" check, just against a simulated exam instead of a real one.

Both need ground truth (the simulated theta_true) that real data never
gives you directly, which is exactly why this has to be validated in
simulation first and real-data calibration is a separate, later step once
H.10 lifts.

Usage: python scripts/beta_binomial_calibration.py [--seed N] [--n-users N]
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.exam_pass_predictor import predict_pass_probability

N_EXAM_QUESTIONS = 50
PASS_PCT = 70.0
PRACTICE_SIZES = (10, 30, 100, 300, 1000)
CREDIBLE_MASS = 0.90
N_CALIBRATION_BUCKETS = 10


def simulate_one(rng: random.Random, theta_true: float, n_practice: int):
    correct = sum(1 for _ in range(n_practice) if rng.random() < theta_true)
    incorrect = n_practice - correct
    pred = predict_pass_probability(
        correct, incorrect, n_exam_questions=N_EXAM_QUESTIONS, pass_pct=PASS_PCT,
        credible_mass=CREDIBLE_MASS,
    )
    exam_score = sum(1 for _ in range(N_EXAM_QUESTIONS) if rng.random() < theta_true)
    actually_passed = exam_score >= pred.pass_cutoff_questions
    covered = pred.theta_ci_low <= theta_true <= pred.theta_ci_high
    return pred, actually_passed, covered


def run_parameter_recovery(seed: int, n_users: int) -> bool:
    """For each practice-sample size, draw `n_users` learners with a THETA
    DRAWN AT RANDOM per user (not fixed), and check credible-interval
    coverage over that population. Coverage should sit near CREDIBLE_MASS
    regardless of n_practice — tight or wide, the interval should be honest
    about where theta actually is."""
    print(f"\n=== Parameter recovery (seed={seed}, n_users={n_users}, "
          f"nominal coverage={CREDIBLE_MASS:.0%}) ===")
    print(f"{'n_practice':>10}  {'coverage':>10}  {'mean CI width':>14}")
    all_ok = True
    for n_practice in PRACTICE_SIZES:
        rng = random.Random(seed * 1000 + n_practice)
        covered_count = 0
        widths = []
        for _ in range(n_users):
            theta_true = rng.uniform(0.3, 0.98)
            pred, _actually_passed, covered = simulate_one(rng, theta_true, n_practice)
            covered_count += covered
            widths.append(pred.theta_ci_high - pred.theta_ci_low)
        coverage = covered_count / n_users
        mean_width = sum(widths) / len(widths)
        # Binomial standard error on the coverage estimate itself, at n_users
        # samples — +/- 3 SE is the "this would be a real miss" band, not
        # just sampling noise around the nominal rate.
        se = (CREDIBLE_MASS * (1 - CREDIBLE_MASS) / n_users) ** 0.5
        ok = abs(coverage - CREDIBLE_MASS) < 3 * se
        all_ok &= ok
        flag = "OK" if ok else "FAIL"
        print(f"{n_practice:>10}  {coverage:>9.1%}  {mean_width:>14.3f}  {flag}")
    return all_ok


def run_calibration(seed: int, n_users: int) -> bool:
    """Pool predictions across a realistic mixture of practice amounts and
    abilities, bucket by predicted p_pass into deciles, and compare the
    mean prediction in each bucket to the empirical pass rate — the
    reliability-curve check 14.8 asks for, against simulated ground truth."""
    print(f"\n=== Calibration curve (seed={seed}, n_users={n_users}) ===")
    rng = random.Random(seed)
    rows = []
    for _ in range(n_users):
        theta_true = rng.uniform(0.3, 0.98)
        n_practice = rng.choice(PRACTICE_SIZES)
        pred, actually_passed, _covered = simulate_one(rng, theta_true, n_practice)
        rows.append((pred.p_pass, actually_passed))

    rows.sort(key=lambda r: r[0])
    bucket_size = len(rows) // N_CALIBRATION_BUCKETS
    print(f"{'bucket (p_pass range)':>26}  {'n':>6}  {'mean predicted':>14}  {'observed rate':>14}  {'|error|':>8}")
    brier_terms = [(p - (1.0 if passed else 0.0)) ** 2 for p, passed in rows]
    brier_baseline_rate = sum(1 for _, passed in rows if passed) / len(rows)
    brier_baseline_terms = [(brier_baseline_rate - (1.0 if passed else 0.0)) ** 2 for _, passed in rows]

    all_ok = True
    for i in range(N_CALIBRATION_BUCKETS):
        start = i * bucket_size
        end = (i + 1) * bucket_size if i < N_CALIBRATION_BUCKETS - 1 else len(rows)
        chunk = rows[start:end]
        if not chunk:
            continue
        mean_pred = sum(p for p, _ in chunk) / len(chunk)
        observed = sum(1 for _, passed in chunk if passed) / len(chunk)
        error = abs(mean_pred - observed)
        ok = error < 0.10
        all_ok &= ok
        label = f"[{chunk[0][0]:.2f}-{chunk[-1][0]:.2f}]"
        print(f"{label:>26}  {len(chunk):>6}  {mean_pred:>14.3f}  {observed:>14.3f}  {error:>8.3f}  {'OK' if ok else 'FAIL'}")

    brier = sum(brier_terms) / len(brier_terms)
    brier_baseline = sum(brier_baseline_terms) / len(brier_baseline_terms)
    print(f"\nBrier score (model):            {brier:.4f}")
    print(f"Brier score (base-rate-only):    {brier_baseline:.4f}  "
          f"(predicting the overall pass rate {brier_baseline_rate:.1%} for everyone)")
    skill = 1 - brier / brier_baseline if brier_baseline > 0 else float("nan")
    print(f"Brier skill score vs base rate:  {skill:.3f}  (>0 means the model beats guessing the base rate)")
    all_ok &= brier < brier_baseline
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Beta-binomial exam-pass predictor validation (14.8)")
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--n-users", type=int, default=5000)
    args = parser.parse_args()

    recovery_ok = run_parameter_recovery(args.seed, args.n_users)
    calibration_ok = run_calibration(args.seed, args.n_users)

    print()
    if recovery_ok and calibration_ok:
        print("RESULT: PASS — parameter recovery and calibration both within tolerance")
    else:
        print("RESULT: FAIL — see FAIL rows above")
        sys.exit(1)


if __name__ == "__main__":
    main()
