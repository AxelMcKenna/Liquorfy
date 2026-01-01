"""
Run all product scrapers sequentially to populate fresh pricing data.

This script runs all 8 configured product scrapers:
1. Super Liquor
2. Liquorland
3. Liquor Centre
4. Bottle O
5. New World
6. PakNSave
7. Countdown
8. Glengarry

Usage:
    # Dry run (shows what would be scraped):
    python scripts/run_all_scrapers.py

    # Actually run scrapers:
    python scripts/run_all_scrapers.py --confirm
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.registry import CHAINS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_duration(start, end):
    """Calculate duration, handling timezone-aware and naive datetimes."""
    try:
        return end - start
    except TypeError:
        # If one is aware and one is naive, convert both to naive
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end
        return end_naive - start_naive


async def run_all_scrapers(dry_run: bool = True):
    """Run all product scrapers sequentially."""

    chains = list(CHAINS.keys())

    logger.info("=" * 70)
    logger.info("SCRAPER EXECUTION PLAN")
    logger.info("=" * 70)
    logger.info(f"Total scrapers: {len(chains)}")
    logger.info(f"Chains to scrape:")
    for i, chain in enumerate(chains, 1):
        logger.info(f"  {i}. {chain}")
    logger.info("=" * 70)

    if dry_run:
        logger.info("")
        logger.info("🔍 DRY RUN MODE - No scraping will occur")
        logger.info("To actually run scrapers: python scripts/run_all_scrapers.py --confirm")
        logger.info("")
        return

    # Confirm execution
    logger.info("")
    logger.warning("⚠️  This will scrape all chains and update the database!")
    logger.warning("⚠️  This may take 30-60 minutes depending on rate limits.")
    logger.info("")
    response = input("Are you sure you want to continue? Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        logger.info("❌ Aborted by user")
        return

    # Track results
    results = {
        "successful": [],
        "failed": [],
        "start_time": datetime.now()
    }

    logger.info("")
    logger.info("🚀 Starting scraper execution...")
    logger.info("")

    for i, chain in enumerate(chains, 1):
        logger.info("=" * 70)
        logger.info(f"[{i}/{len(chains)}] Running {chain} scraper...")
        logger.info("=" * 70)

        try:
            # Get scraper class and instantiate
            scraper_class = CHAINS[chain]

            # Most scrapers don't use fixtures for live scraping
            # Browser-based scrapers ignore use_fixtures parameter
            try:
                scraper = scraper_class(use_fixtures=False)
            except TypeError:
                # Some scrapers don't accept use_fixtures
                scraper = scraper_class()

            # Run the scraper
            run = await scraper.run()

            # Log results
            logger.info("")
            logger.info(f"✅ {chain} completed successfully!")
            logger.info(f"   Status: {run.status}")
            logger.info(f"   Total items: {run.items_total}")
            logger.info(f"   Changed items: {run.items_changed}")
            logger.info(f"   Failed items: {run.items_failed}")
            duration = safe_duration(run.started_at, run.finished_at)
            logger.info(f"   Duration: {duration}")
            logger.info("")

            results["successful"].append({
                "chain": chain,
                "total": run.items_total,
                "changed": run.items_changed,
                "failed": run.items_failed,
                "duration": str(duration)
            })

        except Exception as e:
            logger.error(f"❌ {chain} failed: {e}")
            import traceback
            traceback.print_exc()

            results["failed"].append({
                "chain": chain,
                "error": str(e)
            })

            # Ask whether to continue or abort
            logger.info("")
            response = input(f"Continue with remaining scrapers? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Aborting remaining scrapers")
                break
            logger.info("")

    # Print final summary
    results["end_time"] = datetime.now()
    total_duration = results["end_time"] - results["start_time"]

    logger.info("")
    logger.info("=" * 70)
    logger.info("SCRAPING COMPLETE - FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total duration: {total_duration}")
    logger.info(f"Successful: {len(results['successful'])}/{len(chains)}")
    logger.info(f"Failed: {len(results['failed'])}/{len(chains)}")
    logger.info("")

    if results["successful"]:
        logger.info("✅ Successful scrapers:")
        total_products = 0
        total_changed = 0
        for result in results["successful"]:
            logger.info(f"   • {result['chain']}: {result['total']} products, {result['changed']} changed")
            total_products += result['total']
            total_changed += result['changed']
        logger.info(f"   TOTAL: {total_products:,} products, {total_changed:,} price updates")

    if results["failed"]:
        logger.info("")
        logger.info("❌ Failed scrapers:")
        for result in results["failed"]:
            logger.info(f"   • {result['chain']}: {result['error']}")

    logger.info("=" * 70)
    logger.info("")
    logger.info("🎉 All done! Database has been updated with fresh pricing data.")
    logger.info("")


async def main():
    dry_run = "--confirm" not in sys.argv

    if dry_run:
        logger.info("Running in DRY RUN mode")
        logger.info("")

    await run_all_scrapers(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
