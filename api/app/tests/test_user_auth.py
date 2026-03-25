"""Tests for Supabase user auth dependency."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.user_auth import get_current_user, get_optional_user


# Use the same secret as conftest sets for SECRET_KEY;
# we need a separate one for Supabase JWT secret.
_JWT_SECRET = "test-supabase-jwt-secret-at-least-32-chars"


def _make_token(
    sub: str | None = None,
    aud: str = "authenticated",
    expired: bool = False,
    secret: str = _JWT_SECRET,
) -> str:
    payload: dict = {}
    if sub is not None:
        payload["sub"] = sub
    if aud:
        payload["aud"] = aud
    if expired:
        payload["exp"] = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    else:
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    return jwt.encode(payload, secret, algorithm="HS256")


class _FakeCredentials:
    def __init__(self, token: str):
        self.credentials = token


@pytest.fixture(autouse=True)
def _set_supabase_secret(monkeypatch):
    """Patch the module-level settings object so JWT verification uses the test secret."""
    import app.core.user_auth as mod
    monkeypatch.setattr(mod.settings, "supabase_jwt_secret", _JWT_SECRET)


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    user_id = str(uuid.uuid4())
    token = _make_token(sub=user_id)
    result = await get_current_user(_FakeCredentials(token))
    assert result == uuid.UUID(user_id)


@pytest.mark.asyncio
async def test_get_current_user_missing_token():
    with pytest.raises(Exception) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    token = _make_token(sub=str(uuid.uuid4()), expired=True)
    with pytest.raises(Exception) as exc_info:
        await get_current_user(_FakeCredentials(token))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_wrong_secret():
    token = _make_token(sub=str(uuid.uuid4()), secret="wrong-secret-that-is-32-chars-long!!")
    with pytest.raises(Exception) as exc_info:
        await get_current_user(_FakeCredentials(token))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_sub():
    token = _make_token(sub=None)
    with pytest.raises(Exception) as exc_info:
        await get_current_user(_FakeCredentials(token))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_wrong_audience():
    token = _make_token(sub=str(uuid.uuid4()), aud="wrong")
    with pytest.raises(Exception) as exc_info:
        await get_current_user(_FakeCredentials(token))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_optional_user_valid():
    user_id = str(uuid.uuid4())
    token = _make_token(sub=user_id)
    result = await get_optional_user(_FakeCredentials(token))
    assert result == uuid.UUID(user_id)


@pytest.mark.asyncio
async def test_get_optional_user_none():
    result = await get_optional_user(None)
    assert result is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid():
    result = await get_optional_user(_FakeCredentials("bad-token"))
    assert result is None
