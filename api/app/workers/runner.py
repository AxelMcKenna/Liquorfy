from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import text, update

from app.core.logging import configure_logging
from app.db.models import IngestionRun
from app.db.session import async_transaction, get_async_session
from app.scrapers.registry import CHAINS, get_chain_scraper

configure_logging()
logger = logging.getLogger(__name__)


# Configuration
SCRAPER_INTERVAL_HOURS = 24  # Run scrapers once per day
SCRAPER_TIMEOUT_MINUTES = 120  # Max time per scraper (Liquor Centre has 90 stores!)
SEQUENTIAL_DELAY_SECONDS = 60  # Delay between scrapers to avoid overwhelming system
RETRY_DELAY_SECONDS = 120  # Wait before retrying a failed chain
MAX_RETRIES = 1  # Number of retries per chain per pass
DB_HEALTH_CHECK_RETRIES = 5
DB_HEALTH_CHECK_DELAY = 10  # seconds between DB health check retries
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


async def _cleanup_zombie_runs() -> int:
    """Mark any leftover 'running' ingestion runs as failed.

    This handles the case where the worker crashed mid-scrape, leaving
    IngestionRun records stuck in 'running' status forever.

    Returns count of cleaned-up runs.
    """
    async with async_transaction() as session:
        stmt = (
            update(IngestionRun)
            .where(IngestionRun.status == "running")
            .values(
                status="failed",
                finished_at=datetime.now(timezone.utc),
                error_message="Worker restarted while scraper was running",
            )
        )
        result = await session.execute(stmt)
        count = getattr(result, "rowcount", 0) or 0

    if count:
        logger.warning(f"Cleaned up {count} zombie ingestion run(s) from previous crash")
    return count


