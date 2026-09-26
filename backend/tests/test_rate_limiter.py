"""Tests for rate limiting (Series 22.6) and rate-limit stats (22.1)."""

import pytest

from app.core.rate_limiter import InMemoryRateLimiter, RateLimitStats, get_rate_limiter


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_allows_within_limit():
    """Verify in-memory limiter allows requests within limit."""
    limiter = InMemoryRateLimiter()
    
    # Allow 5 requests per 60 seconds
    key = "test_ip"
    limit = 5
    
    for i in range(limit):
        allowed = await limiter.is_allowed(key, limit)
        assert allowed is True, f"Request {i+1} should be allowed"


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_blocks_over_limit():
    """Verify in-memory limiter blocks requests over limit."""
    limiter = InMemoryRateLimiter()
    
    key = "test_ip"
    limit = 3
    
    # Allow first 3
    for i in range(limit):
        allowed = await limiter.is_allowed(key, limit)
        assert allowed is True
    
    # 4th should be blocked
    allowed = await limiter.is_allowed(key, limit)
    assert allowed is False, "Request exceeding limit should be blocked"


@pytest.mark.asyncio
async def test_rate_limiter_per_key():
    """Verify rate limiter tracks separate keys independently."""
    limiter = InMemoryRateLimiter()
    
    key1 = "ip_1"
    key2 = "ip_2"
    limit = 2
    
    # Fill up key1
    await limiter.is_allowed(key1, limit)
    await limiter.is_allowed(key1, limit)
    
    # key2 should still be able to make requests
    allowed = await limiter.is_allowed(key2, limit)
    assert allowed is True


@pytest.mark.asyncio
async def test_get_rate_limiter_returns_in_memory_by_default():
    """Verify factory returns in-memory limiter by default."""
    limiter = get_rate_limiter(redis_url=None)
    assert isinstance(limiter, InMemoryRateLimiter)


def test_get_rate_limiter_factory():
    """Verify rate limiter factory can be called."""
    # Should not raise
    limiter = get_rate_limiter()
    assert limiter is not None


def test_rate_limit_stats_empty():
    stats = RateLimitStats()
    s = stats.summary()
    assert s["total_blocked"] == 0
    assert s["by_bucket"] == {}
    assert s["top_ips"] == []


def test_rate_limit_stats_records_hits():
    stats = RateLimitStats()
    stats.record_hit("1.2.3.4", "auth")
    stats.record_hit("1.2.3.4", "auth")
    stats.record_hit("5.6.7.8", "api")
    s = stats.summary()
    assert s["total_blocked"] == 3
    assert s["by_bucket"]["auth"] == 2
    assert s["by_bucket"]["api"] == 1
    assert len(s["top_ips"]) == 2
    assert s["top_ips"][0]["ip"] == "1.2.3.4"
    assert s["top_ips"][0]["hits"] == 2
