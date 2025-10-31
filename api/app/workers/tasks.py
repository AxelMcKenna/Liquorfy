from __future__ import annotations

import asyncio
from typing import Dict, List

from app.scrapers.registry import get_chain_scraper

_jobs: Dict[str, str] = {}


async def enqueue_ingest(chain: str) -> str:
    job_id = f"job-{chain}"
    _jobs[job_id] = "queued"

    async def _run() -> None:
        scraper = get_chain_scraper(chain)
        await scraper.run()
        _jobs[job_id] = "finished"

    asyncio.create_task(_run())
    return job_id


async def job_status(job_id: str) -> str:
    return _jobs.get(job_id, "unknown")


__all__ = ["enqueue_ingest", "job_status"]