class WorkerScheduler:
    """Manages scraper scheduling and execution with proper error handling."""

    def __init__(self, chains_to_run: Optional[List[str]] = None):
        self.chains_to_run = chains_to_run or list(CHAINS.keys())
        self.last_run: Dict[str, Optional[datetime]] = {chain: None for chain in self.chains_to_run}
        self.running_chains: Dict[str, asyncio.Task] = {}
        self.consecutive_failures: Dict[str, int] = {chain: 0 for chain in self.chains_to_run}

    async def run_scraper(self, chain: str) -> bool:
        """Run a single scraper with timeout and error handling.

        Returns True if the scraper completed successfully, False otherwise.
        """
        logger.info(f"Starting scraper: {chain}")
        start_time = datetime.utcnow()
        timeout_minutes = CHAIN_TIMEOUT_MINUTES.get(chain, SCRAPER_TIMEOUT_MINUTES)

        try:
            scraper = get_chain_scraper(chain)

            await asyncio.wait_for(
                scraper.run(),
                timeout=timeout_minutes * 60
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Scraper completed: {chain} ({duration:.1f}s)")
            self.last_run[chain] = datetime.utcnow()
            self.consecutive_failures[chain] = 0
            return True

        except asyncio.TimeoutError:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Scraper timeout: {chain} (>{duration:.1f}s, limit={timeout_minutes}m)"
            )
            self.consecutive_failures[chain] = self.consecutive_failures.get(chain, 0) + 1
            return False

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Scraper failed: {chain} ({duration:.1f}s) - {type(e).__name__}: {e}")
            logger.exception(e)
            self.consecutive_failures[chain] = self.consecutive_failures.get(chain, 0) + 1
            return False

        finally:
            if chain in self.running_chains:
                del self.running_chains[chain]

            # Log warning for chains with repeated failures
            failures = self.consecutive_failures.get(chain, 0)
            if failures >= 3:
                logger.warning(
                    f"Chain '{chain}' has failed {failures} consecutive times - "
                    f"may need manual investigation"
                )

    async def should_run_scraper(self, chain: str) -> bool:
        """Check if a scraper should run based on schedule."""
        if chain in self.running_chains:
            return False

        last_run = self.last_run.get(chain)
        if last_run is None:
            return True

        time_since_last_run = datetime.utcnow() - last_run
        return time_since_last_run >= timedelta(hours=SCRAPER_INTERVAL_HOURS)

    async def run_all_scrapers(self, force: bool = False) -> None:
        """Run all scrapers sequentially with delays, retrying failures once."""
        logger.info(f"Checking {len(self.chains_to_run)} scrapers for scheduled runs")

        failed_chains: List[str] = []

        for chain in self.chains_to_run:
            if force or await self.should_run_scraper(chain):
                task = asyncio.create_task(self.run_scraper(chain))
                self.running_chains[chain] = task

                try:
                    success = await task
                    if not success:
                        failed_chains.append(chain)
                except Exception as e:
                    logger.error(f"Scraper task failed for chain={chain}: {e}")
                    failed_chains.append(chain)

                logger.info(f"Waiting {SEQUENTIAL_DELAY_SECONDS}s before next scraper...")
                await asyncio.sleep(SEQUENTIAL_DELAY_SECONDS)
            else:
                last_run = self.last_run.get(chain)
                if last_run:
                    time_since = datetime.utcnow() - last_run
                    logger.info(f"Skipping {chain} (last run {time_since.total_seconds() / 3600:.1f}h ago)")

        # Retry failed chains once
        if failed_chains:
            logger.info(
                f"Retrying {len(failed_chains)} failed chain(s) after "
                f"{RETRY_DELAY_SECONDS}s: {', '.join(failed_chains)}"
            )
            await asyncio.sleep(RETRY_DELAY_SECONDS)

            for chain in failed_chains:
                logger.info(f"Retry attempt for: {chain}")
                task = asyncio.create_task(self.run_scraper(chain))
                self.running_chains[chain] = task

                try:
                    await task
                except Exception as e:
                    logger.error(f"Retry failed for chain={chain}: {e}")

                await asyncio.sleep(SEQUENTIAL_DELAY_SECONDS)


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

    logger.info(f"Interval: {SCRAPER_INTERVAL_HOURS}h | Timeout: {SCRAPER_TIMEOUT_MINUTES}m | Retry delay: {RETRY_DELAY_SECONDS}s")
    logger.info(f"Run once: {'yes' if run_once else 'no'}")
    if CHAIN_TIMEOUT_MINUTES:
        overrides = ", ".join(
            f"{chain}={minutes}m" for chain, minutes in CHAIN_TIMEOUT_MINUTES.items()
        )
        logger.info(f"Timeout overrides: {overrides}")
    logger.info("=" * 60)

    # Pre-flight checks
    await _check_db_health()
    await _cleanup_zombie_runs()

    scheduler = WorkerScheduler(chains_to_run=chains_to_run)

    # Run all scrapers once at startup
    logger.info("Running initial scraper pass...")
    await scheduler.run_all_scrapers(force=True)

    try:
        from app.workers.discord_report import send_discord_report

        await send_discord_report()
    except Exception as e:
        logger.warning(f"Discord report failed: {e}")

    # Evaluate price alerts after initial scraper pass
    try:
        from app.services.alert_evaluator import evaluate_alerts

        count = await evaluate_alerts()
        logger.info(f"Alert evaluation: {count} notification(s) sent")
    except Exception as e:
        logger.warning(f"Alert evaluation failed: {e}")

    if run_once:
        logger.info("LIQUORFY_RUN_ONCE enabled - exiting after initial pass")
        return

    # Then run on schedule
    while True:
        logger.info("Worker sleeping for 1 hour...")
        await asyncio.sleep(3600)

        logger.info("Checking for scheduled scraper runs...")
        await scheduler.run_all_scrapers()

        try:
            from app.workers.discord_report import send_discord_report

            await send_discord_report()
        except Exception as e:
            logger.warning(f"Discord report failed: {e}")

        # Periodic promo expiry cleanup (lightweight, runs every cycle)
        try:
            from app.workers.cleanup import run_promo_expiry_cleanup

            await run_promo_expiry_cleanup()
        except Exception as e:
            logger.warning(f"Promo expiry cleanup failed: {e}")

        # Evaluate price alerts and send notifications
        try:
            from app.services.alert_evaluator import evaluate_alerts

            count = await evaluate_alerts()
            logger.info(f"Alert evaluation: {count} notification(s) sent")
        except Exception as e:
            logger.warning(f"Alert evaluation failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        logger.exception(e)
        raise
