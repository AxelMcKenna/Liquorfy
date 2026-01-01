"""
Clear old price data from the database before re-scraping.

This script safely removes all existing price records while preserving:
- Products (product metadata)
- Stores (store locations and info)
- Ingestion runs (historical scrape logs)

This is useful before a fresh scrape to ensure clean, up-to-date pricing data.
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func, delete

from app.db.models import Price, Product, Store
from app.db.session import async_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_price_data(dry_run: bool = False) -> None:
    """
    Clear all price data from the database.

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Get counts before deletion
    price_count = 0

    async with async_transaction() as session:
        price_count_result = await session.execute(select(func.count(Price.id)))
        price_count = price_count_result.scalar()

        product_count_result = await session.execute(select(func.count(Product.id)))
        product_count = product_count_result.scalar()

        store_count_result = await session.execute(select(func.count(Store.id)))
        store_count = store_count_result.scalar()

        logger.info("=" * 60)
        logger.info("DATABASE CLEANUP - CURRENT STATE")
        logger.info("=" * 60)
        logger.info(f"📦 Products:  {product_count:,} (will be KEPT)")
        logger.info(f"🏪 Stores:    {store_count:,} (will be KEPT)")
        logger.info(f"💰 Prices:    {price_count:,} (will be DELETED)")
        logger.info("=" * 60)

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        logger.info("To actually delete, run: python scripts/clear_price_data.py --confirm")
        return

    # Confirm deletion
    logger.info("")
    logger.warning("⚠️  WARNING: This will delete ALL price records!")
    logger.warning("⚠️  Products and Stores will be preserved.")
    logger.info("")
    response = input("Are you sure you want to continue? Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        logger.info("❌ Aborted by user")
        return

    # Delete all prices
    logger.info("")
    logger.info("🗑️  Deleting price records...")

    async with async_transaction() as session:
        delete_stmt = delete(Price)
        await session.execute(delete_stmt)

    # Verify deletion in new transaction
    async with async_transaction() as session:
        final_price_count_result = await session.execute(select(func.count(Price.id)))
        final_price_count = final_price_count_result.scalar()

        product_count_result = await session.execute(select(func.count(Product.id)))
        product_count = product_count_result.scalar()

        store_count_result = await session.execute(select(func.count(Store.id)))
        store_count = store_count_result.scalar()

    logger.info("=" * 60)
    logger.info("✅ CLEANUP COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Deleted:   {price_count - final_price_count:,} price records")
    logger.info(f"Remaining: {final_price_count:,} prices")
    logger.info(f"Products:  {product_count:,} (unchanged)")
    logger.info(f"Stores:    {store_count:,} (unchanged)")
    logger.info("=" * 60)
    logger.info("")
    logger.info("✨ Database is ready for fresh scraping!")
    logger.info("")


async def main():
    import sys

    # Check for --confirm flag
    dry_run = "--confirm" not in sys.argv

    if dry_run:
        logger.info("Running in DRY RUN mode (no changes will be made)")
        logger.info("")

    await clear_price_data(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
