"""Supabase user authentication dependencies."""
from __future__ import annotations

import asyncio
import functools
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

_security = HTTPBearer(auto_error=False)


@functools.lru_cache(maxsize=4)
def _get_jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


async def _require_active_supabase_user(
    *,
    token: str,
    user_id: UUID,
) -> None:
    """Confirm sensitive API tokens still belong to an active Auth user."""
    settings = get_settings()
    if not settings.supabase_url:
        return
    if not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User session verification is not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Authorization": f"Bearer {token}",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User session verification is temporarily unavailable",
        ) from exc

    if response.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive session",
        )
    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User session verification is temporarily unavailable",
        )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive session",
        )

    try:
        verified_user_id = UUID(response.json()["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session response",
        ) from exc
    if verified_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session does not match token subject",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> UUID:
    """Verify a Supabase-issued JWT and return the user_id."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )

    token = credentials.credentials
    settings = get_settings()
    auth_issuer = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1"
        if settings.supabase_url
        else None
    )
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise jwt.PyJWTError("Supabase shared JWT secret is not configured")
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret.encode(),
                algorithms=["HS256"],
                audience="authenticated",
                issuer=auth_issuer,
                options={"verify_iss": auth_issuer is not None},
            )
        elif alg in {"ES256", "RS256"} and auth_issuer:
            jwks_client = _get_jwks_client(
                f"{auth_issuer}/.well-known/jwks.json"
            )
            signing_key = await asyncio.to_thread(
                jwks_client.get_signing_key_from_jwt,
                token,
            )
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated",
                issuer=auth_issuer,
            )
        else:
            raise jwt.PyJWTError("Unsupported Supabase JWT algorithm")
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = UUID(sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        ) from exc
    await _require_active_supabase_user(token=token, user_id=user_id)
    return user_id


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
