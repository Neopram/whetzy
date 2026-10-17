"""Unit tests for app.services.domain_mastery (C.2/B.11, 2026-10-04).

Pure functions over synthetic skill_id -> p_known maps, same style as
test_domain_report.py — no DB session needed.
"""

from __future__ import annotations

import pytest

from app.services.domain_mastery import (
    DOMAIN_READY_THRESHOLD,
    compute_domain_mastery,
    compute_weighted_overall_mastery,
    is_domain_ready,
    is_ready_for_simulacro,
)

# ── compute_domain_mastery ───────────────────────────────────────────────────


def test_mean_is_over_every_skill_of_the_domain() -> None:
    """42.6 (PLAN_ULTRACODE §4, dentro de 43.4): una skill sin estado cuenta 0.
    Antes la media iba solo sobre las evaluadas, así que practicar 1 de 10
    skills al 0,9 daba un dominio «listo» al 0,9."""
    mastery = compute_domain_mastery(
        "d1", weight_pct=30.0, skill_ids=["s1", "s2", "s3"],
        p_known_by_skill={"s1": 0.9, "s2": 0.6},  # s3 never attempted
    )
    assert mastery.p_known_mean == pytest.approx(0.5)  # (0.9 + 0.6 + 0) / 3
    assert mastery.skills_assessed == 2
    assert mastery.skills_total == 3
    assert mastery.has_data is True


def test_one_strong_skill_does_not_make_a_big_domain_ready() -> None:
    skills = [f"s{i}" for i in range(10)]
    mastery = compute_domain_mastery("d1", 20.0, skills, {"s0": 0.95})
    assert mastery.p_known_mean == pytest.approx(0.095)
    assert is_domain_ready(mastery) is False


def test_an_untouched_domain_reports_no_data_not_a_fabricated_number() -> None:
    """The actual bug: before this module, an untouched domain reported
    p_known_mean=0.1 (the BKT prior), not "sin datos"."""
    mastery = compute_domain_mastery(
        "d1", weight_pct=30.0, skill_ids=["s1", "s2"], p_known_by_skill={},
    )
    assert mastery.p_known_mean is None
    assert mastery.skills_assessed == 0
    assert mastery.skills_total == 2
    assert mastery.has_data is False


def test_a_domain_with_no_skills_at_all_also_reports_no_data() -> None:
    mastery = compute_domain_mastery("d1", weight_pct=10.0, skill_ids=[], p_known_by_skill={})
    assert mastery.p_known_mean is None
    assert mastery.skills_total == 0


def test_extra_entries_in_p_known_by_skill_outside_this_domain_are_ignored() -> None:
    """Only `skill_ids` (this domain's own skills) should count, even if the
    caller passes a p_known map covering the whole track."""
    mastery = compute_domain_mastery(
        "d1", weight_pct=30.0, skill_ids=["s1"],
        p_known_by_skill={"s1": 0.6, "other_domains_skill": 0.99},
    )
    assert mastery.p_known_mean == pytest.approx(0.6)
    assert mastery.skills_assessed == 1


# ── compute_weighted_overall_mastery ─────────────────────────────────────────


def test_overall_is_weighted_by_domain_weight() -> None:
    domains = [
        compute_domain_mastery("d1", 70.0, ["a"], {"a": 0.9}),
        compute_domain_mastery("d2", 30.0, ["b"], {"b": 0.3}),
    ]
    overall = compute_weighted_overall_mastery(domains)
    assert overall == pytest.approx((0.9 * 70 + 0.3 * 30) / 100)


def test_a_domain_with_no_data_is_excluded_from_both_numerator_and_denominator() -> None:
    """The real behavior change from the old BKT_PRIOR=0.1 approach: an
    untouched domain must not drag the overall score toward 0.1 just for
    existing - it is left out entirely, not treated as "measured and bad"."""
    domains = [
        compute_domain_mastery("d1", 50.0, ["a"], {"a": 0.9}),
        compute_domain_mastery("d2", 50.0, ["b", "c"], {}),  # untouched domain
    ]
    overall = compute_weighted_overall_mastery(domains)
    assert overall == pytest.approx(0.9), (
        "an untouched domain must not pull the overall average down at all"
    )


def test_overall_is_sin_datos_when_every_domain_is_untouched() -> None:
    domains = [
        compute_domain_mastery("d1", 50.0, ["a"], {}),
        compute_domain_mastery("d2", 50.0, ["b"], {}),
    ]
    assert compute_weighted_overall_mastery(domains) is None


def test_overall_of_an_empty_domain_list_is_sin_datos() -> None:
    assert compute_weighted_overall_mastery([]) is None


# ── is_domain_ready / is_ready_for_simulacro (B.11) ──────────────────────────


def test_a_domain_with_no_data_is_never_ready() -> None:
    untouched = compute_domain_mastery("d1", 50.0, ["a"], {})
    assert is_domain_ready(untouched) is False


def test_a_domain_right_at_the_threshold_is_ready() -> None:
    at_bar = compute_domain_mastery("d1", 50.0, ["a"], {"a": DOMAIN_READY_THRESHOLD})
    assert is_domain_ready(at_bar) is True
    just_under = compute_domain_mastery("d1", 50.0, ["a"], {"a": DOMAIN_READY_THRESHOLD - 0.01})
    assert is_domain_ready(just_under) is False


def test_ready_for_simulacro_requires_every_domain_ready() -> None:
    all_ready = [
        compute_domain_mastery("d1", 50.0, ["a"], {"a": 0.9}),
        compute_domain_mastery("d2", 50.0, ["b"], {"b": 0.8}),
    ]
    assert is_ready_for_simulacro(all_ready) is True

    one_weak = [
        compute_domain_mastery("d1", 50.0, ["a"], {"a": 0.9}),
        compute_domain_mastery("d2", 50.0, ["b"], {"b": 0.5}),  # below the bar
    ]
    assert is_ready_for_simulacro(one_weak) is False, (
        "one weak domain must hold back the whole track, even with a strong average"
    )


def test_ready_for_simulacro_is_false_when_any_domain_has_no_data() -> None:
    """The exact B.11 case: a domain the learner hasn't touched must not be
    waved through just because every OTHER domain looks great."""
    domains = [
        compute_domain_mastery("d1", 50.0, ["a"], {"a": 0.95}),
        compute_domain_mastery("d2", 50.0, ["b"], {}),  # untouched
    ]
    assert is_ready_for_simulacro(domains) is False


def test_ready_for_simulacro_is_false_for_a_track_with_no_domains() -> None:
    assert is_ready_for_simulacro([]) is False
