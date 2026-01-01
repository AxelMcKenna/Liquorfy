"""Run missing store scrapers: Bottle O and Thirsty Liquor."""
import asyncio
import logging
from sqlalchemy import select
from app.store_scrapers.bottle_o import BottleOLocationScraper
from app.store_scrapers.thirsty_liquor import ThirstyLiquorLocationScraper
from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_scraper_and_save(scraper_class, name):
    """Run a store scraper and save results to database."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running {name} store scraper...")
    logger.info(f"{'='*60}\n")

    try:
        # Use scraper as context manager
        async with scraper_class() as scraper:
            # Fetch stores
            stores_data = await scraper.fetch_stores()

            if not stores_data:
                logger.warning(f"No stores found for {name}")
                return

            logger.info(f"Found {len(stores_data)} stores")

            # Save to database
            async with async_transaction() as session:
                # Check existing stores
                result = await session.execute(
                    select(Store).where(Store.chain == scraper.chain)
                )
                existing_stores = {s.name: s for s in result.scalars().all()}

                created = 0
                updated = 0

                for store_data in stores_data:
                    name = store_data.get("name", "").strip()
                    if not name:
                        continue

                    address = store_data.get("address")
                    region = store_data.get("region")
                    lat = store_data.get("lat") or 0.0  # Default to 0.0 if missing
                    lon = store_data.get("lon") or 0.0  # Default to 0.0 if missing
                    url = store_data.get("url")

                    if name in existing_stores:
                        # Update existing
                        store = existing_stores[name]
                        store.address = address
                        store.region = region
                        store.lat = lat
                        store.lon = lon
                        store.url = url
                        updated += 1
                    else:
                        # Create new
                        store = Store(
                            chain=scraper.chain,
                            name=name,
                            address=address,
                            region=region,
                            lat=lat,
                            lon=lon,
                            url=url,
                        )
                        session.add(store)
                        created += 1

                logger.info(f"✓ {name}: Created {created} stores, updated {updated} stores")

    except Exception as e:
        logger.error(f"✗ {name} failed: {e}", exc_info=True)


async def main():
    """Run both missing store scrapers."""

    await run_scraper_and_save(BottleOLocationScraper, "Bottle O")
    await run_scraper_and_save(ThirstyLiquorLocationScraper, "Thirsty Liquor")


if __name__ == "__main__":
    asyncio.run(main())
