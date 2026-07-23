"""Durable PostgreSQL-backed ingestion job queue."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID

from sqlalchemy import Select, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IngestionJob
from app.db.session import async_transaction, get_async_session
from app.scrapers.registry import CHAINS

ACTIVE_JOB_STATUSES = ("queued", "running")
TERMINAL_JOB_STATUSES = ("completed", "failed", "cancelled")
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_LEASE_SECONDS = 120
RETRY_BASE_SECONDS = 120


class HeartbeatState(str, Enum):
    ACTIVE = "active"
    CANCEL_REQUESTED = "cancel_requested"
    LEASE_LOST = "lease_lost"


class JobOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ClaimedIngestionJob:
    id: UUID
    chain: str
    attempt_count: int
    max_attempts: int


async def enqueue_ingest(
    chain: str,
    *,
    requested_by: str,
    dedupe_key: str | None = None,
    scheduled_for: datetime | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> UUID:
    """Create a job or return the existing job for this request.

    Only one queued/running job is allowed per chain. A durable ``dedupe_key``
    additionally makes scheduled requests idempotent after they finish.
    """
    if chain not in CHAINS:
        raise ValueError(f"Unknown chain: {chain}")
    if not 1 <= max_attempts <= 10:
        raise ValueError("max_attempts must be between 1 and 10")

    async with async_transaction() as session:
        # Serialize lookup/insert per chain across API and scheduler replicas.
        await session.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtextextended(:lock_name, 0))"
            ),
            {"lock_name": f"liquorfy:ingest:{chain}"},
        )

        if dedupe_key is not None:
            deduped_job_id = await session.scalar(
                select(IngestionJob.id).where(
                    IngestionJob.dedupe_key == dedupe_key
                )
            )
            if deduped_job_id is not None:
                return deduped_job_id

        active_job_id = await session.scalar(
            select(IngestionJob.id)
            .where(
                IngestionJob.chain == chain,
                IngestionJob.status.in_(ACTIVE_JOB_STATUSES),
            )
            .order_by(IngestionJob.created_at.asc())
            .limit(1)
        )
        if active_job_id is not None:
            return active_job_id

        job = IngestionJob(
            chain=chain,
            requested_by=requested_by,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for,
            available_at=datetime.now(timezone.utc),
            max_attempts=max_attempts,
            status="queued",
        )
        session.add(job)
        await session.flush()
        return job.id


async def _recover_expired_jobs(
    session: AsyncSession,
    *,
    now: datetime,
) -> int:
    """Requeue or finish jobs whose worker lease expired."""
    cancelled = await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.status == "running",
            IngestionJob.lease_expires_at <= now,
            IngestionJob.cancel_requested_at.is_not(None),
        )
        .values(
            status="cancelled",
            finished_at=now,
            claimed_by=None,
            heartbeat_at=None,
            lease_expires_at=None,
            error_message="Cancelled after worker lease expired",
        )
    )
    failed = await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.status == "running",
            IngestionJob.lease_expires_at <= now,
            IngestionJob.cancel_requested_at.is_(None),
            IngestionJob.attempt_count >= IngestionJob.max_attempts,
        )
        .values(
            status="failed",
            finished_at=now,
            claimed_by=None,
            heartbeat_at=None,
            lease_expires_at=None,
            error_message="Worker lease expired after final attempt",
        )
    )
    requeued = await session.execute(
        update(IngestionJob)
        .where(
            IngestionJob.status == "running",
            IngestionJob.lease_expires_at <= now,
            IngestionJob.cancel_requested_at.is_(None),
            IngestionJob.attempt_count < IngestionJob.max_attempts,
        )
        .values(
            status="queued",
            available_at=now + timedelta(seconds=RETRY_BASE_SECONDS),
            claimed_by=None,
            heartbeat_at=None,
            lease_expires_at=None,
            error_message="Worker lease expired; retry queued",
        )
    )
    return sum(
        (getattr(result, "rowcount", 0) or 0)
        for result in (cancelled, failed, requeued)
    )


async def recover_expired_ingest_jobs() -> int:
    async with async_transaction() as session:
        return await _recover_expired_jobs(
            session,
            now=datetime.now(timezone.utc),
        )


async def claim_next_ingest_job(
    *,
    worker_id: str,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
) -> ClaimedIngestionJob | None:
    """Atomically claim the oldest ready job without blocking other workers."""
    if lease_seconds < 30:
        raise ValueError("lease_seconds must be at least 30")

    now = datetime.now(timezone.utc)
    async with async_transaction() as session:
        await _recover_expired_jobs(session, now=now)

        job = await session.scalar(
            select(IngestionJob)
            .where(
                IngestionJob.status == "queued",
                IngestionJob.available_at <= now,
                IngestionJob.cancel_requested_at.is_(None),
                IngestionJob.attempt_count < IngestionJob.max_attempts,
            )
            .order_by(IngestionJob.available_at.asc(), IngestionJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None

        job.status = "running"
        job.attempt_count += 1
        job.claimed_by = worker_id
        job.started_at = job.started_at or now
        job.heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        job.error_message = None
        await session.flush()
        return ClaimedIngestionJob(
            id=job.id,
            chain=job.chain,
            attempt_count=job.attempt_count,
            max_attempts=job.max_attempts,
        )


async def heartbeat_ingest_job(
    job_id: UUID,
    *,
    worker_id: str,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
) -> HeartbeatState:
    """Extend a claimed job lease and report cancellation or lease loss."""
    now = datetime.now(timezone.utc)
    async with async_transaction() as session:
        job = await session.get(IngestionJob, job_id, with_for_update=True)
        if (
            job is None
            or job.status != "running"
            or job.claimed_by != worker_id
        ):
            return HeartbeatState.LEASE_LOST
        if job.cancel_requested_at is not None:
            return HeartbeatState.CANCEL_REQUESTED

        job.heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        return HeartbeatState.ACTIVE


async def finish_ingest_job(
    job_id: UUID,
    *,
    worker_id: str,
    outcome: JobOutcome,
    error_message: str | None = None,
) -> str | None:
    """Finish, cancel, or retry a job owned by ``worker_id``."""
    now = datetime.now(timezone.utc)
    async with async_transaction() as session:
        job = await session.get(IngestionJob, job_id, with_for_update=True)
        if (
            job is None
            or job.status != "running"
            or job.claimed_by != worker_id
        ):
            return None

        if outcome is JobOutcome.CANCELLED or job.cancel_requested_at is not None:
            job.status = "cancelled"
            job.finished_at = now
        elif outcome is JobOutcome.SUCCEEDED:
            job.status = "completed"
            job.finished_at = now
        elif job.attempt_count < job.max_attempts:
            delay_seconds = RETRY_BASE_SECONDS * (2 ** (job.attempt_count - 1))
            job.status = "queued"
            job.available_at = now + timedelta(seconds=delay_seconds)
            job.finished_at = None
        else:
            job.status = "failed"
            job.finished_at = now

        job.claimed_by = None
        job.heartbeat_at = None
        job.lease_expires_at = None
        job.error_message = error_message[:1000] if error_message else None
        return job.status


async def cancel_ingest_job(job_id: UUID) -> IngestionJob | None:
    """Cancel a queued job or ask its worker to cancel a running job."""
    now = datetime.now(timezone.utc)
    async with async_transaction() as session:
        job = await session.get(IngestionJob, job_id, with_for_update=True)
        if job is None:
            return None
        if job.status == "queued":
            job.status = "cancelled"
            job.cancel_requested_at = now
            job.finished_at = now
            job.error_message = "Cancelled before execution"
        elif job.status == "running" and job.cancel_requested_at is None:
            job.cancel_requested_at = now
        await session.flush()
        return job


async def get_ingest_job(job_id: UUID) -> IngestionJob | None:
    async with get_async_session() as session:
        return await session.get(IngestionJob, job_id)


def _jobs_query() -> Select[tuple[IngestionJob]]:
    return select(IngestionJob).order_by(IngestionJob.created_at.desc())


async def list_ingest_jobs(
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[IngestionJob]:
    query = _jobs_query()
    if status is not None:
        query = query.where(IngestionJob.status == status)
    async with get_async_session() as session:
        result = await session.execute(query.limit(limit))
        return list(result.scalars().all())


__all__ = [
    "ClaimedIngestionJob",
    "HeartbeatState",
    "JobOutcome",
    "cancel_ingest_job",
    "claim_next_ingest_job",
    "enqueue_ingest",
    "finish_ingest_job",
    "get_ingest_job",
    "heartbeat_ingest_job",
    "list_ingest_jobs",
    "recover_expired_ingest_jobs",
]
