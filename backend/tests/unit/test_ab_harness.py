"""Unit tests for A/B cohort assignment (task 4.6)."""

from __future__ import annotations

import uuid

import pytest

from app.services.ab_harness import get_cohort


def test_get_cohort_returns_valid_cohort() -> None:
    assert get_cohort(uuid.uuid4()) in ("bkt", "dkt")


def test_get_cohort_is_deterministic() -> None:
    uid = uuid.uuid4()
    assert get_cohort(uid) == get_cohort(uid)


def test_get_cohort_stable_known_id() -> None:
    uid = uuid.UUID("00000000-0000-0000-0000-000000000042")
    c1 = get_cohort(uid)
    c2 = get_cohort(uid)
    assert c1 == c2
    assert c1 in ("bkt", "dkt")


def test_get_cohort_ratio_zero_all_bkt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.DKT_AB_RATIO", 0.0)
    for _ in range(30):
        assert get_cohort(uuid.uuid4()) == "bkt"


def test_get_cohort_ratio_one_all_dkt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.DKT_AB_RATIO", 1.0)
    for _ in range(30):
        assert get_cohort(uuid.uuid4()) == "dkt"


def test_get_cohort_clamps_negative_ratio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.DKT_AB_RATIO", -1.0)
    for _ in range(20):
        assert get_cohort(uuid.uuid4()) == "bkt"


def test_get_cohort_clamps_ratio_above_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.DKT_AB_RATIO", 2.0)
    for _ in range(20):
        assert get_cohort(uuid.uuid4()) == "dkt"


def test_get_cohort_distribution_roughly_50_50() -> None:
    # Default ratio=0.5 → roughly half DKT over a large sample
    dkt_count = sum(1 for _ in range(2000) if get_cohort(uuid.uuid4()) == "dkt")
    assert 700 <= dkt_count <= 1300, f"Expected ~1000 DKT, got {dkt_count}"


def test_get_cohort_different_users_can_differ() -> None:
    cohorts = {get_cohort(uuid.uuid4()) for _ in range(50)}
    assert len(cohorts) == 2, "Expected both cohorts to appear in 50 random users"
