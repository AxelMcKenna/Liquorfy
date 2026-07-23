"""Tests for worker API endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


class TestWorkerHealthEndpoint:
    """Tests for GET /worker/health endpoint."""

    def test_worker_health_returns_status(self, client: TestClient, auth_headers):
        """Worker health should return status information."""
        mock_chains = {"chain1": None, "chain2": None}

        with patch("app.routes.worker.CHAINS", mock_chains):
            with patch("app.routes.worker.get_async_session") as mock_session:
                # Mock empty results (never run)
                mock_ctx = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_ctx.execute.return_value = mock_result
                mock_session.return_value.__aenter__.return_value = mock_ctx

                response = client.get("/worker/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "total_scrapers" in data
        assert "scrapers" in data

    def test_worker_health_response_structure(self, client: TestClient, auth_headers):
        """Worker health response should have correct structure."""
        mock_chains = {"test": None}

        with patch("app.routes.worker.CHAINS", mock_chains):
            with patch("app.routes.worker.get_async_session") as mock_session:
                mock_ctx = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_ctx.execute.return_value = mock_result
                mock_session.return_value.__aenter__.return_value = mock_ctx

                response = client.get("/worker/health", headers=auth_headers)

        data = response.json()
        assert "healthy" in data
        assert "total_scrapers" in data
        assert "scrapers_healthy" in data
        assert "scrapers_failing" in data
        assert "scrapers_never_run" in data
        assert "scrapers_running" in data
        assert "scrapers" in data
        assert isinstance(data["scrapers"], list)


class TestListIngestionRunsEndpoint:
    """Tests for GET /worker/runs endpoint."""

    def test_list_runs_empty(self, client: TestClient, auth_headers):
        """Should return empty list when no runs exist."""
        with patch("app.routes.worker.get_async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_ctx.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_ctx

            response = client.get("/worker/runs", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_runs_with_chain_filter(self, client: TestClient, auth_headers):
        """Should filter runs by chain."""
        with patch("app.routes.worker.get_async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_ctx.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_ctx

            response = client.get(
                "/worker/runs?chain=countdown", headers=auth_headers
            )

        assert response.status_code == 200

    def test_list_runs_pagination(self, client: TestClient, auth_headers):
        """Should accept pagination parameters."""
        with patch("app.routes.worker.get_async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_ctx.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_ctx

            response = client.get(
                "/worker/runs?limit=10&offset=5", headers=auth_headers
            )

        assert response.status_code == 200


class TestGetIngestionRunEndpoint:
    """Tests for GET /worker/runs/{run_id} endpoint."""

    def test_get_run_not_found(self, client: TestClient, auth_headers):
        """Should return 404 for non-existent run."""
        run_id = str(uuid.uuid4())

        with patch("app.routes.worker.get_async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_ctx.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_ctx

            response = client.get(
                f"/worker/runs/{run_id}", headers=auth_headers
            )

        assert response.status_code == 404

    def test_get_run_success(
        self, client: TestClient, sample_ingestion_run, auth_headers
    ):
        """Should return run details for valid run."""
        with patch("app.routes.worker.get_async_session") as mock_session:
            mock_ctx = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_ingestion_run
            mock_ctx.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_ctx

            response = client.get(
                f"/worker/runs/{sample_ingestion_run.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["chain"] == "test_chain"
        assert data["status"] == "completed"

    def test_get_run_invalid_uuid(self, client: TestClient, auth_headers):
        """Should return error for invalid UUID."""
        response = client.get(
            "/worker/runs/not-a-uuid", headers=auth_headers
        )
        assert response.status_code == 422


class TestScraperStatus:
    """Tests for scraper status calculation."""

    def test_never_run_status(self, client: TestClient, auth_headers):
        """Should correctly identify scrapers that never ran."""
        mock_chains = {"chain1": None}

        with patch("app.routes.worker.CHAINS", mock_chains):
            with patch("app.routes.worker.get_async_session") as mock_session:
                mock_ctx = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_ctx.execute.return_value = mock_result
                mock_session.return_value.__aenter__.return_value = mock_ctx

                response = client.get("/worker/health", headers=auth_headers)

        data = response.json()
        assert data["scrapers_never_run"] == 1
        assert data["scrapers"][0]["status"] == "never_run"
