"""Unit tests for the entitlements tier-gating module (7.3, 39.31)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.entitlements import user_meets_tier


def _user(tier: str | None, is_premium: bool = False, expires_at=None):
    """Minimal User stub — only the fields entitlements.py reads."""
    from unittest.mock import MagicMock
    u = MagicMock()
    u.subscription_tier = tier
    u.is_premium = is_premium
    u.subscription_expires_at = expires_at
    return u


# ── tier hierarchy ─────────────────────────────────────────────────────────────

def test_free_user_meets_free():
    assert user_meets_tier(_user(None), "free") is True


def test_free_user_does_not_meet_plus():
    assert user_meets_tier(_user(None), "plus") is False


def test_free_user_does_not_meet_pro():
    assert user_meets_tier(_user(None), "pro") is False


def test_plus_user_meets_free():
    assert user_meets_tier(_user("plus"), "free") is True


def test_plus_user_meets_plus():
    assert user_meets_tier(_user("plus"), "plus") is True


def test_plus_user_does_not_meet_pro():
    assert user_meets_tier(_user("plus"), "pro") is False


def test_pro_user_meets_all():
    u = _user("pro")
    assert user_meets_tier(u, "free") is True
    assert user_meets_tier(u, "plus") is True
    assert user_meets_tier(u, "pro") is True


# ── is_premium bypass (grandfathered accounts) ─────────────────────────────────

def test_is_premium_no_tier_treated_as_plus():
    """User with is_premium=True but no tier is treated as Plus."""
    u = _user(None, is_premium=True)
    assert user_meets_tier(u, "plus") is True


def test_is_premium_no_tier_does_not_meet_pro():
    u = _user(None, is_premium=True)
    assert user_meets_tier(u, "pro") is False


# ── lapsed subscription counts as free (39.31) ──────────────────────────────────

def test_no_expiry_set_keeps_tier():
    """subscription_expires_at=None means no expiry (grandfathered/admin accounts)."""
    u = _user("pro", expires_at=None)
    assert user_meets_tier(u, "pro") is True


def test_future_expiry_keeps_tier():
    u = _user("pro", expires_at=datetime.now(UTC) + timedelta(days=5))
    assert user_meets_tier(u, "pro") is True


def test_past_expiry_downgrades_to_free():
    u = _user("pro", expires_at=datetime.now(UTC) - timedelta(days=1))
    assert user_meets_tier(u, "pro") is False
    assert user_meets_tier(u, "plus") is False
    assert user_meets_tier(u, "free") is True


def test_past_expiry_downgrades_is_premium_bypass_too():
    u = _user(None, is_premium=True, expires_at=datetime.now(UTC) - timedelta(days=1))
    assert user_meets_tier(u, "plus") is False


def test_naive_past_expiry_still_downgrades():
    """SQLite/rows written without a zone return naive datetimes (see security._as_utc)."""
    u = _user("pro", expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1))
    assert user_meets_tier(u, "pro") is False
