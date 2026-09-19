"""Rate limiting abstraction with in-memory and Redis backends.

Series 22.6: Use Redis if REDIS_URL is set, otherwise fall back to in-memory.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

logger = logging.getLogger("whetzy")


class RateLimiter(ABC):
    """Abstract rate limiter interface."""

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if a request is allowed. Return True if allowed, False if rate limited."""
        pass


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
        import redis
        self._redis = redis.from_url(redis_url, decode_responses=True)
        logger.info("Rate limiter: Using Redis backend (%s)", redis_url)

    async def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check rate limit using Redis."""
        import redis
        from redis import Redis

        redis_client: Redis = self._redis
        cache_key = f"rate_limit:{key}"

        try:
            # Increment counter
            count = redis_client.incr(cache_key)

            # Set expiration on first increment
            if count == 1:
                redis_client.expire(cache_key, window_seconds)

            return count <= limit
        except redis.RedisError as e:
            # If Redis is down, fall back to allowing the request (fail open)
            logger.warning("Redis rate limiter error: %s; allowing request", e)
            return True


def get_rate_limiter(redis_url: Optional[str] = None) -> RateLimiter:
    """Factory: return Redis limiter if available, else in-memory."""
    if redis_url:
        try:
            return RedisRateLimiter(redis_url)
        except Exception as e:
            logger.warning("Failed to initialize Redis limiter: %s; falling back to in-memory", e)
    return InMemoryRateLimiter()
