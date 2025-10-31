from __future__ import annotations

import asyncio
import logging

from app.scrapers.registry import CHAINS
from app.workers.tasks import enqueue_ingest

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting Liquorfy worker")
    # As a demo, schedule ingestion for enabled chains once at startup.
    for chain in CHAINS:
        await enqueue_ingest(chain)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
