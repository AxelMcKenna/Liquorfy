from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Awaitable, Callable, Optional

try:  # pragma: no cover - optional dependency
    import aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

from app.core.config import get_settings

_settings = get_settings()


class AsyncTTLCache:
    """Fallback async cache using in-memory dictionary."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, str]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            value = self._data.get(key)
            if not value:
                return None
            expires_at, payload = value
            if expires_at < time.time():
                self._data.pop(key, None)
                return None
            return payload

    async def set(self, key: str, value: str, ttl: int) -> None:
        async with self._lock:
            self._data[key] = (time.time() + ttl, value)


class CacheClient:
    def __init__(self) -> None:
        self._redis = None
        if aioredis is not None:
            try:  # pragma: no cover
                self._redis = aioredis.from_url(str(_settings.redis_url))
            except Exception:
                self._redis = None
        self._fallback = AsyncTTLCache()

    async def get(self, key: str) -> Optional[str]:
        if self._redis is not None:
            try:
                value = await self._redis.get(key)
                if value:
                    return value.decode()
            except Exception:
                pass
        return await self._fallback.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        if self._redis is not None:
            try:
                await self._redis.set(key, value, ex=ttl)
                return
            except Exception:
                pass
        await self._fallback.set(key, value, ttl)


_cache = CacheClient()


async def cached_json(key: str, ttl: Optional[int], producer: Callable[[], Awaitable[Any]]) -> Any:
    if ttl:
        cached = await _cache.get(key)
        if cached:
            return json.loads(cached)
    result = await producer()
    if ttl:
        await _cache.set(key, json.dumps(result), ttl)
    return result


__all__ = ["cached_json"]
