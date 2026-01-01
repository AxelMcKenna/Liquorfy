"""Rate limiting middleware for FastAPI application."""
from __future__ import annotations

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings


def get_limiter() -> Limiter:
    """
    Create and configure rate limiter.

    Uses client IP address as the key for rate limiting.
    Default limits can be overridden per-route using the @limiter.limit() decorator.

    Storage:
    - Development: In-memory (simple, single-instance)
    - Production: Redis (distributed, multi-instance support)
    """
    settings = get_settings()

    # Use Redis in production for distributed rate limiting
    if settings.environment == "production":
        # Convert redis://host:port/db to redis://host:port format
        redis_url = str(settings.redis_url)
        storage_uri = redis_url
    else:
        # Development: use in-memory storage
        storage_uri = "memory://"

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["60/minute"],  # Default: 60 requests per minute per IP
        storage_uri=storage_uri,
    )
    return limiter


__all__ = ["get_limiter", "RateLimitExceeded", "_rate_limit_exceeded_handler"]
