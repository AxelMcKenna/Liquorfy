"""
Worker and scraper health monitoring endpoints.

Provides visibility into scraper status, last run times, and health metrics.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, desc

from app.db.models import IngestionRun
from app.db.session import get_async_session
from app.scrapers.registry import CHAINS

router = APIRouter(prefix="/worker", tags=["worker"])


# ============================================================================
# Schemas
# ============================================================================

class ScraperStatus(BaseModel):
    """Status information for a single scraper."""
    chain: str
    status: str  # success, failed, running, never_run
    last_run_started: Optional[datetime]
    last_run_finished: Optional[datetime]
    last_run_duration_seconds: Optional[float]
    items_total: Optional[int]
    items_changed: Optional[int]
    items_failed: Optional[int]
    success_rate: Optional[float]  # Percentage
    hours_since_last_run: Optional[float]


class WorkerHealthResponse(BaseModel):
    """Overall worker health status."""
    healthy: bool
    total_scrapers: int
    scrapers_healthy: int
    scrapers_failing: int
    scrapers_never_run: int
    scrapers_running: int
    oldest_successful_run_hours: Optional[float]
    scrapers: List[ScraperStatus]


class IngestionRunResponse(BaseModel):
    """Single ingestion run details."""
    id: str
    chain: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    items_total: int
    items_changed: int
    items_failed: int

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health", response_model=WorkerHealthResponse)
async def worker_health():
    """
    Get overall worker health status.

    Returns health metrics for all configured scrapers including:
    - Last run times
    - Success/failure rates
    - Items processed
    - Overall system health
    """
    async with get_async_session() as session:
        scrapers_status = []
        scrapers_healthy = 0
        scrapers_failing = 0
        scrapers_never_run = 0
        scrapers_running = 0
        oldest_success_hours = None

        for chain in CHAINS:
            # Get most recent run for this chain
            result = await session.execute(
                select(IngestionRun)
                .where(IngestionRun.chain == chain)
                .order_by(desc(IngestionRun.started_at))
                .limit(1)
            )
            last_run = result.scalar_one_or_none()

            if not last_run:
                # Never run
                scrapers_never_run += 1
                scrapers_status.append(ScraperStatus(
                    chain=chain,
                    status="never_run",
                    last_run_started=None,
                    last_run_finished=None,
                    last_run_duration_seconds=None,
                    items_total=None,
                    items_changed=None,
                    items_failed=None,
                    success_rate=None,
                    hours_since_last_run=None,
                ))
                continue

            # Calculate metrics
            duration = None
            if last_run.finished_at:
                duration = (last_run.finished_at - last_run.started_at).total_seconds()

            hours_since = (datetime.utcnow() - last_run.started_at).total_seconds() / 3600

            success_rate = None
            if last_run.items_total > 0:
                success_rate = ((last_run.items_total - last_run.items_failed) / last_run.items_total) * 100

            # Determine status
            status = last_run.status

            if status == "completed":
                scrapers_healthy += 1
                if oldest_success_hours is None or hours_since > oldest_success_hours:
                    oldest_success_hours = hours_since
            elif status == "running":
                scrapers_running += 1
            else:
                scrapers_failing += 1

            scrapers_status.append(ScraperStatus(
                chain=chain,
                status=status,
                last_run_started=last_run.started_at,
                last_run_finished=last_run.finished_at,
                last_run_duration_seconds=duration,
                items_total=last_run.items_total,
                items_changed=last_run.items_changed,
                items_failed=last_run.items_failed,
                success_rate=success_rate,
                hours_since_last_run=hours_since,
            ))

        # Overall health: healthy if at least 50% of scrapers have run successfully recently
        # and no scrapers have been running for > 2 hours
        healthy = (
            scrapers_healthy >= len(CHAINS) * 0.5
            and (oldest_success_hours is None or oldest_success_hours < 48)
        )

        return WorkerHealthResponse(
            healthy=healthy,
            total_scrapers=len(CHAINS),
            scrapers_healthy=scrapers_healthy,
            scrapers_failing=scrapers_failing,
            scrapers_never_run=scrapers_never_run,
            scrapers_running=scrapers_running,
            oldest_successful_run_hours=oldest_success_hours,
            scrapers=scrapers_status,
        )


@router.get("/runs", response_model=List[IngestionRunResponse])
async def list_ingestion_runs(
    chain: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List recent ingestion runs.

    Args:
        chain: Filter by chain name (optional)
        limit: Maximum number of runs to return (default 50)
        offset: Number of runs to skip (default 0)

    Returns:
        List of ingestion runs, most recent first
    """
    async with get_async_session() as session:
        query = select(IngestionRun).order_by(desc(IngestionRun.started_at))

        if chain:
            query = query.where(IngestionRun.chain == chain)

        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        runs = result.scalars().all()

        return [
            IngestionRunResponse(
                id=str(run.id),
                chain=run.chain,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                duration_seconds=(
                    (run.finished_at - run.started_at).total_seconds()
                    if run.finished_at else None
                ),
                items_total=run.items_total,
                items_changed=run.items_changed,
                items_failed=run.items_failed,
            )
            for run in runs
        ]


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
async def get_ingestion_run(run_id: str):
    """
    Get details for a specific ingestion run.

    Args:
        run_id: UUID of the ingestion run

    Returns:
        Ingestion run details
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(IngestionRun).where(IngestionRun.id == run_id)
        )
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(status_code=404, detail="Ingestion run not found")

        return IngestionRunResponse(
            id=str(run.id),
            chain=run.chain,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_seconds=(
                (run.finished_at - run.started_at).total_seconds()
                if run.finished_at else None
            ),
            items_total=run.items_total,
            items_changed=run.items_changed,
            items_failed=run.items_failed,
        )


__all__ = ["router"]
