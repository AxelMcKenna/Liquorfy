from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import logging
import uuid
from typing import Optional

import bcrypt
import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
_auth_redis: redis.Redis | None = None


# Redis client for token blacklist
async def get_redis_client() -> redis.Redis:
    """Get Redis client for token revocation."""
    global _auth_redis
    if _auth_redis is None:
        _auth_redis = redis.from_url(
            str(get_settings().redis_url),
            decode_responses=True,
        )
    return _auth_redis


async def close_auth_redis() -> None:
    global _auth_redis
    if _auth_redis is not None:
        await _auth_redis.aclose()
        _auth_redis = None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_admin_token() -> str:
    """
    Create an admin JWT token.

    Note: This function should only be used after password verification.
    For login, use create_token_with_credentials() instead.

    Returns:
        JWT token string
    """
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": settings.admin_username,
        "iss": "liquorfy",
        "aud": "liquorfy-admin",
        "iat": now,
        "jti": str(uuid.uuid4()),
        "exp": now + dt.timedelta(seconds=settings.admin_token_ttl_seconds),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_token_with_credentials(username: str, password: str) -> str:
    """
    Verify credentials and create a JWT token if valid.

    Args:
        username: Username to verify
        password: Plain text password to verify

    Returns:
        JWT token string

    Raises:
        HTTPException: If credentials are invalid
    """
    settings = get_settings()
    username_matches = hmac.compare_digest(username, settings.admin_username)
    if settings.admin_password_hash:
        password_matches = verify_password(password, settings.admin_password_hash)
    else:
        password_matches = hmac.compare_digest(password, settings.admin_password)

    if not username_matches or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return create_admin_token()


async def revoke_token(token: str) -> None:
    """
    Revoke a JWT token by adding it to the Redis blacklist.

    Args:
        token: JWT token string to revoke

    The token is hashed before storing for efficiency and privacy.
    Expiry matches the token's exp claim so blacklist auto-cleans.
    """
    settings = get_settings()
    try:
        # Decode to get expiration
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience="liquorfy-admin",
            issuer="liquorfy",
            options={"verify_exp": False},
        )
        exp = payload.get("exp")

        if not exp:
            return  # Token has no expiration, can't revoke effectively

        # Calculate TTL (time until expiration)
        now = dt.datetime.now(dt.timezone.utc).timestamp()
        ttl = int(exp - now)

        if ttl <= 0:
            return  # Token already expired

        # Hash token for storage (shorter key, more privacy)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store in Redis with TTL matching token expiration
        redis_client = await get_redis_client()
        await redis_client.setex(f"revoked_token:{token_hash}", ttl, "1")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    except Exception as exc:
        logger.exception("Failed to revoke admin token")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token revocation is temporarily unavailable",
        ) from exc


async def is_token_revoked(token: str) -> bool:
    """
    Check if a token has been revoked.

    Args:
        token: JWT token string to check

    Returns:
        True if token is revoked, False otherwise
    """
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        redis_client = await get_redis_client()
        revoked = await redis_client.exists(f"revoked_token:{token_hash}")
        return bool(revoked)
    except Exception:
        # If revocation check fails, deny access (fail closed).
        logger.exception("Failed to check admin token revocation")
        return True


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Verify JWT token and require admin access.

    Args:
        credentials: HTTP Authorization credentials with Bearer token

    Returns:
        Admin username from token

    Raises:
        HTTPException: If token is missing, invalid, revoked, or not admin
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = credentials.credentials
    settings = get_settings()

    # Check if token is revoked
    if await is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience="liquorfy-admin",
            issuer="liquorfy",
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("sub") != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return payload["sub"]


__all__ = [
    "create_admin_token",
    "create_token_with_credentials",
    "close_auth_redis",
    "hash_password",
    "verify_password",
    "revoke_token",
    "is_token_revoked",
    "require_admin",
]
