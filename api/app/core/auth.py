from __future__ import annotations

import datetime as dt
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


def create_admin_token() -> str:
    payload = {
        "sub": settings.admin_username,
        "exp": dt.datetime.utcnow() + dt.timedelta(hours=12),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if payload.get("sub") != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return payload["sub"]


__all__ = ["create_admin_token", "require_admin"]
