"""Tests for ingest API endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestIngestEndpoint:
    """Tests for POST /ingest/run endpoint."""

    def test_ingest_requires_auth(self, client: TestClient):
        """Ingest endpoint should require authentication."""
        response = client.post("/ingest/run?chain=countdown")
        assert response.status_code == 401

    def test_ingest_with_chain(self, client: TestClient, auth_headers):
        """Ingest should accept chain parameter."""
        with patch("app.routes.ingest.enqueue_ingest", AsyncMock(return_value="job-123")):
            response = client.post("/ingest/run?chain=countdown", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "job_ids" in data
        assert "job-123" in data["job_ids"]

    def test_ingest_with_all_flag(self, client: TestClient, auth_headers):
        """Ingest should accept all=true parameter."""
        with patch("app.routes.ingest.enqueue_ingest", AsyncMock(return_value="job-all")):
            with patch("app.routes.ingest.CHAINS", {"countdown": None, "paknsave": None}):
                response = client.post("/ingest/run?all=true", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "job_ids" in data

    def test_ingest_requires_chain_or_all(self, client: TestClient, auth_headers):
        """Ingest should require chain or all parameter."""
        response = client.post("/ingest/run", headers=auth_headers)
        assert response.status_code == 400
        assert "chain" in response.json()["detail"].lower()

    def test_ingest_returns_job_ids(self, client: TestClient, auth_headers):
        """Ingest should return list of job IDs."""
        with patch("app.routes.ingest.enqueue_ingest", AsyncMock(return_value="job-abc")):
            response = client.post("/ingest/run?chain=test", headers=auth_headers)

        data = response.json()
        assert isinstance(data["job_ids"], list)
        assert len(data["job_ids"]) > 0

    def test_ingest_invalid_token(self, client: TestClient, invalid_auth_headers):
        """Ingest should reject invalid token."""
        response = client.post("/ingest/run?chain=countdown", headers=invalid_auth_headers)
        assert response.status_code == 401


class TestIngestMultipleChains:
    """Tests for ingesting multiple chains."""

    def test_ingest_all_chains(self, client: TestClient, auth_headers):
        """Ingest all=true should enqueue all chains."""
        mock_chains = {"countdown": None, "paknsave": None, "newworld": None}
        enqueue_calls = []

        async def mock_enqueue(chain):
            enqueue_calls.append(chain)
            return f"job-{chain}"

        with patch("app.routes.ingest.enqueue_ingest", mock_enqueue):
            with patch("app.routes.ingest.CHAINS", mock_chains):
                response = client.post("/ingest/run?all=true", headers=auth_headers)

        assert response.status_code == 200
        assert len(enqueue_calls) == 3
