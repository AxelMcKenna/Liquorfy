from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Optional

from redis import asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CacheClient:
    """Shared Redis client; callers decide whether cache failures are fatal."""

    def __init__(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        """Gets a value from the cache."""
        value = await self._redis.get(key)
        return value

    async def set(self, key: str, value: str, ttl: int) -> None:
        """Sets a value in the cache with a TTL."""
        # The 'ex' parameter sets the TTL in seconds.
        await self._redis.set(key, value, ex=ttl)

    async def ping(self) -> bool:
        """Pings the Redis server to check connectivity."""
        return await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()


_cache: CacheClient | None = None


def _get_cache() -> CacheClient:
    global _cache
    if _cache is None:
        _cache = CacheClient(str(get_settings().redis_url))
    return _cache


async def get_redis_client() -> CacheClient:
    """Returns the shared Redis cache client for health checks and other uses."""
    return _get_cache()


async def close_cache() -> None:
    global _cache
    if _cache is not None:
        await _cache.close()
        _cache = None


async def cached_json(key: str, ttl: Optional[int], producer: Callable[[], Awaitable[Any]]) -> Any:
    """
    A decorator-like function to cache the JSON result of an async function.
    """
    # A TTL of 0 or None means the cache is bypassed
    if ttl:
        try:
            cached = await _get_cache().get(f"liquorfy:cache:v1:{key}")
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Cache read failed for key %s", key, exc_info=True)

    result = await producer()

    # A TTL of 0 or None means we don't write to the cache
    if ttl:
        try:
            await _get_cache().set(
                f"liquorfy:cache:v1:{key}",
                json.dumps(result),
                ttl,
            )
        except Exception:
            logger.warning("Cache write failed for key %s", key, exc_info=True)

    return result


__all__ = ["cached_json", "close_cache", "get_redis_client"]
