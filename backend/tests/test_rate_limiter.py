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


@pytest.mark.asyncio
async def test_redis_caido_limita_en_memoria_y_no_deja_pasar_todo():
    """Produccion 2026-09-27: REDIS_URL apuntaba a localhost sin Redis y cada
    peticion salia por «allowing request»: el login no tenia limite."""
    from app.core.rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter("redis://127.0.0.1:1/0")
    resultados = [await limiter.is_allowed("login:1.2.3.4", 3, 60) for _ in range(5)]
    assert resultados == [True, True, True, False, False]
    # Y por clave, como el limitador en memoria.
    assert await limiter.is_allowed("login:5.6.7.8", 3, 60) is True


@pytest.mark.asyncio
async def test_redis_event_loop_closed_tambien_limita_en_memoria():
    """Encontrado corriendo la suite entera (2026-09-28): una conexión de
    redis-py rota bajo pytest-asyncio no siempre sale como redis.RedisError --
    "Event loop is closed" es un RuntimeError liso, de asyncio, por debajo de
    la jerarquía de excepciones de redis-py. El except solo cazaba
    redis.RedisError, así que este caso se colaba sin caer al limitador en
    memoria (justo lo que el incidente de producción de más arriba dice que
    no debe pasar) -- se propagaba como un 500 en vez de degradar."""
    from unittest.mock import AsyncMock

    from app.core.rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter("redis://127.0.0.1:1/0")
    limiter._redis.incr = AsyncMock(side_effect=RuntimeError("Event loop is closed"))

    resultados = [await limiter.is_allowed("login:9.9.9.9", 3, 60) for _ in range(5)]
    assert resultados == [True, True, True, False, False]
