"""
Comprehensive store location scraper for all NZ liquor chains.
Runs scrapers in order of ROI (largest impact first) to achieve 95% coverage.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

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


# Scraper configurations in order of ROI (largest impact first)
SCRAPER_CONFIGS = [
    {
        "chain": "countdown",
        "expected_stores": 180,
        "scraper_class": CountdownLocationScraper,
        "priority": 1,
        "notes": "Largest supermarket liquor chain, API available"
    },
    {
        "chain": "new_world",
        "expected_stores": 144,
        "scraper_class": GenericLocationScraper,
        "url": "https://www.newworld.co.nz/store-finder",
        "priority": 2,
        "notes": "Foodstuffs brand, likely has API"
    },
    {
        "chain": "super_liquor",
        "expected_stores": 130,
        "scraper_class": SuperLiquorLocationScraper,
        "priority": 3,
        "notes": "Largest dedicated liquor chain (already scraped - 131 stores)"
    },
    {
        "chain": "thirsty_liquor",
        "expected_stores": 130,
        "scraper_class": ThirstyLiquorLocationScraper,
        "priority": 4,
        "notes": "Large chain, Shopify-based"
    },
    {
        "chain": "liquorland",
        "expected_stores": 100,
        "scraper_class": LiquorlandLocationScraper,
        "priority": 5,
        "notes": "Foodstuffs owned, Vue.js site"
    },
    {
        "chain": "liquor_centre",
        "expected_stores": 90,
        "scraper_class": GenericLocationScraper,
        "url": "https://www.liquorcentre.co.nz/stores",
        "priority": 6,
        "notes": "Store-specific subdomains, 90+ stores"
    },
    {
        "chain": "pak_n_save",
        "expected_stores": 57,
        "scraper_class": GenericLocationScraper,
        "url": "https://www.paknsave.co.nz/store-finder",
        "priority": 7,
        "notes": "Foodstuffs brand, likely has API"
    },
    {
        "chain": "bottle_o",
        "expected_stores": 40,
        "scraper_class": BottleOLocationScraper,
        "priority": 8,
        "notes": "Lion NZ owned, ~40 stores"
    },
    {
        "chain": "black_bull",
        "expected_stores": 60,
        "scraper_class": BlackBullLocationScraper,
        "priority": 9,
        "notes": "Franchise model, 60+ stores but only ~3 have online ordering"
    },
    {
        "chain": "glengarry",
        "expected_stores": 5,
        "scraper_class": GlengarryLocationScraper,
        "priority": 10,
        "notes": "Specialty retailer, 3-5 flagship stores"
    },
]


async def scrape_chain_stores(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape stores for a single chain."""
    chain = config["chain"]
    expected = config["expected_stores"]
    priority = config["priority"]

    logger.info(f"\n{'='*80}")
    logger.info(f"[{priority}/10] Scraping: {chain.upper().replace('_', ' ')}")
    logger.info(f"Expected stores: ~{expected}")
    logger.info(f"Notes: {config.get('notes', '')}")
    logger.info(f"{'='*80}")

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
            logger.info(f"✓ Scraped {actual} stores ({coverage:.1f}% of expected {expected})")

            if coverage < 90:
                logger.warning(f"⚠️  Coverage below 90% target ({coverage:.1f}%)")

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
        # Skip if already has coordinates
        if store.get("lat") and store.get("lon"):
            already_geocoded += 1
            continue

        # Need to geocode
        address = store.get("address")
        if not address:
            logger.warning(f"Store '{store.get('name')}' has no address to geocode")
            failed_count += 1
            continue

        logger.info(f"Geocoding: {store.get('name')} - {address[:60]}...")

        coords = await geocode_with_retry(address, region="New Zealand")

        if coords:
            store["lat"], store["lon"] = coords
            geocoded_count += 1
            logger.info(f"  ✓ Geocoded to ({coords[0]:.4f}, {coords[1]:.4f})")
        else:
            logger.error(f"  ✗ Failed to geocode")
            failed_count += 1

        # Rate limit geocoding
        await asyncio.sleep(0.5)

    logger.info(f"Geocoding complete: {already_geocoded} already had coords, "
                f"{geocoded_count} newly geocoded, {failed_count} failed")
    return stores


