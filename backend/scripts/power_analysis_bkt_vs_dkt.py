#!/usr/bin/env python3
"""power_analysis_bkt_vs_dkt.py — 32.2: how many users does the BKT-vs-DKT
A/B experiment need, to detect what effect?

Design-only: this computes sample sizes, it does not touch the experiment
framework (app.services.experiments) or flip any flag. The experiment stays
BLOCKED (H.10, cohort < 30) — see docs/ml/ab_bkt_vs_dkt_32_2.md for the
experiment design itself (arms, metrics, adoption rule) and why this script
exists instead of just quoting a textbook formula.

Method: Monte Carlo power simulation for both outcome metrics, not a
closed-form plugged in and trusted — the same "verify, don't assume" each
other script in this PR follows (the closed-form two-proportion formula is
computed too, as a cross-check that the simulation and the textbook formula
agree, not as the answer on its own).

Usage: python scripts/power_analysis_bkt_vs_dkt.py [--seed N]
"""

from __future__ import annotations

import argparse
import math
import random
from collections.abc import Callable
from functools import partial

import numpy as np
from sklearn.metrics import roc_auc_score

ALPHA = 0.05
TARGET_POWER = 0.80
N_TRIALS = 2000  # Monte Carlo repeats per (n, effect) cell -- D7 (cheap: plain Python loop)
AUC_N_TRIALS = 50  # separate, smaller budget: each trial runs a permutation test internally
AUC_N_PERMS = 40  # permutations per trial, to build the null distribution for one observed diff

# From the real BKT-vs-DKT benchmark (docs/ml/kt-benchmark.json, 11.3):
# BKT test AUC 0.7983, DKT test AUC 0.8294 -- the actual measured margin on
# this product's own skill-selection task, not a textbook round number.
BASELINE_AUC = 0.7983
MEASURED_AUC_MARGIN = 0.0311

# From 11.8's own criterion (docs/archive/LEDGER_HISTORY.md:1317): "D7 >= 20%
# medidos". The adoption rule (32.2) is "no empeora D7": the question this
# answers is how many users are needed to DETECT a drop of a given size from
# that 20% baseline, which is what "no empeora" has to be checked against.
BASELINE_D7 = 0.20


def _z(p: float) -> float:
    """Inverse standard normal CDF via a rational approximation (Acklam's
    algorithm) -- avoids a scipy.stats dependency for a two-line lookup."""
    import statistics

    return statistics.NormalDist().inv_cdf(p)


def two_proportion_n_closed_form(p1: float, p2: float, alpha: float = ALPHA, power: float = TARGET_POWER) -> int:
    """Standard closed-form sample size per arm for a two-proportion z-test
    (e.g. Fleiss, 'Statistical Methods for Rates and Proportions')."""
    z_alpha = _z(1 - alpha / 2)
    z_beta = _z(power)
    p_bar = (p1 + p2) / 2
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p1 - p2) ** 2
    return math.ceil(numerator / denominator)


def simulate_two_proportion_power(n_per_arm: int, p1: float, p2: float, rng: random.Random) -> float:
    """Empirical power: fraction of simulated trials where a two-proportion
    z-test on n_per_arm vs n_per_arm rejects H0 at alpha, when the TRUE
    rates are p1 and p2."""
    rejections = 0
    for _ in range(N_TRIALS):
        x1 = sum(1 for _ in range(n_per_arm) if rng.random() < p1)
        x2 = sum(1 for _ in range(n_per_arm) if rng.random() < p2)
        p1_hat, p2_hat = x1 / n_per_arm, x2 / n_per_arm
        p_pool = (x1 + x2) / (2 * n_per_arm)
        se = math.sqrt(p_pool * (1 - p_pool) * (2 / n_per_arm)) if p_pool not in (0.0, 1.0) else 0.0
        if se == 0.0:
            continue
        z_stat = (p1_hat - p2_hat) / se
        if abs(z_stat) > _z(1 - ALPHA / 2):
            rejections += 1
    return rejections / N_TRIALS


