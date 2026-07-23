from __future__ import annotations

import asyncio
import logging
import os
import socket
import sys
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.logging import configure_logging
from app.db.session import get_async_session
from app.scrapers.registry import CHAINS, get_chain_scraper
from app.workers.tasks import (
    HeartbeatState,
    JobOutcome,
    claim_next_ingest_job,
    enqueue_ingest,
    finish_ingest_job,
    get_ingest_job,
    heartbeat_ingest_job,
    recover_expired_ingest_jobs,
)

configure_logging()
logger = logging.getLogger(__name__)


# Configuration
SCRAPER_TIMEOUT_MINUTES = 120  # Max time per scraper (Liquor Centre has 90 stores!)
DB_HEALTH_CHECK_RETRIES = 5
DB_HEALTH_CHECK_DELAY = 10  # seconds between DB health check retries
JOB_POLL_SECONDS = 5
MAINTENANCE_INTERVAL_SECONDS = 900
JOB_LEASE_SECONDS = 120
JOB_HEARTBEAT_SECONDS = 30
CHAIN_TIMEOUT_MINUTES = {
    # Liquorland category pagination is significantly larger than other chains.
    "liquorland": 300,
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def _check_db_health() -> None:
    """Verify database connectivity before starting scrapers.

    Retries up to DB_HEALTH_CHECK_RETRIES times with DB_HEALTH_CHECK_DELAY
    between attempts. Raises RuntimeError if DB is unreachable.
    """
    for attempt in range(1, DB_HEALTH_CHECK_RETRIES + 1):
        try:
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("DB health check passed")
            return
        except Exception as e:
            if attempt < DB_HEALTH_CHECK_RETRIES:
                logger.warning(
                    f"DB health check failed (attempt {attempt}/{DB_HEALTH_CHECK_RETRIES}): {e}"
                )
                await asyncio.sleep(DB_HEALTH_CHECK_DELAY)
            else:
                raise RuntimeError(
                    f"DB unreachable after {DB_HEALTH_CHECK_RETRIES} attempts: {e}"
                ) from e


class ScraperExecutor:
    """Execute one scraper at a time for jobs claimed from the durable queue."""

    def __init__(self, chains_to_run: Optional[List[str]] = None):
        self.chains_to_run = chains_to_run or list(CHAINS.keys())
        self.consecutive_failures: Dict[str, int] = {chain: 0 for chain in self.chains_to_run}

    async def run_scraper(self, chain: str) -> bool:
        """Run a single scraper with timeout and error handling.

        Returns True if the scraper completed successfully, False otherwise.
        """
        logger.info(f"Starting scraper: {chain}")
        start_time = datetime.now(timezone.utc)
        timeout_minutes = CHAIN_TIMEOUT_MINUTES.get(chain, SCRAPER_TIMEOUT_MINUTES)

        try:
            scraper = get_chain_scraper(chain)

            await asyncio.wait_for(scraper.run(), timeout=timeout_minutes * 60)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Scraper completed: {chain} ({duration:.1f}s)")
            self.consecutive_failures[chain] = 0
            return True

        except asyncio.TimeoutError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Scraper timeout: {chain} (>{duration:.1f}s, limit={timeout_minutes}m)")
            self.consecutive_failures[chain] = self.consecutive_failures.get(chain, 0) + 1
            return False

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Scraper failed: {chain} ({duration:.1f}s) - {type(e).__name__}: {e}")
            logger.exception(e)
            self.consecutive_failures[chain] = self.consecutive_failures.get(chain, 0) + 1
            return False

        finally:
            # Log warning for chains with repeated failures
            failures = self.consecutive_failures.get(chain, 0)
            if failures >= 3:
                logger.warning(
                    f"Chain '{chain}' has failed {failures} consecutive times - "
                    f"may need manual investigation"
                )


async def _post_scrape_tasks() -> None:
    """Run discord report and alert evaluation after a scrape pass."""
    try:
        from app.workers.discord_report import send_discord_report

        await send_discord_report()
    except Exception as e:
        logger.warning(f"Discord report failed: {e}")

    try:
        from app.services.alert_evaluator import evaluate_alerts

        count = await evaluate_alerts()
        logger.info(f"Alert evaluation: {count} notification(s) sent")
    except Exception as e:
        logger.warning(f"Alert evaluation failed: {e}")


async def _maintain_job_lease(
    job_id: UUID,
    *,
    worker_id: str,
    stop: asyncio.Event,
) -> HeartbeatState:
    """Heartbeat until the scrape finishes, cancellation is requested, or ownership is lost."""
    while not stop.is_set():
        try:
            await asyncio.wait_for(
                stop.wait(),
                timeout=JOB_HEARTBEAT_SECONDS,
            )
            return HeartbeatState.ACTIVE
        except asyncio.TimeoutError:
            try:
                state = await heartbeat_ingest_job(
                    job_id,
                    worker_id=worker_id,
                    lease_seconds=JOB_LEASE_SECONDS,
                )
            except Exception:
                logger.exception("Could not heartbeat ingestion job %s", job_id)
                return HeartbeatState.LEASE_LOST
            if state is not HeartbeatState.ACTIVE:
                return state
    return HeartbeatState.ACTIVE


async def _run_claimed_job(
    executor: ScraperExecutor,
    *,
    worker_id: str,
    job_id: UUID,
    chain: str,
) -> str | None:
    stop_heartbeat = asyncio.Event()
    scrape_task = asyncio.create_task(executor.run_scraper(chain))
    heartbeat_task = asyncio.create_task(
        _maintain_job_lease(
            job_id,
            worker_id=worker_id,
            stop=stop_heartbeat,
        )
    )

    done, _ = await asyncio.wait(
        {scrape_task, heartbeat_task},
        return_when=asyncio.FIRST_COMPLETED,
    )
    error_message: str | None

    if heartbeat_task in done and not scrape_task.done():
        heartbeat_state = await heartbeat_task
        scrape_task.cancel()
        with suppress(asyncio.CancelledError):
            await scrape_task
        outcome = (
            JobOutcome.CANCELLED
            if heartbeat_state is HeartbeatState.CANCEL_REQUESTED
            else JobOutcome.FAILED
        )
        error_message = (
            "Cancellation requested"
            if outcome is JobOutcome.CANCELLED
            else "Worker lost the database lease"
        )
    else:
        try:
            succeeded = await scrape_task
        except Exception as exc:
            logger.exception("Ingestion job %s crashed", job_id)
            succeeded = False
            error_message = f"{type(exc).__name__}: {exc}"
        else:
            error_message = None if succeeded else "Scraper failed; inspect ingestion run"
        stop_heartbeat.set()
        heartbeat_state = await heartbeat_task
        if heartbeat_state is HeartbeatState.CANCEL_REQUESTED:
            outcome = JobOutcome.CANCELLED
            error_message = "Cancellation requested"
        elif heartbeat_state is HeartbeatState.LEASE_LOST:
            outcome = JobOutcome.FAILED
            error_message = "Worker lost the database lease"
        else:
            outcome = JobOutcome.SUCCEEDED if succeeded else JobOutcome.FAILED

    return await finish_ingest_job(
        job_id,
        worker_id=worker_id,
        outcome=outcome,
        error_message=error_message,
    )


async def _drain_ingest_jobs(
    executor: ScraperExecutor,
    *,
    worker_id: str,
) -> int:
    """Run ready jobs sequentially, while other workers skip claimed rows."""
    processed = 0
    while True:
        job = await claim_next_ingest_job(
            worker_id=worker_id,
            lease_seconds=JOB_LEASE_SECONDS,
        )
        if job is None:
            return processed

        logger.info(
            "Claimed ingestion job %s for %s (attempt %s/%s)",
            job.id,
            job.chain,
            job.attempt_count,
            job.max_attempts,
        )
        final_status = await _run_claimed_job(
            executor,
            worker_id=worker_id,
            job_id=job.id,
            chain=job.chain,
        )
        logger.info("Ingestion job %s transitioned to %s", job.id, final_status)
        processed += 1


async def _run_maintenance() -> None:
    try:
        from app.workers.cleanup import (
            run_price_history_cleanup,
            run_promo_expiry_cleanup,
        )

        await run_promo_expiry_cleanup()
        await run_price_history_cleanup()
    except Exception as exc:
        logger.warning("Cleanup failed: %s", exc)


async def main(chains_to_run: Optional[List[str]] = None) -> None:
    """Main worker loop."""
    # Parse chains from command line args or env var if not provided
    if chains_to_run is None:
        env_chains = os.environ.get("LIQUORFY_CHAINS")
        if env_chains:
            chains_to_run = [c.strip() for c in env_chains.split(",")]
        elif len(sys.argv) > 1:
            chains_to_run = sys.argv[1].split(",")

    logger.info("=" * 60)
    logger.info("Starting Liquorfy Worker")
    logger.info("=" * 60)
    run_once = _env_bool("LIQUORFY_RUN_ONCE", default=False)

    if chains_to_run:
        invalid_chains = [c for c in chains_to_run if c not in CHAINS]
        if invalid_chains:
            logger.error(f"Invalid chains: {', '.join(invalid_chains)}")
            logger.error(f"Available chains: {', '.join(CHAINS.keys())}")
            sys.exit(1)
        logger.info(f"Running specific chains: {', '.join(chains_to_run)}")
    else:
        chains_to_run = list(CHAINS.keys())
        logger.info(f"Running all chains: {', '.join(chains_to_run)}")

    worker_id = os.environ.get("LIQUORFY_WORKER_ID") or (
        f"{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"
    )

    logger.info(
        "Worker id: %s | Default scraper timeout: %sm",
        worker_id,
        SCRAPER_TIMEOUT_MINUTES,
    )
    logger.info(f"Run once: {'yes' if run_once else 'no'}")
    if CHAIN_TIMEOUT_MINUTES:
        overrides = ", ".join(
            f"{chain}={minutes}m" for chain, minutes in CHAIN_TIMEOUT_MINUTES.items()
        )
        logger.info(f"Timeout overrides: {overrides}")
    logger.info("=" * 60)

    # Pre-flight checks
    await _check_db_health()
    recovered = await recover_expired_ingest_jobs()
    if recovered:
        logger.warning("Recovered %s ingestion job(s) with expired leases", recovered)

    executor = ScraperExecutor(chains_to_run=chains_to_run)

    if run_once:
        logger.info("Queueing one-off scraper pass")
        requested_job_ids = [
            await enqueue_ingest(
                chain,
                requested_by=f"worker-cli:{worker_id}",
            )
            for chain in chains_to_run
        ]
        processed_total = 0
        while True:
            processed_total += await _drain_ingest_jobs(
                executor,
                worker_id=worker_id,
            )
            jobs = [await get_ingest_job(job_id) for job_id in requested_job_ids]
            if all(
                job is not None and job.status in {"completed", "failed", "cancelled"}
                for job in jobs
            ):
                break
            await asyncio.sleep(JOB_POLL_SECONDS)
        if processed_total:
            await _post_scrape_tasks()
        logger.info("LIQUORFY_RUN_ONCE enabled - exiting after queued pass")
        return

    # Scheduling runs in app.workers.scheduler. This process only consumes jobs.
    last_maintenance_at = 0.0
    while True:
        processed = await _drain_ingest_jobs(
            executor,
            worker_id=worker_id,
        )
        if processed:
            await _post_scrape_tasks()
            continue

        now_monotonic = time.monotonic()
        if now_monotonic - last_maintenance_at >= MAINTENANCE_INTERVAL_SECONDS:
            await _run_maintenance()
            last_maintenance_at = now_monotonic

        await asyncio.sleep(JOB_POLL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        logger.exception(e)
        raise
