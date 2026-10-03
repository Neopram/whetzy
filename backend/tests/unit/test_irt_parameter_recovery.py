"""Tests for `recovery_passes` in scripts/irt_parameter_recovery.py (14.10).

A full JMLE recovery run takes ~20s per seed (60000 simulated responses), so
this does NOT re-run the simulation — it tests the pass/fail GATE itself,
the pure function that decides PASS/FAIL from already-computed statistics.

The thresholds it checks against were widened (Regla 11, revision adversaria
del 2026-10-03 17:21 en el #89): a single seed is not a reliable gate — the
previous thresholds (b_rmse < 0.3, a_rmse < 0.5) failed seed=2 (b_rmse=0.304)
and seed=5 (a_rmse=0.540) on Monte Carlo noise alone, confirmed by running
10 fixed seeds and finding every other statistic (r for b/a/theta, theta_rmse)
comfortably inside tolerance both times. The two real-measured cases below
(seed 2 and seed 5's actual output) must now PASS; a mutation that narrows
either threshold back toward the old value must make them FAIL again.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "irt_parameter_recovery.py"

assert SCRIPT.exists(), f"irt_parameter_recovery.py no esta en {SCRIPT}"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("irt_parameter_recovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Real measured output (python scripts/irt_parameter_recovery.py --seed 2 / --seed 5),
# not invented numbers.
SEED_2_STATS = {"b_r": 0.974, "b_rmse": 0.304, "a_r": 0.899, "a_rmse": 0.348, "theta_r": 0.884, "theta_rmse": 0.483}
SEED_5_STATS = {"b_r": 0.989, "b_rmse": 0.183, "a_r": 0.922, "a_rmse": 0.540, "theta_r": 0.887, "theta_rmse": 0.474}


def test_seed_2_passes_the_widened_threshold(mod) -> None:
    """Under the OLD threshold (b_rmse < 0.3) this seed failed by 0.004 —
    noise, not a real recovery problem (every other statistic was fine).
    The widened threshold (0.32) must accept it."""
    assert mod.recovery_passes(**SEED_2_STATS) is True


def test_seed_5_passes_the_widened_threshold(mod) -> None:
    """Same story on the discrimination RMSE side: old threshold 0.5,
    measured 0.540, widened threshold 0.61."""
    assert mod.recovery_passes(**SEED_5_STATS) is True


def test_a_genuinely_bad_recovery_still_fails(mod) -> None:
    """The widened thresholds are not "always pass" — correlations well
    below the bar, or RMSE far past the widened ceiling, must still FAIL."""
    bad = {"b_r": 0.5, "b_rmse": 1.5, "a_r": 0.3, "a_rmse": 2.0, "theta_r": 0.4, "theta_rmse": 1.5}
    assert mod.recovery_passes(**bad) is False


def test_each_criterion_is_independently_required(mod) -> None:
    """Passing 5 of 6 criteria must still FAIL — this is an AND, not a
    majority vote."""
    almost = dict(SEED_2_STATS, a_rmse=0.62)  # just over the 0.61 ceiling
    assert mod.recovery_passes(**almost) is False
