from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.auth import require_admin
from app.scrapers.registry import CHAINS
from app.workers.tasks import (
    ACTIVE_JOB_STATUSES,
    TERMINAL_JOB_STATUSES,
    cancel_ingest_job,
    enqueue_ingest,
    get_ingest_job,
    list_ingest_jobs,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestJobsResponse(BaseModel):
    job_ids: list[UUID]


class IngestJobResponse(BaseModel):
    id: UUID
    chain: str
    status: str
    requested_by: str
    dedupe_key: str | None
    scheduled_for: datetime | None
    available_at: datetime
    attempt_count: int
    max_attempts: int
    claimed_by: str | None
    heartbeat_at: datetime | None
    lease_expires_at: datetime | None
    cancel_requested_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


@router.post(
    "/run",
    response_model=IngestJobsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_ingest(
    chain: str | None = Query(None),
    all_chains: bool = Query(False, alias="all"),
    admin_username: str = Depends(require_admin),
) -> IngestJobsResponse:
    if chain is not None and all_chains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either chain= or all=true, not both",
        )
    if chain is not None and chain not in CHAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown chain: {chain}",
        )

    chains = [chain] if chain else list(CHAINS) if all_chains else []
    if not chains:
        raise HTTPException(status_code=400, detail="Provide chain= or all=true")
    job_ids: list[UUID] = []
    for ch in chains:
        job_id = await enqueue_ingest(ch, requested_by=admin_username)
        job_ids.append(job_id)
    return IngestJobsResponse(job_ids=job_ids)


@router.get("/jobs", response_model=list[IngestJobResponse])
async def list_jobs(
    job_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    _: str = Depends(require_admin),
) -> list[IngestJobResponse]:
    valid_statuses = {*ACTIVE_JOB_STATUSES, *TERMINAL_JOB_STATUSES}
    if job_status is not None and job_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown job status: {job_status}",
        )
    jobs = await list_ingest_jobs(status=job_status, limit=limit)
    return [IngestJobResponse.from_orm(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=IngestJobResponse)
async def get_job(
    job_id: UUID,
    _: str = Depends(require_admin),
) -> IngestJobResponse:
    job = await get_ingest_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion job not found",
        )
    return IngestJobResponse.from_orm(job)


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=IngestJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_job(
    job_id: UUID,
    _: str = Depends(require_admin),
) -> IngestJobResponse:
    job = await cancel_ingest_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion job not found",
        )
    return IngestJobResponse.from_orm(job)
