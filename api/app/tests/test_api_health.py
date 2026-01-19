"""Tests for health check API endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthzEndpoint:
    """Tests for GET /healthz endpoint (liveness probe)."""

    def test_healthz_returns_ok(self, client: TestClient):
        """Healthz endpoint should return status ok."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_healthz_response_structure(self, client: TestClient):
        """Healthz response should have correct structure."""
        response = client.get("/healthz")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestHealthEndpoint:
    """Tests for GET /health endpoint (comprehensive health check)."""

    def test_health_healthy_returns_200(self, client: TestClient, mock_redis):
        """Health endpoint should return 200 when all checks pass."""
        # Mock successful DB check
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_response_structure(self, client: TestClient, mock_redis):
        """Health response should have correct structure."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/health")

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]

    def test_health_db_failure_returns_503(self, client: TestClient, mock_redis):
        """Health endpoint should return 503 when DB check fails."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_tx.return_value.__aenter__.side_effect = Exception("DB connection failed")

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "unhealthy"

    def test_health_redis_failure_returns_503(self, client: TestClient):
        """Health endpoint should return 503 when Redis check fails."""
        failing_redis = MagicMock()
        failing_redis.ping = AsyncMock(side_effect=Exception("Redis down"))
        failing_redis.close = AsyncMock()

        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=failing_redis):
                response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["redis"]["status"] == "unhealthy"

    def test_health_includes_timestamp(self, client: TestClient, mock_redis):
        """Health response should include ISO timestamp."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/health")

        data = response.json()
        # Should be ISO format
        assert "T" in data["timestamp"]


class TestReadinessEndpoint:
    """Tests for GET /readiness endpoint (readiness probe)."""

    def test_readiness_ready_returns_200(self, client: TestClient, mock_redis):
        """Readiness endpoint should return 200 when ready."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/readiness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_readiness_db_failure_returns_503(self, client: TestClient, mock_redis):
        """Readiness endpoint should return 503 when DB not ready."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_tx.return_value.__aenter__.side_effect = Exception("DB not ready")

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/readiness")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"

    def test_readiness_response_structure(self, client: TestClient, mock_redis):
        """Readiness response should have correct structure."""
        with patch("app.routes.health.async_transaction") as mock_tx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_tx.return_value.__aenter__.return_value = mock_session

            with patch("app.routes.health.get_redis_client", return_value=mock_redis):
                response = client.get("/readiness")

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
