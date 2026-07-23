"""Tests for durable ingestion API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _job(*, status: str = "queued") -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        chain="countdown",
        status=status,
        requested_by="testadmin",
        dedupe_key=None,
        scheduled_for=None,
        available_at=now,
        attempt_count=0,
        max_attempts=2,
        claimed_by=None,
        heartbeat_at=None,
        lease_expires_at=None,
        cancel_requested_at=None,
        started_at=None,
        finished_at=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


class TestIngestEndpoint:
    def test_ingest_requires_auth(self, client: TestClient):
        response = client.post("/ingest/run?chain=countdown")
        assert response.status_code == 401

    def test_ingest_with_chain_returns_accepted(
        self,
        client: TestClient,
        auth_headers,
    ):
        job_id = uuid.uuid4()
        enqueue = AsyncMock(return_value=job_id)
        with patch("app.routes.ingest.enqueue_ingest", enqueue):
            response = client.post(
                "/ingest/run?chain=countdown",
                headers=auth_headers,
            )

        assert response.status_code == 202
        assert response.json() == {"job_ids": [str(job_id)]}
        enqueue.assert_awaited_once_with(
            "countdown",
            requested_by="testadmin",
        )

    def test_ingest_with_all_flag(self, client: TestClient, auth_headers):
        enqueue = AsyncMock(side_effect=[uuid.uuid4(), uuid.uuid4()])
        with patch("app.routes.ingest.enqueue_ingest", enqueue):
            with patch(
                "app.routes.ingest.CHAINS",
                {"countdown": None, "paknsave": None},
            ):
                response = client.post(
                    "/ingest/run?all=true",
                    headers=auth_headers,
                )

        assert response.status_code == 202
        assert len(response.json()["job_ids"]) == 2

    def test_ingest_requires_chain_or_all(
        self,
        client: TestClient,
        auth_headers,
    ):
        response = client.post("/ingest/run", headers=auth_headers)
        assert response.status_code == 400

    def test_ingest_rejects_chain_and_all(
        self,
        client: TestClient,
        auth_headers,
    ):
        response = client.post(
            "/ingest/run?chain=countdown&all=true",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_ingest_rejects_unknown_chain(
        self,
        client: TestClient,
        auth_headers,
    ):
        response = client.post(
            "/ingest/run?chain=unknown",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_ingest_invalid_token(
        self,
        client: TestClient,
        invalid_auth_headers,
    ):
        response = client.post(
            "/ingest/run?chain=countdown",
            headers=invalid_auth_headers,
        )
        assert response.status_code == 401


class TestIngestJobs:
    def test_get_job(self, client: TestClient, auth_headers):
        job = _job()
        with patch(
            "app.routes.ingest.get_ingest_job",
            AsyncMock(return_value=job),
        ):
            response = client.get(
                f"/ingest/jobs/{job.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        assert response.json()["max_attempts"] == 2

    def test_get_job_not_found(self, client: TestClient, auth_headers):
        with patch(
            "app.routes.ingest.get_ingest_job",
            AsyncMock(return_value=None),
        ):
            response = client.get(
                f"/ingest/jobs/{uuid.uuid4()}",
                headers=auth_headers,
            )
        assert response.status_code == 404

    def test_list_jobs(self, client: TestClient, auth_headers):
        with patch(
            "app.routes.ingest.list_ingest_jobs",
            AsyncMock(return_value=[_job()]),
        ):
            response = client.get(
                "/ingest/jobs?status=queued",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_jobs_rejects_unknown_status(
        self,
        client: TestClient,
        auth_headers,
    ):
        response = client.get(
            "/ingest/jobs?status=unknown",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_cancel_job(self, client: TestClient, auth_headers):
        job = _job(status="cancelled")
        with patch(
            "app.routes.ingest.cancel_ingest_job",
            AsyncMock(return_value=job),
        ):
            response = client.post(
                f"/ingest/jobs/{job.id}/cancel",
                headers=auth_headers,
            )
        assert response.status_code == 202
        assert response.json()["status"] == "cancelled"
