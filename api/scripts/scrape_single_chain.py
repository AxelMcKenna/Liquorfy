"""
Script to scrape stores for a single chain.
Usage: python scrape_single_chain.py <chain_name>
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
from app.store_scrapers.countdown import CountdownLocationScraper
from app.store_scrapers.liquorland import LiquorlandLocationScraper
from app.store_scrapers.thirsty_liquor import ThirstyLiquorLocationScraper
from app.store_scrapers.bottle_o import BottleOLocationScraper
from app.store_scrapers.black_bull import BlackBullLocationScraper
from app.store_scrapers.glengarry import GlengarryLocationScraper
from app.store_scrapers.generic import GenericLocationScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SCRAPER_CONFIGS = {
    "countdown": {
        "scraper_class": CountdownLocationScraper,
        "expected": 180,
    },
    "new_world": {
        "scraper_class": GenericLocationScraper,
        "url": "https://www.newworld.co.nz/store-finder",
        "expected": 144,
    },
    "super_liquor": {
        "scraper_class": SuperLiquorLocationScraper,
        "expected": 130,
    },
    "thirsty_liquor": {
        "scraper_class": ThirstyLiquorLocationScraper,
        "expected": 130,
    },
    "liquorland": {
        "scraper_class": LiquorlandLocationScraper,
        "expected": 100,
    },
    "liquor_centre": {
        "scraper_class": GenericLocationScraper,
        "url": "https://www.liquorcentre.co.nz/stores",
        "expected": 90,
    },
    "pak_n_save": {
        "scraper_class": GenericLocationScraper,
        "url": "https://www.paknsave.co.nz/store-finder",
        "expected": 57,
    },
    "bottle_o": {
        "scraper_class": BottleOLocationScraper,
        "expected": 40,
    },
    "black_bull": {
        "scraper_class": BlackBullLocationScraper,
        "expected": 60,
    },
    "glengarry": {
        "scraper_class": GlengarryLocationScraper,
        "expected": 5,
    },
}


async def scrape_chain(chain: str) -> List[Dict[str, Any]]:
    """Scrape stores for a single chain."""
    if chain not in SCRAPER_CONFIGS:
        logger.error(f"Unknown chain: {chain}")
        logger.info(f"Available chains: {', '.join(SCRAPER_CONFIGS.keys())}")
        return []

    config = SCRAPER_CONFIGS[chain]
    expected = config["expected"]

    logger.info(f"\n{'='*80}")
    logger.info(f"Scraping: {chain.upper().replace('_', ' ')}")
    logger.info(f"Expected stores: ~{expected}")
    logger.info(f"{'='*80}\n")

    try:
        # Initialize scraper
        if "url" in config:
            scraper = config["scraper_class"](chain, config["url"])
        else:
            scraper = config["scraper_class"]()

        async with scraper:
            stores = await scraper.fetch_stores()

        if stores:
            actual = len(stores)
            coverage = (actual / expected * 100) if expected > 0 else 0
            logger.info(f"\n✓ Scraped {actual} stores ({coverage:.1f}% of expected {expected})")

            if coverage < 80:
                logger.warning(f"⚠️  Coverage below 80% target ({coverage:.1f}%)")

            return stores
        else:
            logger.error(f"✗ No stores found for {chain}")
            return []

    except Exception as e:
        logger.error(f"✗ Failed to scrape {chain}: {e}", exc_info=True)
        return []


async def geocode_stores(stores: List[Dict[str, Any]], chain: str) -> List[Dict[str, Any]]:
    """Geocode stores that don't have coordinates."""
    if not stores:
        return stores

    logger.info(f"\nGeocoding addresses for {chain}...")

    geocoded_count = 0
    failed_count = 0
    already_geocoded = 0

    for store in stores:
        if store.get("lat") and store.get("lon"):
            already_geocoded += 1
            continue

        address = store.get("address")
        if not address:
            logger.warning(f"Store '{store.get('name')}' has no address")
            failed_count += 1
            continue

        logger.info(f"Geocoding: {store.get('name')}")

        coords = await geocode_with_retry(address, region="New Zealand")

        if coords:
            store["lat"], store["lon"] = coords
            geocoded_count += 1
            logger.info(f"  ✓ ({coords[0]:.4f}, {coords[1]:.4f})")
        else:
            logger.error(f"  ✗ Failed")
            failed_count += 1

        await asyncio.sleep(0.5)  # Rate limit

    logger.info(f"\nGeocoding: {already_geocoded} already had coords, "
                f"{geocoded_count} newly geocoded, {failed_count} failed")
    return stores


async def save_stores_to_db(stores: List[Dict[str, Any]], chain: str) -> int:
    """Save stores to database."""
    if not stores:
        return 0

    logger.info(f"\nSaving {len(stores)} stores to database...")

    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for store in stores:
            if not store.get("lat") or not store.get("lon"):
                logger.warning(f"Skipping (no coords): {store.get('name')}")
                skipped_count += 1
                continue

            stmt = insert(Store).values(
                chain=chain,
                name=store["name"],
                address=store.get("address"),
                region=store.get("region"),
                lat=store["lat"],
                lon=store["lon"],
                url=store.get("url"),
            )

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


async def run_single_chain(chain: str):
    """Scrape and save a single chain."""
    logger.info("="*80)
    logger.info(f"LIQUORFY STORE SCRAPER - {chain.upper()}")
    logger.info("="*80)

    # Scrape
    stores = await scrape_chain(chain)

    if not stores:
        logger.error(f"Failed to scrape {chain}")
        return

    # Geocode
    stores = await geocode_stores(stores, chain)

    # Save
    saved = await save_stores_to_db(stores, chain)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Chain: {chain}")
    logger.info(f"Stores scraped: {len(stores)}")
    logger.info(f"Stores saved to DB: {saved}")

    # Save backup
    output_file = Path(__file__).parent.parent / "data" / f"{chain}_stores.json"
    with open(output_file, "w") as f:
        json.dump(stores, f, indent=2)
    logger.info(f"Backup saved to: {output_file}")

    logger.info("\n✓ DONE!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape_single_chain.py <chain_name>")
        print(f"\nAvailable chains:")
        for chain in SCRAPER_CONFIGS.keys():
            print(f"  - {chain}")
        sys.exit(1)

    chain_name = sys.argv[1].lower()

    try:
        asyncio.run(run_single_chain(chain_name))
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
