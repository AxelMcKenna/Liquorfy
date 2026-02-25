from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.logging import configure_logging
from app.scrapers.registry import CHAINS, get_chain_scraper

configure_logging()
logger = logging.getLogger(__name__)


# Configuration
SCRAPER_INTERVAL_HOURS = 24  # Run scrapers once per day
SCRAPER_TIMEOUT_MINUTES = 120  # Max time per scraper (Liquor Centre has 90 stores!)
SEQUENTIAL_DELAY_SECONDS = 60  # Delay between scrapers to avoid overwhelming system
CHAIN_TIMEOUT_MINUTES = {
    # Liquorland category pagination is significantly larger than other chains.
    "liquorland": 300,
}


class WorkerScheduler:
    """Manages scraper scheduling and execution with proper error handling."""

    def __init__(self, chains_to_run: Optional[List[str]] = None):
        """
        Initialize scheduler.

        Args:
            chains_to_run: Optional list of specific chains to run. If None, runs all chains.
        """
        self.chains_to_run = chains_to_run or list(CHAINS.keys())
        self.last_run: Dict[str, Optional[datetime]] = {chain: None for chain in self.chains_to_run}
        self.running_chains: Dict[str, asyncio.Task] = {}

    async def run_scraper(self, chain: str) -> None:
        """Run a single scraper with timeout and error handling."""
        logger.info(f"🚀 Starting scraper: {chain}")
        start_time = datetime.utcnow()
        timeout_minutes = CHAIN_TIMEOUT_MINUTES.get(chain, SCRAPER_TIMEOUT_MINUTES)

        try:
            scraper = get_chain_scraper(chain)

            # Run with timeout
            await asyncio.wait_for(
                scraper.run(),
                timeout=timeout_minutes * 60
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Scraper completed: {chain} ({duration:.1f}s)")
            self.last_run[chain] = datetime.utcnow()

        except asyncio.TimeoutError:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"⏱️ Scraper timeout: {chain} (>{duration:.1f}s, limit={timeout_minutes}m)"
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Scraper failed: {chain} ({duration:.1f}s) - {type(e).__name__}: {e}")
            logger.exception(e)

        finally:
            # Remove from running tasks
            if chain in self.running_chains:
                del self.running_chains[chain]

    async def should_run_scraper(self, chain: str) -> bool:
        """Check if a scraper should run based on schedule."""
        if chain in self.running_chains:
            return False  # Already running

        last_run = self.last_run.get(chain)
        if last_run is None:
            return True  # Never run before

        # Check if enough time has passed
        time_since_last_run = datetime.utcnow() - last_run
        return time_since_last_run >= timedelta(hours=SCRAPER_INTERVAL_HOURS)

    async def run_all_scrapers(self, force: bool = False) -> None:
        """Run all scrapers sequentially with delays."""
        logger.info(f"📋 Checking {len(self.chains_to_run)} scrapers for scheduled runs")

        for chain in self.chains_to_run:
            if force or await self.should_run_scraper(chain):
                # Run scraper
                task = asyncio.create_task(self.run_scraper(chain))
                self.running_chains[chain] = task

                # Wait for completion — catch failures so remaining chains still run
                try:
                    await task
                except Exception as e:
                    logger.error(f"❌ Scraper failed for chain={chain}: {e}")

                # Delay between scrapers to avoid overwhelming the system
                logger.info(f"⏸️  Waiting {SEQUENTIAL_DELAY_SECONDS}s before next scraper...")
                await asyncio.sleep(SEQUENTIAL_DELAY_SECONDS)
            else:
                last_run = self.last_run.get(chain)
                if last_run:
                    time_since = datetime.utcnow() - last_run
                    logger.info(f"⏭️  Skipping {chain} (last run {time_since.total_seconds() / 3600:.1f}h ago)")


async def main(chains_to_run: Optional[List[str]] = None) -> None:
    """
    Main worker loop.

    Args:
        chains_to_run: Optional list of specific chains to run. If None, runs all chains.
    """
    # Parse chains from command line args or env var if not provided
    if chains_to_run is None:
        # Check environment variable
        env_chains = os.environ.get("LIQUORFY_CHAINS")
        if env_chains:
            chains_to_run = [c.strip() for c in env_chains.split(",")]
        # Check command line args
        elif len(sys.argv) > 1:
            chains_to_run = sys.argv[1].split(",")

    logger.info("=" * 60)
    logger.info("🔧 Starting Liquorfy Worker")
    logger.info("=" * 60)

    if chains_to_run:
        # Validate chains
        invalid_chains = [c for c in chains_to_run if c not in CHAINS]
        if invalid_chains:
            logger.error(f"❌ Invalid chains: {', '.join(invalid_chains)}")
            logger.error(f"Available chains: {', '.join(CHAINS.keys())}")
            sys.exit(1)
        logger.info(f"🎯 Running specific chains: {', '.join(chains_to_run)}")
    else:
        chains_to_run = list(CHAINS.keys())
        logger.info(f"📦 Running all chains: {', '.join(chains_to_run)}")

    logger.info(f"Interval: {SCRAPER_INTERVAL_HOURS}h")
    logger.info(f"Timeout: {SCRAPER_TIMEOUT_MINUTES}m")
    if CHAIN_TIMEOUT_MINUTES:
        overrides = ", ".join(
            f"{chain}={minutes}m" for chain, minutes in CHAIN_TIMEOUT_MINUTES.items()
        )
        logger.info(f"Timeout overrides: {overrides}")
    logger.info("=" * 60)

    scheduler = WorkerScheduler(chains_to_run=chains_to_run)

    # Run all scrapers once at startup
    logger.info("🏁 Running initial scraper pass...")
    await scheduler.run_all_scrapers(force=True)

    try:
        from app.workers.discord_report import send_discord_report

        await send_discord_report()
    except Exception as e:
        logger.warning(f"Discord report failed: {e}")

    # Then run on schedule
    while True:
        logger.info("💤 Worker sleeping for 1 hour...")
        await asyncio.sleep(3600)  # Check every hour

        logger.info("⏰ Checking for scheduled scraper runs...")
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Worker stopped by user")
    except Exception as e:
        logger.error(f"💥 Worker crashed: {e}")
        logger.exception(e)
        raise
