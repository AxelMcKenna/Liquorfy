"""Supabase user authentication dependencies."""
from __future__ import annotations

import base64
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
_security = HTTPBearer(auto_error=False)
_jwt_secret = base64.b64decode(settings.supabase_jwt_secret) if settings.supabase_jwt_secret else b""

# Supabase JWKS endpoint for ES256 token verification
_jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json" if settings.supabase_url else None
_jwks_client = jwt.PyJWKClient(_jwks_url) if _jwks_url else None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> UUID:
    """Verify a Supabase-issued JWT and return the user_id."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )

    token = credentials.credentials
    try:
        # Peek at the algorithm to decide verification method
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "HS256":
            payload = jwt.decode(
                token,
                _jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        elif _jwks_client:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        else:
            raise jwt.PyJWTError("Unsupported algorithm and no JWKS configured")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return UUID(sub)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> UUID | None:
    """Return user_id if a valid token is present, otherwise None."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


__all__ = ["get_current_user", "get_optional_user"]
