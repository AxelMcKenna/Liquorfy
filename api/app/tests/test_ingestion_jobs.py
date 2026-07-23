"""Unit tests for ingestion queue leases, retries, and scheduling."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.models import IngestionJob
from app.workers.scheduler import NZ_TIMEZONE, enqueue_nightly_jobs
from app.workers.tasks import (
    HeartbeatState,
    JobOutcome,
    cancel_ingest_job,
    claim_next_ingest_job,
    finish_ingest_job,
    heartbeat_ingest_job,
)


def _job(
    *,
    status: str = "queued",
    attempt_count: int = 0,
    max_attempts: int = 2,
    claimed_by: str | None = None,
) -> IngestionJob:
    now = datetime.now(timezone.utc)
    return IngestionJob(
        id=uuid.uuid4(),
        chain="countdown",
        status=status,
        requested_by="test",
        available_at=now,
        attempt_count=attempt_count,
        max_attempts=max_attempts,
        claimed_by=claimed_by,
        started_at=None,
        finished_at=None,
    )


def _transaction(session):
    @asynccontextmanager
    async def transaction():
        yield session

    return transaction


@pytest.mark.asyncio
async def test_claim_sets_owner_attempt_and_lease():
    session = MagicMock()
    session.execute = AsyncMock(return_value=SimpleNamespace(rowcount=0))
    session.flush = AsyncMock()
    job = _job()
    session.scalar = AsyncMock(return_value=job)

    with patch(
        "app.workers.tasks.async_transaction",
        _transaction(session),
    ):
        claimed = await claim_next_ingest_job(
            worker_id="worker-1",
            lease_seconds=120,
        )

    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.attempt_count == 1
    assert job.status == "running"
    assert job.claimed_by == "worker-1"
    assert job.heartbeat_at is not None
    assert job.lease_expires_at > job.heartbeat_at


@pytest.mark.asyncio
async def test_heartbeat_detects_cancellation():
    session = MagicMock()
    job = _job(status="running", attempt_count=1, claimed_by="worker-1")
    job.cancel_requested_at = datetime.now(timezone.utc)
    session.get = AsyncMock(return_value=job)

    with patch(
        "app.workers.tasks.async_transaction",
        _transaction(session),
    ):
        state = await heartbeat_ingest_job(
            job.id,
            worker_id="worker-1",
        )

    assert state is HeartbeatState.CANCEL_REQUESTED


@pytest.mark.asyncio
async def test_failed_attempt_requeues_with_backoff():
    session = MagicMock()
    job = _job(status="running", attempt_count=1, claimed_by="worker-1")
    session.get = AsyncMock(return_value=job)
    before = datetime.now(timezone.utc)

    with patch(
        "app.workers.tasks.async_transaction",
        _transaction(session),
    ):
        status = await finish_ingest_job(
            job.id,
            worker_id="worker-1",
            outcome=JobOutcome.FAILED,
            error_message="temporary failure",
        )

    assert status == "queued"
    assert job.available_at > before + timedelta(seconds=100)
    assert job.claimed_by is None
    assert job.error_message == "temporary failure"


@pytest.mark.asyncio
async def test_final_failed_attempt_is_terminal():
    session = MagicMock()
    job = _job(
        status="running",
        attempt_count=2,
        max_attempts=2,
        claimed_by="worker-1",
    )
    session.get = AsyncMock(return_value=job)

    with patch(
        "app.workers.tasks.async_transaction",
        _transaction(session),
    ):
        status = await finish_ingest_job(
            job.id,
            worker_id="worker-1",
            outcome=JobOutcome.FAILED,
            error_message="permanent failure",
        )

    assert status == "failed"
    assert job.finished_at is not None


@pytest.mark.asyncio
async def test_queued_job_cancels_immediately():
    session = MagicMock()
    session.flush = AsyncMock()
    job = _job()
    session.get = AsyncMock(return_value=job)

    with patch(
        "app.workers.tasks.async_transaction",
        _transaction(session),
    ):
        cancelled = await cancel_ingest_job(job.id)

    assert cancelled is job
    assert job.status == "cancelled"
    assert job.finished_at is not None


@pytest.mark.asyncio
async def test_scheduler_uses_auckland_date_dedupe_keys():
    now = datetime(2026, 7, 23, 3, tzinfo=NZ_TIMEZONE)
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    enqueue = AsyncMock(side_effect=[first_id, second_id])

    with patch(
        "app.workers.scheduler.CHAINS",
        {"countdown": None, "new_world": None},
    ):
        with patch("app.workers.scheduler.enqueue_ingest", enqueue):
            job_ids = await enqueue_nightly_jobs(now=now)

    assert job_ids == [str(first_id), str(second_id)]
    assert enqueue.await_args_list[0].kwargs["dedupe_key"] == (
        "nightly:2026-07-23:countdown"
    )
    assert enqueue.await_args_list[1].kwargs["dedupe_key"] == (
        "nightly:2026-07-23:new_world"
    )
