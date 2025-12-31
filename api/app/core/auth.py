from __future__ import annotations

import datetime as dt
import hashlib
from typing import Optional

import bcrypt
import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


# Redis client for token blacklist
async def get_redis_client() -> redis.Redis:
    """Get Redis client for token revocation."""
    return redis.from_url(str(settings.redis_url), decode_responses=True)


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
    payload = {
        "sub": settings.admin_username,
        "exp": dt.datetime.utcnow() + dt.timedelta(hours=12),
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
    # For now, we're still using plaintext comparison for backwards compatibility
    # TODO: Once admin password is hashed in database, switch to verify_password()
    if username != settings.admin_username or password != settings.admin_password:
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
    try:
        # Decode to get expiration
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp = payload.get("exp")

        if not exp:
            return  # Token has no expiration, can't revoke effectively

        # Calculate TTL (time until expiration)
        now = dt.datetime.utcnow().timestamp()
        ttl = int(exp - now)

        if ttl <= 0:
            return  # Token already expired

        # Hash token for storage (shorter key, more privacy)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store in Redis with TTL matching token expiration
        redis_client = await get_redis_client()
        await redis_client.setex(f"revoked_token:{token_hash}", ttl, "1")
        await redis_client.close()
    except Exception:
        # If revocation fails, don't block the operation
        pass


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
        await redis_client.close()
        return bool(revoked)
    except Exception:
        # If check fails, assume token is not revoked (fail open)
        return False


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

    # Check if token is revoked
    if await is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("sub") != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return payload["sub"]


__all__ = [
    "create_admin_token",
    "create_token_with_credentials",
    "hash_password",
    "verify_password",
    "revoke_token",
    "is_token_revoked",
    "require_admin",
]
