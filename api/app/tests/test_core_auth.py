"""Tests for core authentication module."""
from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from app.core.auth import (
    create_admin_token,
    create_token_with_credentials,
    hash_password,
    is_token_revoked,
    require_admin,
    revoke_token,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """hash_password should return a bcrypt hash string."""
        result = hash_password("test_password")
        assert isinstance(result, str)
        assert result.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_different_for_same_input(self):
        """hash_password should use random salt, producing different hashes."""
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password."""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_unicode(self):
        """verify_password should handle unicode passwords."""
        password = "p@ssw0rd_with_\u00e9_and_\u4e2d"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_empty(self):
        """verify_password should handle empty passwords."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_create_admin_token_returns_valid_jwt(self):
        """create_admin_token should return a valid JWT string."""
        token = create_admin_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_admin_token_contains_correct_claims(self):
        """create_admin_token should include correct claims."""
        from app.core.config import get_settings
        settings = get_settings()

        token = create_admin_token()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        assert payload["sub"] == settings.admin_username
        assert "exp" in payload

    def test_create_admin_token_expiration(self):
        """create_admin_token should set 12-hour expiration."""
        from app.core.config import get_settings
        settings = get_settings()

        now = dt.datetime.utcnow()
        token = create_admin_token()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        exp_time = dt.datetime.utcfromtimestamp(payload["exp"])
        expected_exp = now + dt.timedelta(hours=12)

        # Allow 2 minute tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 120

    def test_create_token_with_valid_credentials(self):
        """create_token_with_credentials should return token for valid creds."""
        from app.core.config import get_settings
        settings = get_settings()

        token = create_token_with_credentials(
            settings.admin_username,
            settings.admin_password
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_invalid_username(self):
        """create_token_with_credentials should reject invalid username."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            create_token_with_credentials("wrong_user", "testpassword123")

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    def test_create_token_with_invalid_password(self):
        """create_token_with_credentials should reject invalid password."""
        from fastapi import HTTPException
        from app.core.config import get_settings
        settings = get_settings()

        with pytest.raises(HTTPException) as exc_info:
            create_token_with_credentials(settings.admin_username, "wrong_password")

        assert exc_info.value.status_code == 401


class TestTokenRevocation:
    """Tests for token revocation."""

    @pytest.mark.asyncio
    async def test_revoke_token_stores_in_redis(self):
        """revoke_token should store token hash in Redis."""
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.close = AsyncMock()

        token = create_admin_token()

        with patch("app.core.auth.get_redis_client", AsyncMock(return_value=mock_redis)):
            await revoke_token(token)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0].startswith("revoked_token:")
        assert call_args[2] == "1"

    @pytest.mark.asyncio
    async def test_revoke_expired_token_does_nothing(self):
        """revoke_token should not store expired tokens."""
        from app.core.config import get_settings
        settings = get_settings()

        # Create an already-expired token
        payload = {
            "sub": settings.admin_username,
            "exp": dt.datetime.utcnow() - dt.timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock()
        mock_redis.close = AsyncMock()

        with patch("app.core.auth.get_redis_client", AsyncMock(return_value=mock_redis)):
            await revoke_token(expired_token)

        # Should not call setex for expired token
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_token_revoked_returns_false_for_valid_token(self):
        """is_token_revoked should return False for non-revoked token."""
        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.close = AsyncMock()

        token = create_admin_token()

        with patch("app.core.auth.get_redis_client", AsyncMock(return_value=mock_redis)):
            result = await is_token_revoked(token)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_revoked_returns_true_for_revoked_token(self):
        """is_token_revoked should return True for revoked token."""
        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.close = AsyncMock()

        token = create_admin_token()

        with patch("app.core.auth.get_redis_client", AsyncMock(return_value=mock_redis)):
            result = await is_token_revoked(token)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_revoked_fails_open(self):
        """is_token_revoked should return False if Redis fails."""
        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis down"))
        mock_redis.close = AsyncMock()

        token = create_admin_token()

        with patch("app.core.auth.get_redis_client", AsyncMock(return_value=mock_redis)):
            result = await is_token_revoked(token)

        assert result is False  # Fail open


class TestRequireAdmin:
    """Tests for require_admin dependency."""

    @pytest.mark.asyncio
    async def test_require_admin_with_valid_token(self, mock_redis):
        """require_admin should return username for valid admin token."""
        from fastapi.security import HTTPAuthorizationCredentials

        token = create_admin_token()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch("app.core.auth.is_token_revoked", AsyncMock(return_value=False)):
            result = await require_admin(credentials)

        from app.core.config import get_settings
        assert result == get_settings().admin_username

    @pytest.mark.asyncio
    async def test_require_admin_missing_token(self):
        """require_admin should raise 401 for missing token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(None)

        assert exc_info.value.status_code == 401
        assert "Missing token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_admin_revoked_token(self):
        """require_admin should raise 401 for revoked token."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        token = create_admin_token()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch("app.core.auth.is_token_revoked", AsyncMock(return_value=True)):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

        assert exc_info.value.status_code == 401
        assert "revoked" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_require_admin_invalid_token(self):
        """require_admin should raise 401 for invalid token."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")

        with patch("app.core.auth.is_token_revoked", AsyncMock(return_value=False)):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_admin_wrong_user(self):
        """require_admin should raise 403 for non-admin user."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        from app.core.config import get_settings

        settings = get_settings()

        # Create token for a different user
        payload = {
            "sub": "not_admin",
            "exp": dt.datetime.utcnow() + dt.timedelta(hours=12),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch("app.core.auth.is_token_revoked", AsyncMock(return_value=False)):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

        assert exc_info.value.status_code == 403
        assert "Forbidden" in str(exc_info.value.detail)
