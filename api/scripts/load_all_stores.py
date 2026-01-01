"""Load all store locations from scrapers into database."""
from __future__ import annotations
import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.db.models import Store
from app.services.geocoding import geocode_with_retry
from app.store_scrapers.bottle_o import BottleOLocationScraper
from app.store_scrapers.black_bull import BlackBullLocationScraper
from app.store_scrapers.thirsty_liquor import ThirstyLiquorLocationScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def load_stores_from_scraper(scraper_class, chain_name: str, db: Session):
    """Load stores from a scraper into the database."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Loading {chain_name} stores")
    logger.info(f"{'='*60}")

    try:
        async with scraper_class as scraper:
            raw_stores = await scraper.fetch_stores()

            # Parse stores if the scraper has a parse_store method
            if hasattr(scraper, 'parse_store'):
                stores = []
                for raw_store in raw_stores:
                    try:
                        parsed = await scraper.parse_store(raw_store)
                        stores.append(parsed)
                    except Exception as e:
                        logger.warning(f"Failed to parse store: {e}")
                        continue
            else:
                stores = raw_stores

            logger.info(f"Found {len(stores)} {chain_name} stores")

            loaded = 0
            failed = 0

            for store_data in stores:
                try:
                    # Check if store already exists
                    existing = db.query(Store).filter(
                        Store.chain == chain_name,
                        Store.name == store_data['name']
                    ).first()

                    if existing:
                        logger.info(f"  ⏭️  Skipping existing store: {store_data['name']}")
                        continue

                    # Geocode if needed
                    lat = store_data.get('latitude')
                    lng = store_data.get('longitude')

                    if not lat or not lng:
                        address = store_data.get('address', '')
                        suburb = store_data.get('suburb', '')
                        full_address = f"{address}, {suburb}, New Zealand" if suburb else f"{address}, New Zealand"

                        logger.info(f"  🗺️  Geocoding: {full_address}")
                        coords = await geocode_with_retry(full_address)

                        if coords:
                            lat, lng = coords
                            logger.info(f"      ✅ Geocoded to: {lat}, {lng}")
                        else:
                            logger.warning(f"      ❌ Failed to geocode: {full_address}")
                            failed += 1
                            continue

                    # Create store
                    store = Store(
                        name=store_data['name'],
                        chain=chain_name,
                        address=store_data.get('address'),
                        suburb=store_data.get('suburb'),
                        city=store_data.get('city'),
                        region=store_data.get('region'),
                        postcode=store_data.get('postcode'),
                        phone=store_data.get('phone'),
                        latitude=lat,
                        longitude=lng,
                        location=f"POINT({lng} {lat})"
                    )

                    db.add(store)
                    db.commit()
                    loaded += 1
                    logger.info(f"  ✅ Loaded: {store_data['name']}")

                except Exception as e:
                    logger.error(f"  ❌ Error loading store {store_data.get('name')}: {e}")
                    failed += 1
                    db.rollback()
                    continue

            logger.info(f"\n{chain_name} Summary:")
            logger.info(f"  ✅ Loaded: {loaded}")
            logger.info(f"  ❌ Failed: {failed}")
            if len(stores) > 0:
                logger.info(f"  📊 Success Rate: {loaded}/{len(stores)} ({loaded/len(stores)*100:.1f}%)")

    except Exception as e:
        logger.error(f"Failed to scrape {chain_name}: {e}")
        raise


async def main():
    """Load all stores."""
    with get_session() as db:
        # Bottle O
        await load_stores_from_scraper(BottleOLocationScraper(), "Bottle O", db)

        # Black Bull
        await load_stores_from_scraper(BlackBullLocationScraper(), "Black Bull", db)

        # Thirsty Liquor
        await load_stores_from_scraper(ThirstyLiquorLocationScraper(), "Thirsty Liquor", db)

        logger.info(f"\n{'='*60}")
        logger.info("ALL STORES LOADED")
        logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
