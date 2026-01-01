"""Load Super Liquor stores from API."""
from __future__ import annotations
import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.db.models import Store
from app.store_scrapers.super_liquor import SuperLiquorLocationScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Load Super Liquor stores."""
    logger.info("="*60)
    logger.info("Loading Super Liquor Stores")
    logger.info("="*60)

    with get_session() as db:
        async with SuperLiquorLocationScraper() as scraper:
            # Fetch and parse stores
            raw_stores = await scraper.fetch_stores()

            stores = []
            for raw_store in raw_stores:
                try:
                    parsed = await scraper.parse_store(raw_store)
                    stores.append(parsed)
                except Exception as e:
                    logger.warning(f"Failed to parse store: {e}")
                    continue

            logger.info(f"Found {len(stores)} stores")

            loaded = 0
            skipped = 0
            failed = 0

            for store_data in stores:
                try:
                    # Check if store already exists
                    existing = db.query(Store).filter(
                        Store.chain == "Super Liquor",
                        Store.name == store_data['name']
                    ).first()

                    if existing:
                        logger.info(f"  ⏭️  Skipping: {store_data['name']}")
                        skipped += 1
                        continue

                    # Create store
                    store = Store(
                        name=store_data['name'],
                        chain="Super Liquor",
                        address=store_data.get('address'),
                        region=store_data.get('region'),
                        lat=store_data['latitude'],
                        lon=store_data['longitude']
                    )

                    db.add(store)
                    db.commit()
                    loaded += 1
                    logger.info(f"  ✅ Loaded: {store_data['name']}")

                except Exception as e:
                    logger.error(f"  ❌ Error loading {store_data.get('name')}: {e}")
                    failed += 1
                    db.rollback()
                    continue

            logger.info(f"\n{'='*60}")
            logger.info("Summary:")
            logger.info(f"  ✅ Loaded: {loaded}")
            logger.info(f"  ⏭️  Skipped (existing): {skipped}")
            logger.info(f"  ❌ Failed: {failed}")
            logger.info(f"  📊 Total: {loaded + skipped}/{len(stores)}")
            logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
