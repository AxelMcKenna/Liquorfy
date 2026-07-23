"""Authentication routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.auth import create_token_with_credentials, revoke_token
from app.middleware.rate_limit import get_limiter

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)
limiter = get_limiter()


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
) -> TokenResponse:
    """
    Authenticate with username and password to receive a JWT token.

    Args:
        credentials: Login credentials (username and password)

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid (401)
    """
    token = create_token_with_credentials(credentials.username, credentials.password)
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict[str, str]:
    """
    Logout by revoking the current JWT token.

    This adds the token to a Redis-backed blacklist until it expires.
    Future requests with this token will be rejected.

    Args:
        credentials: HTTP Authorization credentials with Bearer token

    Returns:
        Success message

    Raises:
        HTTPException: If token is missing (401)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token"
        )

    # Revoke the token
    await revoke_token(credentials.credentials)

    return {"message": "Logged out successfully"}


__all__ = ["router"]
