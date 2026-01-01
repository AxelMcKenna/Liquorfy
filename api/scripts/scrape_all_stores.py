"""
Script to scrape all store locations from NZ liquor chains,
geocode addresses to coordinates, and store in database.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction
from app.services.geocoding import geocode_with_retry
from app.store_scrapers.super_liquor import SuperLiquorLocationScraper
from app.store_scrapers.liquorland import LiquorlandLocationScraper
from app.store_scrapers.countdown import CountdownLocationScraper
from app.store_scrapers.generic import GenericLocationScraper
from app.store_scrapers.glengarry import GlengarryLocationScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define all store locator configurations
SCRAPER_CONFIGS = [
    {
        "chain": "super_liquor",
        "scraper_class": SuperLiquorLocationScraper,
    },
    {
        "chain": "liquorland",
        "scraper_class": LiquorlandLocationScraper,
    },
    {
        "chain": "countdown",
        "scraper_class": CountdownLocationScraper,
    },
    {
        "chain": "new_world",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.newworld.co.nz/store-finder",
    },
    {
        "chain": "pak_n_save",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.paknsave.co.nz/store-finder",
    },
    {
        "chain": "bottle_o",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.thebottleo.co.nz/store-locator",
    },
    {
        "chain": "liquor_centre",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.liquorcentre.co.nz/stores",
    },
    {
        "chain": "glengarry",
        "scraper_class": GlengarryLocationScraper,
    },
]


async def scrape_chain_stores(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape stores for a single chain."""
    chain = config["chain"]
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping stores for: {chain.upper()}")
    logger.info(f"{'='*60}")

    try:
        # Initialize scraper
        if "url" in config:
            # Generic scraper with custom URL
            scraper = config["scraper_class"](chain, config["url"])
        else:
            # Chain-specific scraper
            scraper = config["scraper_class"]()

        async with scraper:
            stores = await scraper.fetch_stores()

        logger.info(f"✓ Successfully scraped {len(stores)} stores for {chain}")
        return stores

    except Exception as e:
        logger.error(f"✗ Failed to scrape {chain}: {e}", exc_info=True)
        return []


async def geocode_stores(stores: List[Dict[str, Any]], chain: str) -> List[Dict[str, Any]]:
    """Geocode stores that don't have coordinates."""
    logger.info(f"\nGeocoding addresses for {chain}...")

    geocoded_count = 0
    failed_count = 0

    for store in stores:
        # Skip if already has coordinates
        if store.get("lat") and store.get("lon"):
            continue

        # Need to geocode
        address = store.get("address")
        if not address:
            logger.warning(f"Store '{store.get('name')}' has no address to geocode")
            failed_count += 1
            continue

        logger.info(f"Geocoding: {store.get('name')} - {address}")

        coords = await geocode_with_retry(address, region="New Zealand")

        if coords:
            store["lat"], store["lon"] = coords
            geocoded_count += 1
            logger.info(f"  ✓ Geocoded to ({coords[0]}, {coords[1]})")
        else:
            logger.error(f"  ✗ Failed to geocode")
            failed_count += 1

    logger.info(f"Geocoding complete: {geocoded_count} geocoded, {failed_count} failed")
    return stores


async def save_stores_to_db(stores: List[Dict[str, Any]], chain: str) -> int:
    """Save stores to database."""
    logger.info(f"\nSaving {len(stores)} stores for {chain} to database...")

    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for store in stores:
            # Skip stores without coordinates
            if not store.get("lat") or not store.get("lon"):
                logger.warning(f"Skipping store without coordinates: {store.get('name')}")
                skipped_count += 1
                continue

            # Upsert store (update if exists based on chain + name, or insert if new)
            stmt = insert(Store).values(
                chain=chain,
                name=store["name"],
                address=store.get("address"),
                region=store.get("region"),
                lat=store["lat"],
                lon=store["lon"],
                url=store.get("url"),
            )

            # On conflict, update the record
            stmt = stmt.on_conflict_do_update(
                index_elements=["chain", "name"],
                set_={
                    "address": stmt.excluded.address,
                    "region": stmt.excluded.region,
                    "lat": stmt.excluded.lat,
                    "lon": stmt.excluded.lon,
                    "url": stmt.excluded.url,
                }
            )

            await session.execute(stmt)
            saved_count += 1

    logger.info(f"✓ Saved {saved_count} stores, skipped {skipped_count}")
    return saved_count


async def scrape_all_stores():
    """Main function to scrape all store locations."""
    logger.info("="*60)
    logger.info("LIQUORFY STORE LOCATION SCRAPER")
    logger.info("="*60)

    all_stores = {}
    total_scraped = 0
    total_geocoded = 0
    total_saved = 0

    # Scrape each chain
    for config in SCRAPER_CONFIGS:
        chain = config["chain"]

        # Scrape stores
        stores = await scrape_chain_stores(config)

        if not stores:
            logger.warning(f"No stores found for {chain}, skipping...")
            continue

        total_scraped += len(stores)

        # Geocode addresses if needed
        stores = await geocode_stores(stores, chain)

        # Save to database
        saved = await save_stores_to_db(stores, chain)
        total_saved += saved

        all_stores[chain] = stores

        # Rate limiting between chains
        logger.info("\nWaiting 2 seconds before next chain...")
        await asyncio.sleep(2)

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SCRAPING COMPLETE - SUMMARY")
    logger.info("="*60)
    logger.info(f"Total chains scraped: {len(all_stores)}")
    logger.info(f"Total stores scraped: {total_scraped}")
    logger.info(f"Total stores saved to DB: {total_saved}")

    for chain, stores in all_stores.items():
        logger.info(f"  {chain}: {len(stores)} stores")

    # Save raw data to file for backup
    output_file = Path(__file__).parent.parent / "data" / "scraped_stores.json"
    with open(output_file, "w") as f:
        json.dump(all_stores, f, indent=2)

    logger.info(f"\nRaw data saved to: {output_file}")

    # Print database stats
    async with async_transaction() as session:
        result = await session.execute(select(func.count()).select_from(Store))
        total_in_db = result.scalar()
        logger.info(f"Total stores now in database: {total_in_db}")


if __name__ == "__main__":
    try:
        asyncio.run(scrape_all_stores())
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
