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
other script in this PR follows (the closed-form formula is computed too,
as a cross-check that the simulation and the textbook formula agree, not as
the answer on its own).

D7's adoption rule is "no empeora D7" — a NON-INFERIORITY question, not "can
we detect a difference": this script tests that directly (one-sided,
margin-based), not a plain two-sided two-proportion test (corrected per
[COORD]'s adversarial review, 2026-10-03 17:21 on issue #89). AUC's own rule
("AUC >= 0.70 AND DKT > BKT") IS a superiority question, so that section
stays a two-sided detection test — and reports users/arm (not just
responses/arm) for a few plausible responses-per-user scenarios, since the
experiment framework (24.14) assigns and runs per user.

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
# medidos". The adoption rule (32.2) is "no empeora D7" -- a NON-INFERIORITY
# claim, not "detect any difference": corrected per the [COORD] adversarial
# review (2026-10-03 17:21, #89), which flagged that a plain two-sided
# detection test answers a different question ("can we tell D7 moved at
# all?") than the one the adoption rule actually asks ("can we rule out that
# DKT is meaningfully worse?"). See two_proportion_n_noninferiority_*() below.
BASELINE_D7 = 0.20

# "No empeora" margins to test non-inferiority against: the same three
# absolute-drop sizes the original two-sided table used, now read as "the
# largest drop we're still willing to call 'didn't get worse'", not as "the
# effect size we're trying to detect".
D7_NONINFERIORITY_MARGINS = (0.05, 0.08, 0.12)

# A/B tests run per-user (`get_user_variant`, 24.14), but AUC's natural unit
# here is per-RESPONSE (one scored prediction per answered question), so the
# script also reports users/arm for a few plausible "responses answered per
# user during the experiment window" scenarios -- the same translation
# docs/ml/ab_bkt_vs_dkt_32_2.md's table did by hand, now computed here so the
# two can't drift apart.
RESPONSES_PER_USER_SCENARIOS = (10, 30, 50, 100)


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


def two_proportion_n_noninferiority_closed_form(
    p_true: float, margin: float, alpha: float = ALPHA, power: float = TARGET_POWER
) -> int:
    """Sample size per arm for a ONE-SIDED non-inferiority test on two
    proportions: H0 is "DKT's true D7 is at least `margin` below BKT's"
    (DKT meaningfully worse); we want power to REJECT H0 when DKT is in
    fact truly equivalent (`p_true` for both arms -- the "if it really
    doesn't make things worse" scenario the adoption rule needs evidence
    for). One-sided alpha (`z_(1-alpha)`, not `z_(1-alpha/2)`) because
    non-inferiority only cares about the "got worse" direction -- DKT
    being BETTER isn't the hypothesis under test here, AUC already covers
    that comparison. This is why non-inferiority needs fewer samples than
    the two-sided detection test for the same margin: see
    tests/unit/test_power_analysis_bkt_vs_dkt.py."""
    z_alpha = _z(1 - alpha)  # one-sided, not alpha/2
    z_beta = _z(power)
    variance_term = 2 * p_true * (1 - p_true)  # both arms at the SAME true rate under H1
    return math.ceil(((z_alpha + z_beta) ** 2) * variance_term / margin**2)


def simulate_noninferiority_power(n_per_arm: int, p_true: float, margin: float, rng: random.Random) -> float:
    """Empirical power: fraction of simulated trials where a one-sided
    non-inferiority test correctly concludes "not meaningfully worse",
    when BOTH arms are simulated at the SAME true rate `p_true` (DKT is, in
    truth, exactly as good as BKT -- this measures our ability to show
    that, not to detect a difference that isn't there)."""
    z_alpha = _z(1 - ALPHA)  # one-sided, matching the closed-form above
    rejections = 0
    for _ in range(N_TRIALS):
        x1 = sum(1 for _ in range(n_per_arm) if rng.random() < p_true)
        x2 = sum(1 for _ in range(n_per_arm) if rng.random() < p_true)
        p1_hat, p2_hat = x1 / n_per_arm, x2 / n_per_arm
        se = math.sqrt(p1_hat * (1 - p1_hat) / n_per_arm + p2_hat * (1 - p2_hat) / n_per_arm)
        if se == 0.0:
            continue
        # Non-inferiority margin shifts the null boundary: conclude
        # "not worse by more than margin" when (p2_hat - p1_hat) clears
        # -margin by enough standard errors, one-sided.
        z_stat = (p2_hat - p1_hat + margin) / se
        if z_stat > z_alpha:
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

    print("=== D7 retention: NON-INFERIORITY -- how many users/arm to show DKT didn't make it worse? ===")
    print(f"(H0: DKT's true D7 is >= `margin` below BKT's; one-sided alpha={ALPHA}, "
          f"target power={TARGET_POWER}; assumes DKT is truly equivalent, same {BASELINE_D7:.0%} baseline)\n")
    for margin in D7_NONINFERIORITY_MARGINS:
        n_closed_form = two_proportion_n_noninferiority_closed_form(BASELINE_D7, margin)
        print(f"margin {margin:.0%} (\"no empeora\" = DKT's D7 no more than {margin:.0%} below {BASELINE_D7:.0%}): "
              f"closed-form n/arm = {n_closed_form}")
        candidates = sorted({max(10, int(n_closed_form * f)) for f in (0.5, 0.75, 1.0, 1.25)})
        n_simulated = find_n_for_power(
            partial(simulate_noninferiority_power, p_true=BASELINE_D7, margin=margin, rng=rng), candidates
        )
        print(f"  Monte Carlo n/arm hitting {TARGET_POWER:.0%} power among candidates tried: "
              f"{n_simulated if n_simulated else f'> {max(candidates)} (none tried reached it)'}\n")

    print("=== AUC: how many RESPONSES (and users) per arm to detect the measured BKT->DKT margin? ===")
    print("(AUC's own adoption rule, 'AUC >= 0.70 AND DKT > BKT', IS a superiority question, not "
          "non-inferiority -- this section stays a two-sided/one-sided detection test, unlike D7 above)")
    print(f"(baseline BKT AUC={BASELINE_AUC}, measured margin={MEASURED_AUC_MARGIN} from docs/ml/kt-benchmark.json)\n")
    for margin in (MEASURED_AUC_MARGIN, 0.08):
        auc2 = BASELINE_AUC + margin
        print(f"AUC {BASELINE_AUC:.4f} -> {auc2:.4f} (margin {margin:.4f}):")
        candidates = [1000, 3000, 6000, 10000]
        n_simulated = find_n_for_power(
            partial(simulate_auc_power, auc1=BASELINE_AUC, auc2=auc2, rng_seed=args.seed), candidates
        )
        if n_simulated:
            print(f"  n responses/arm hitting {TARGET_POWER:.0%} power among candidates tried: {n_simulated}")
            print(f"  {'responses/user':>15}  {'users/arm':>10}")
            for responses_per_user in RESPONSES_PER_USER_SCENARIOS:
                users_per_arm = math.ceil(n_simulated / responses_per_user)
                print(f"  {responses_per_user:>15}  {users_per_arm:>10}")
            print()
        else:
            print(f"  n responses/arm hitting {TARGET_POWER:.0%} power among candidates tried: "
                  f"> {max(candidates)} (none tried reached it)\n")

    print("See docs/ml/ab_bkt_vs_dkt_32_2.md for what these numbers mean for how long the "
          "experiment would need to run, and why neither number alone answers 'is the cohort big enough'.")


if __name__ == "__main__":
    main()
