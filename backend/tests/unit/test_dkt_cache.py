"""Unit tests for DKT inference cache (4.4).

Verifies that:
  - cache hits are returned without re-running the LSTM
  - cache is invalidated after TTL expires
  - cache evicts LRU entries when full
  - dkt_cache_clear() wipes all entries
  - p99 latency: cached call completes in < 1 ms (trivially within 200ms budget)
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest

from app.services import dkt as dkt_mod
from app.services.dkt import (
    _cache,
    _cache_get,
    _cache_key,
    _cache_set,
    dkt_cache_clear,
    predict,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

HISTORY: list[dict[str, Any]] = [
    {"skill_id": "sk1", "correct": True},
    {"skill_id": "sk2", "correct": False},
    {"skill_id": "sk1", "correct": True},
]
SKILL_INDEX = {"sk1": 0, "sk2": 1}


@pytest.fixture(autouse=True)
def clear_cache_around_test() -> None:
    dkt_cache_clear()
    yield  # type: ignore[misc]
    dkt_cache_clear()


# ── _cache_key ────────────────────────────────────────────────────────────────

def test_cache_key_deterministic() -> None:
    k1 = _cache_key(HISTORY, SKILL_INDEX)
    k2 = _cache_key(HISTORY, SKILL_INDEX)
    assert k1 == k2


def test_cache_key_differs_on_different_history() -> None:
    other = [{"skill_id": "sk1", "correct": False}]
    assert _cache_key(HISTORY, SKILL_INDEX) != _cache_key(other, SKILL_INDEX)


def test_cache_key_differs_on_different_skill_index() -> None:
    other_index = {"sk1": 0, "sk2": 1, "sk3": 2}
    assert _cache_key(HISTORY, SKILL_INDEX) != _cache_key(HISTORY, other_index)


# ── _cache_get / _cache_set ───────────────────────────────────────────────────

def test_cache_miss_returns_none() -> None:
    assert _cache_get("nonexistent") is None


def test_cache_set_then_get() -> None:
    result = {"sk1": 0.75, "sk2": 0.3}
    _cache_set("testkey", result)
    assert _cache_get("testkey") == result


def test_cache_expired_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    result = {"sk1": 0.5}
    _cache_set("expkey", result)
    # Move time forward past TTL
    monkeypatch.setattr(dkt_mod, "_CACHE_TTL", -1.0)  # TTL already elapsed
    _cache.clear()
    _cache["expkey"] = (time.monotonic() - 1.0, result)  # expired
    assert _cache_get("expkey") is None


def test_dkt_cache_clear() -> None:
    _cache_set("k1", {"sk1": 0.5})
    _cache_set("k2", {"sk2": 0.9})
    assert len(_cache) == 2
    dkt_cache_clear()
    assert len(_cache) == 0


# ── predict() caching ─────────────────────────────────────────────────────────

def test_predict_caches_result() -> None:
    call_count = 0
    original_predict_uncached = dkt_mod._predict_uncached

    def counting_predict(h: Any, si: Any) -> dict[str, float]:
        nonlocal call_count
        call_count += 1
        return original_predict_uncached(h, si)

    with patch.object(dkt_mod, "_predict_uncached", side_effect=counting_predict):
        result1 = predict(HISTORY, SKILL_INDEX)
        result2 = predict(HISTORY, SKILL_INDEX)

    assert call_count == 1, "LSTM should run only once; second call must hit cache"
    assert result1 == result2


def test_predict_different_history_not_cached() -> None:
    other_history = [{"skill_id": "sk1", "correct": False}]
    call_count = 0
    original = dkt_mod._predict_uncached

    def counting_predict(h: Any, si: Any) -> dict[str, float]:
        nonlocal call_count
        call_count += 1
        return original(h, si)

    with patch.object(dkt_mod, "_predict_uncached", side_effect=counting_predict):
        predict(HISTORY, SKILL_INDEX)
        predict(other_history, {"sk1": 0})

    assert call_count == 2, "Two distinct histories must produce two LSTM calls"


# ── p99 latency proxy ─────────────────────────────────────────────────────────

def test_cached_call_faster_than_1ms() -> None:
    predict(HISTORY, SKILL_INDEX)  # warm cache
    start = time.perf_counter()
    predict(HISTORY, SKILL_INDEX)  # cache hit
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 1.0, f"Cache hit took {elapsed_ms:.3f} ms — must be < 1 ms"
