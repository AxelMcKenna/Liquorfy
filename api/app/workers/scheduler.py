"""Durable nightly ingestion scheduler.

This process only inserts idempotent jobs. Scraping is performed by one or more
``app.workers.runner`` processes.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.core.logging import configure_logging
from app.db.session import get_async_session
from app.scrapers.registry import CHAINS
from app.workers.tasks import enqueue_ingest

configure_logging()
logger = logging.getLogger(__name__)

NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")
SCHEDULER_POLL_SECONDS = 60


def _schedule_hour() -> int:
    value = int(os.environ.get("LIQUORFY_SCHEDULE_HOUR", "2"))
    if not 0 <= value <= 23:
        raise ValueError("LIQUORFY_SCHEDULE_HOUR must be between 0 and 23")
    return value


async def _check_db_health() -> None:
    async with get_async_session() as session:
        await session.execute(text("SELECT 1"))


async def enqueue_nightly_jobs(
    *,
    now: datetime | None = None,
) -> list[str]:
    """Insert today's jobs once the configured Auckland hour has passed."""
    now_nz = (now or datetime.now(NZ_TIMEZONE)).astimezone(NZ_TIMEZONE)
    schedule_hour = _schedule_hour()
    if now_nz.hour < schedule_hour:
        return []

    scheduled_for = now_nz.replace(
        hour=schedule_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    schedule_date = scheduled_for.date().isoformat()
    job_ids = []
    for chain in CHAINS:
        job_id = await enqueue_ingest(
            chain,
            requested_by=f"scheduler:{schedule_date}",
            dedupe_key=f"nightly:{schedule_date}:{chain}",
            scheduled_for=scheduled_for,
        )
        job_ids.append(str(job_id))
    return job_ids


async def main() -> None:
    await _check_db_health()
    logger.info(
        "Starting ingestion scheduler at %02d:00 Pacific/Auckland",
        _schedule_hour(),
    )
    while True:
        try:
            job_ids = await enqueue_nightly_jobs()
            if job_ids:
                logger.info("Ensured %s nightly ingestion job(s)", len(job_ids))
        except Exception:
            logger.exception("Nightly ingestion scheduling failed")
        await asyncio.sleep(SCHEDULER_POLL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
