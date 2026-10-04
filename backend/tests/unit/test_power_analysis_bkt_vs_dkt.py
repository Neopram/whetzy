"""Tests for the D7 non-inferiority sample-size formula in
scripts/power_analysis_bkt_vs_dkt.py (32.2).

32.2's own adoption rule is "no empeora D7" — a NON-INFERIORITY question
(can we rule out that DKT is meaningfully worse?), not "can we detect any
difference at all?". Corrected per the [COORD] adversarial review
(2026-10-03 17:21, issue #89): the original script answered the wrong
question with a plain two-sided two-proportion test. This only tests the
closed-form formula (fast, deterministic) — the Monte Carlo cross-check in
the script itself takes ~45s end to end and is exercised by actually
running the script, not by this fast unit test file.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "power_analysis_bkt_vs_dkt.py"

assert SCRIPT.exists(), f"power_analysis_bkt_vs_dkt.py no esta en {SCRIPT}"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("power_analysis_bkt_vs_dkt", SCRIPT)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_noninferiority_n_matches_hand_derivation(mod) -> None:
    """margin=0.05, baseline=0.20: z(0.95)=1.6449, z(0.80)=0.8416,
    variance=2*0.2*0.8=0.32 -> ceil((1.6449+0.8416)^2 * 0.32 / 0.05^2) = 792.
    Matches the script's own printed output for this margin."""
    n = mod.two_proportion_n_noninferiority_closed_form(0.20, 0.05)
    assert n == 792


def test_noninferiority_needs_fewer_users_than_two_sided_detection_for_same_margin(mod) -> None:
    """The whole point of asking the right statistical question: a
    one-sided non-inferiority test against a margin needs FEWER users than
    a two-sided test trying to detect a genuine difference of that same
    size, because it only has to rule out one direction and it assumes true
    equivalence rather than a specific worse rate. `906` is the number
    already published in docs/ml/ab_bkt_vs_dkt_32_2.md for the two-sided
    5pp-drop case (`two_proportion_n_closed_form(0.20, 0.15)`), so this also
    pins that the published figure hasn't silently drifted."""
    n_noninferiority = mod.two_proportion_n_noninferiority_closed_form(0.20, 0.05)
    n_two_sided = mod.two_proportion_n_closed_form(0.20, 0.15)
    assert n_two_sided == 906
    assert n_noninferiority < n_two_sided


def test_smaller_margin_needs_more_users(mod) -> None:
    """A tighter "no empeora" margin (harder to satisfy) must need MORE
    users to have the power to show it, not fewer."""
    n_tight = mod.two_proportion_n_noninferiority_closed_form(0.20, 0.05)
    n_loose = mod.two_proportion_n_noninferiority_closed_form(0.20, 0.12)
    assert n_tight > n_loose
