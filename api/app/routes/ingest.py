from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_admin
from app.scrapers.registry import CHAINS
from app.workers.tasks import enqueue_ingest

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/run")
async def run_ingest(
    chain: str | None = Query(None),
    all: bool = Query(False, alias="all"),
    _: str = Depends(require_admin),
) -> Dict[str, List[str]]:
    chains = [chain] if chain else list(CHAINS.keys()) if all else []
    if not chains:
        raise HTTPException(status_code=400, detail="Provide chain= or all=true")
    job_ids: List[str] = []
    for ch in chains:
        job_id = await enqueue_ingest(ch)
        job_ids.append(job_id)
    return {"job_ids": job_ids}