async def save_stores_to_db(stores: List[Dict[str, Any]], chain: str) -> int:
    """Save stores to database."""
    if not stores:
        return 0

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


async def save_backup(all_stores: Dict[str, List[Dict[str, Any]]]):
    """Save raw scraped data to backup file."""
    output_file = Path(__file__).parent.parent / "data" / f"scraped_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, "w") as f:
        json.dump(all_stores, f, indent=2)

    logger.info(f"\nBackup saved to: {output_file}")


async def print_summary(all_stores: Dict[str, List[Dict[str, Any]]]):
    """Print detailed summary of scraping results."""
    logger.info("\n" + "="*80)
    logger.info("SCRAPING COMPLETE - SUMMARY")
    logger.info("="*80)

    total_scraped = sum(len(stores) for stores in all_stores.values())
    total_expected = sum(c["expected_stores"] for c in SCRAPER_CONFIGS)

    logger.info(f"\nChains scraped: {len(all_stores)}/{len(SCRAPER_CONFIGS)}")
    logger.info(f"Total stores scraped: {total_scraped}")
    logger.info(f"Expected stores: {total_expected}")
    logger.info(f"Overall coverage: {(total_scraped / total_expected * 100):.1f}%")

    logger.info("\nPer-chain breakdown:")
    logger.info(f"{'Chain':<20} {'Scraped':<10} {'Expected':<10} {'Coverage':<10}")
    logger.info("-" * 80)

    for config in SCRAPER_CONFIGS:
        chain = config["chain"]
        expected = config["expected_stores"]
        stores = all_stores.get(chain, [])
        actual = len(stores)
        coverage = (actual / expected * 100) if expected > 0 else 0

        status = "✓" if coverage >= 90 else "⚠️"
        logger.info(f"{status} {chain:<18} {actual:<10} {expected:<10} {coverage:>6.1f}%")

    # Database stats
    async with async_transaction() as session:
        result = await session.execute(select(func.count()).select_from(Store))
        total_in_db = result.scalar()

        result = await session.execute(
            select(Store.chain, func.count()).group_by(Store.chain).order_by(func.count().desc())
        )

        logger.info("\n" + "="*80)
        logger.info("DATABASE SUMMARY")
        logger.info("="*80)
        logger.info(f"Total stores in database: {total_in_db}")
        logger.info("\nStores by chain:")

        for chain, count in result:
            logger.info(f"  {chain:<20} {count} stores")


async def run_all_scrapers():
    """Main function to scrape all store locations."""
    logger.info("="*80)
    logger.info("LIQUORFY COMPREHENSIVE STORE LOCATION SCRAPER")
    logger.info("Target: 95% coverage across all chains")
    logger.info("="*80)

    all_stores = {}
    total_saved = 0

    # Scrape each chain in priority order
    for config in SCRAPER_CONFIGS:
        chain = config["chain"]

        # Scrape stores
        stores = await scrape_chain_stores(config)

        if not stores:
            logger.warning(f"No stores found for {chain}, skipping...")
            continue

        # Geocode addresses if needed
        stores = await geocode_stores(stores, chain)

        # Save to database
        saved = await save_stores_to_db(stores, chain)
        total_saved += saved

        all_stores[chain] = stores

        # Rate limiting between chains
        logger.info("\nWaiting 3 seconds before next chain...")
        await asyncio.sleep(3)

    # Save backup
    await save_backup(all_stores)

    # Print summary
    await print_summary(all_stores)

    logger.info("\n" + "="*80)
    logger.info("✓ ALL DONE!")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_scrapers())
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
