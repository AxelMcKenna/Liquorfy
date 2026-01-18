"""Tests for authentication API endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    def test_login_success(self, client: TestClient):
        """Login with valid credentials should return token."""
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_invalid_username(self, client: TestClient):
        """Login with invalid username should return 401."""
        response = client.post(
            "/auth/login",
            json={"username": "wronguser", "password": "testpassword123"}
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_invalid_password(self, client: TestClient):
        """Login with invalid password should return 401."""
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_missing_username(self, client: TestClient):
        """Login without username should return 422."""
        response = client.post(
            "/auth/login",
            json={"password": "testpassword123"}
        )
        assert response.status_code == 422

    def test_login_missing_password(self, client: TestClient):
        """Login without password should return 422."""
        response = client.post(
            "/auth/login",
            json={"username": "testadmin"}
        )
        assert response.status_code == 422

    def test_login_empty_body(self, client: TestClient):
        """Login with empty body should return 422."""
        response = client.post("/auth/login", json={})
        assert response.status_code == 422

    def test_login_returns_valid_jwt(self, client: TestClient):
        """Login should return a valid JWT that can be decoded."""
        import jwt
        from app.core.config import get_settings

        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "testpassword123"}
        )
        token = response.json()["access_token"]

        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        assert payload["sub"] == settings.admin_username
        assert "exp" in payload


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, auth_headers):
        """Logout with valid token should return success message."""
        with patch("app.core.auth.revoke_token", AsyncMock()):
            response = client.post("/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

    def test_logout_missing_token(self, client: TestClient):
        """Logout without token should return 401."""
        response = client.post("/auth/logout")
        assert response.status_code == 401
        assert "Missing token" in response.json()["detail"]

    def test_logout_calls_revoke_token(self, client: TestClient, auth_headers, auth_token):
        """Logout should call revoke_token with the provided token."""
        mock_revoke = AsyncMock()

        with patch("app.routes.auth.revoke_token", mock_revoke):
            client.post("/auth/logout", headers=auth_headers)

        mock_revoke.assert_called_once_with(auth_token)


class TestProtectedEndpoints:
    """Tests for protected endpoint authentication."""

    def test_ingest_requires_auth(self, client: TestClient):
        """Ingest endpoint should require authentication."""
        response = client.post("/ingest/run?chain=test")
        assert response.status_code == 401

    def test_ingest_with_valid_token(self, client: TestClient, auth_headers):
        """Ingest endpoint should accept valid token."""
        with patch("app.workers.tasks.enqueue_ingest", AsyncMock(return_value="job-123")):
            response = client.post("/ingest/run?chain=test", headers=auth_headers)

        # Should not be 401 (might be 400 for invalid chain, but not auth failure)
        assert response.status_code != 401

    def test_ingest_with_invalid_token(self, client: TestClient, invalid_auth_headers):
        """Ingest endpoint should reject invalid token."""
        response = client.post("/ingest/run?chain=test", headers=invalid_auth_headers)
        assert response.status_code == 401

    def test_token_in_different_case(self, client: TestClient, auth_token):
        """Authorization header should be case-insensitive."""
        headers = {"authorization": f"Bearer {auth_token}"}  # lowercase
        with patch("app.workers.tasks.enqueue_ingest", AsyncMock(return_value="job-123")):
            response = client.post("/ingest/run?chain=test", headers=headers)
        assert response.status_code != 401


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_expired_token_rejected(self, client: TestClient):
        """Expired token should be rejected."""
        import datetime as dt
        import jwt
        from app.core.config import get_settings

        settings = get_settings()
        payload = {
            "sub": settings.admin_username,
            "exp": dt.datetime.utcnow() - dt.timedelta(hours=1),  # Expired
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.post("/ingest/run?chain=test", headers=headers)

        assert response.status_code == 401
