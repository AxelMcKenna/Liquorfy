from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Optional

from redis import asyncio as aioredis

from app.core.config import get_settings

_settings = get_settings()


class CacheClient:
    """A Redis-only cache client that fails loudly if Redis is unavailable."""

    def __init__(self) -> None:
        # This will raise an exception if the URL is invalid or Redis is not available,
        # which is desirable to catch configuration issues early.
        self._redis = aioredis.from_url(str(_settings.redis_url), decode_responses=True)

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


_cache = CacheClient()


async def get_redis_client() -> CacheClient:
    """Returns the shared Redis cache client for health checks and other uses."""
    return _cache


async def cached_json(key: str, ttl: Optional[int], producer: Callable[[], Awaitable[Any]]) -> Any:
    """
    A decorator-like function to cache the JSON result of an async function.
    """
    # A TTL of 0 or None means the cache is bypassed
    if ttl:
        try:
            cached = await _cache.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            # If cache fails, log it but proceed to call the producer.
            # In a real-world scenario, you'd add logging here.
            pass

    result = await producer()

    # A TTL of 0 or None means we don't write to the cache
    if ttl:
        try:
            # We assume 'result' is JSON-serializable.
            # The producer function is responsible for returning a valid structure.
            await _cache.set(key, json.dumps(result), ttl)
        except Exception:
            # If writing to cache fails, log it but don't fail the request.
            # In a real-world scenario, you'd add logging here.
            pass

    return result


__all__ = ["cached_json", "get_redis_client"]