def simulate_auc_power(n_responses_per_arm: int, auc1: float, auc2: float, rng_seed: int) -> float:
    """Empirical power for detecting an AUC difference between two
    INDEPENDENT cohorts (an A/B test splits users, not the same users
    scored twice -- unlike DeLong's test, which is for paired/correlated
    AUCs on the same sample). Simulates scores for a balanced
    positive/negative set via a latent normal model calibrated so the
    resulting AUC matches the target (binormal ROC model: AUC = Phi(d/sqrt2)
    for unit-variance separated normals -- Hanley & McNeil 1982's own setup),
    computes each arm's AUC, and checks how often a basic permutation test
    on the AUC difference would call it significant."""
    rng = np.random.default_rng(rng_seed)
    n_pos = n_responses_per_arm // 2
    n_neg = n_responses_per_arm - n_pos

    def _d_for_auc(auc: float) -> float:
        # AUC = Phi(d / sqrt(2)) for a binormal model, equal variances.
        return _z(auc) * math.sqrt(2)

    rejections = 0
    for _ in range(AUC_N_TRIALS):
        d1, d2 = _d_for_auc(auc1), _d_for_auc(auc2)
        scores1 = np.concatenate([rng.normal(0, 1, n_neg), rng.normal(d1, 1, n_pos)])
        labels1 = np.concatenate([np.zeros(n_neg), np.ones(n_pos)])
        scores2 = np.concatenate([rng.normal(0, 1, n_neg), rng.normal(d2, 1, n_pos)])
        labels2 = np.concatenate([np.zeros(n_neg), np.ones(n_pos)])

        auc1_hat = roc_auc_score(labels1, scores1)
        auc2_hat = roc_auc_score(labels2, scores2)
        observed_diff = auc2_hat - auc1_hat

        # Permutation test: pool both arms' (score, label) pairs, re-split
        # at random, and see how often a random split produces a difference
        # at least as extreme as the observed one -- this is what "detected"
        # means here, not a Hanley-McNeil formula taken on faith.
        pooled_scores = np.concatenate([scores1, scores2])
        pooled_labels = np.concatenate([labels1, labels2])
        n_total = len(pooled_scores)
        n1 = len(scores1)
        extreme = 0
        for _p in range(AUC_N_PERMS):
            perm = rng.permutation(n_total)
            idx1, idx2 = perm[:n1], perm[n1:]
            try:
                perm_auc1 = roc_auc_score(pooled_labels[idx1], pooled_scores[idx1])
                perm_auc2 = roc_auc_score(pooled_labels[idx2], pooled_scores[idx2])
            except ValueError:
                continue  # a permutation with only one class in a split; skip it
            if abs(perm_auc2 - perm_auc1) >= abs(observed_diff):
                extreme += 1
        p_value = extreme / AUC_N_PERMS
        if p_value < ALPHA:
            rejections += 1
    return rejections / AUC_N_TRIALS


def find_n_for_power(
    simulate_fn: Callable[[int], float],
    candidate_ns: list[int],
) -> int | None:
    """Smallest n in candidate_ns (ascending) where simulated power >= TARGET_POWER."""
    for n in candidate_ns:
        power = simulate_fn(n)
        print(f"    n={n:>6}: empirical power = {power:.2f}")
        if power >= TARGET_POWER:
            return n
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="BKT-vs-DKT A/B power analysis (32.2)")
    parser.add_argument("--seed", type=int, default=20261002)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    print("=== D7 retention: how many users per arm to detect a drop from the 20% baseline? ===")
    print(f"(closed-form cross-check vs Monte Carlo simulation, alpha={ALPHA}, target power={TARGET_POWER})\n")
    for absolute_drop in (0.05, 0.08, 0.12):
        p2 = BASELINE_D7 - absolute_drop
        n_closed_form = two_proportion_n_closed_form(BASELINE_D7, p2)
        print(f"D7 {BASELINE_D7:.0%} -> {p2:.0%} (absolute drop {absolute_drop:.0%}): "
              f"closed-form n/arm = {n_closed_form}")
        candidates = sorted({max(10, int(n_closed_form * f)) for f in (0.5, 0.75, 1.0, 1.25)})
        n_simulated = find_n_for_power(partial(simulate_two_proportion_power, p1=BASELINE_D7, p2=p2, rng=rng), candidates)
        print(f"  Monte Carlo n/arm hitting {TARGET_POWER:.0%} power among candidates tried: "
              f"{n_simulated if n_simulated else f'> {max(candidates)} (none tried reached it)'}\n")

    print("=== AUC: how many RESPONSES per arm to detect the measured BKT->DKT margin? ===")
    print(f"(baseline BKT AUC={BASELINE_AUC}, measured margin={MEASURED_AUC_MARGIN} from docs/ml/kt-benchmark.json)\n")
    for margin in (MEASURED_AUC_MARGIN, 0.08):
        auc2 = BASELINE_AUC + margin
        print(f"AUC {BASELINE_AUC:.4f} -> {auc2:.4f} (margin {margin:.4f}):")
        candidates = [1000, 3000, 6000, 10000]
        n_simulated = find_n_for_power(
            partial(simulate_auc_power, auc1=BASELINE_AUC, auc2=auc2, rng_seed=args.seed), candidates
        )
        print(f"  n responses/arm hitting {TARGET_POWER:.0%} power among candidates tried: "
              f"{n_simulated if n_simulated else f'> {max(candidates)} (none tried reached it)'}\n")

    print("See docs/ml/ab_bkt_vs_dkt_32_2.md for what these numbers mean for how long the "
          "experiment would need to run, and why neither number alone answers 'is the cohort big enough'.")


if __name__ == "__main__":
    main()
