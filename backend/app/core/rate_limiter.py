"""Rate limiting abstraction with in-memory and Redis backends.

Series 22.6: Use Redis if REDIS_URL is set, otherwise fall back to in-memory.
22.1: Rate-limit hit stats for admin visibility.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

logger = logging.getLogger("whetzy")


@dataclass
class RateLimitStats:
    """In-process counters for rate-limit denials (22.1)."""

    _hits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))

    def record_hit(self, client_ip: str, bucket: str) -> None:
        self._hits[f"{client_ip}:{bucket}"] += 1

    def summary(self) -> dict[str, object]:
        by_bucket: dict[str, int] = defaultdict(int)
        by_ip: dict[str, int] = defaultdict(int)
        for key, count in self._hits.items():
            ip, bucket = key.rsplit(":", 1)
            by_bucket[bucket] += count
            by_ip[ip] += count
        top_ips = sorted(by_ip.items(), key=lambda x: x[1], reverse=True)[:20]
        return {
            "total_blocked": sum(self._hits.values()),
            "since": self._first_seen.isoformat(),
            "by_bucket": dict(by_bucket),
            "top_ips": [{"ip": ip, "hits": h} for ip, h in top_ips],
        }


_rate_limit_stats = RateLimitStats()


def get_rate_limit_stats() -> RateLimitStats:
    return _rate_limit_stats


class RateLimiter(ABC):
    """Abstract rate limiter interface."""

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if a request is allowed. Return True if allowed, False if rate limited."""


class InMemoryRateLimiter(RateLimiter):
    """Single-instance, in-memory fixed-window rate limiter (no persistence)."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is within rate limit."""
        now = time.monotonic()
        window_start = now - window_seconds
        bucket = self._hits[key]

        # Drop timestamps outside the window
        bucket[:] = [t for t in bucket if t >= window_start]

        if len(bucket) >= limit:
            return False

        bucket.append(now)
        return True


class RedisRateLimiter(RateLimiter):
    """Redis-backed fixed-window rate limiter (horizontal scale across instances)."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as aioredis

        # Cliente asincrono: el sincrono bloquea el event loop dentro de
        # `async def is_allowed`, que es justo lo contrario de lo que busca 22.6.
        self._redis = aioredis.from_url(  # type: ignore[no-untyped-call]  # redis-py sin tipos
            redis_url, decode_responses=True
        )
        # Si Redis no responde se limita en memoria, no se deja pasar todo:
        # en produccion REDIS_URL caia en localhost, que no existe, y el login
        # quedaba sin limite (logs del 2026-09-26/27, «allowing request»).
        self._fallback = InMemoryRateLimiter()
        self._fallback_warned = False
        logger.info("Rate limiter: Using Redis backend (%s)", redis_url)

    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check rate limit using Redis."""
        import redis

        redis_client = self._redis
        cache_key = f"rate_limit:{key}"

        try:
            # Increment counter
            count = await redis_client.incr(cache_key)

            # Set expiration on first increment
            if count == 1:
                await redis_client.expire(cache_key, window_seconds)

            return bool(count <= limit)
        except (redis.RedisError, RuntimeError, OSError) as e:
            # Not just redis.RedisError (2026-09-26/27 incident, see __init__):
            # a torn-down connection can also surface as a plain RuntimeError
            # ("Event loop is closed") or OSError from asyncio/the transport
            # itself, underneath redis-py's own exception hierarchy. Any of
            # them means the same thing here -- Redis is unusable right now --
            # and the whole point of this fallback is to degrade instead of
            # raise, so it has to catch whatever shape that unusability takes.
            if not self._fallback_warned:
                logger.warning("Redis rate limiter error: %s; limiting in memory", e)
                self._fallback_warned = True
            return await self._fallback.is_allowed(key, limit, window_seconds)


def get_rate_limiter(redis_url: str | None = None) -> RateLimiter:
    """Factory: return Redis limiter if available, else in-memory."""
    if redis_url:
        try:
            return RedisRateLimiter(redis_url)
        except Exception as e:  # noqa: BLE001 - cualquier fallo al abrir Redis cae al limitador en memoria
            logger.warning("Failed to initialize Redis limiter: %s; falling back to in-memory", e)
    return InMemoryRateLimiter()
