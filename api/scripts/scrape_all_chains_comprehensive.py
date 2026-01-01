"""
Comprehensive script to scrape ALL store locations for chains we have product scrapers for.
This will get EVERY store for each chain and compare with what we have in the database.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction
from app.services.geocoding import geocode_with_retry
from app.store_scrapers.super_liquor import SuperLiquorLocationScraper
from app.store_scrapers.liquorland import LiquorlandLocationScraper
from app.store_scrapers.generic import GenericLocationScraper
from app.store_scrapers.glengarry import GlengarryLocationScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# All chains we have product scrapers for (excluding Countdown per user request)
SCRAPER_CONFIGS = [
    {
        "chain": "super_liquor",
        "display_name": "Super Liquor",
        "scraper_class": SuperLiquorLocationScraper,
    },
    {
        "chain": "liquorland",
        "display_name": "Liquorland",
        "scraper_class": LiquorlandLocationScraper,
    },
    {
        "chain": "new_world",
        "display_name": "New World",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.newworld.co.nz/store-finder",
    },
    {
        "chain": "pak_n_save",
        "display_name": "PAK'nSAVE",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.paknsave.co.nz/store-finder",
    },
    {
        "chain": "bottle_o",
        "display_name": "Bottle O",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.thebottleo.co.nz/store-locator",
    },
    {
        "chain": "liquor_centre",
        "display_name": "Liquor Centre",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.liquorcentre.co.nz/stores",
    },
    {
        "chain": "glengarry",
        "display_name": "Glengarry",
        "scraper_class": GlengarryLocationScraper,
    },
    {
        "chain": "thirsty_liquor",
        "display_name": "Thirsty Liquor",
        "scraper_class": GenericLocationScraper,
        "url": "https://thirstyliquor.co.nz/pages/our-stores",
    },
    {
        "chain": "black_bull",
        "display_name": "Black Bull",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.blackbullliquor.co.nz/stores",
    },
    {
        "chain": "big_barrel",
        "display_name": "Big Barrel",
        "scraper_class": GenericLocationScraper,
        "url": "https://www.bigbarrel.co.nz/stores",
    },
]


async def scrape_chain_stores(config: Dict[str, Any]) -> Tuple[int, List[Dict[str, Any]]]:
    """Scrape stores for a single chain. Returns (expected_count, stores_list)."""
    chain = config["chain"]
    display_name = config.get("display_name", chain)

    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping stores for: {display_name}")
    logger.info(f"{'='*60}")

    try:
        # Initialize scraper
        if "url" in config:
            scraper = config["scraper_class"](chain, config["url"])
        else:
            scraper = config["scraper_class"]()

        async with scraper:
            stores = await scraper.fetch_stores()

        logger.info(f"✓ Found {len(stores)} stores for {display_name}")

        # Return the count and the stores
        return len(stores), stores

    except Exception as e:
        logger.error(f"✗ Failed to scrape {display_name}: {e}", exc_info=True)
        return 0, []


async def geocode_stores(stores: List[Dict[str, Any]], chain: str) -> List[Dict[str, Any]]:
    """Geocode stores that don't have coordinates."""
    need_geocoding = [s for s in stores if not (s.get("lat") and s.get("lon"))]

    if not need_geocoding:
        logger.info(f"All {len(stores)} stores already have coordinates")
        return stores

    logger.info(f"Geocoding {len(need_geocoding)} addresses for {chain}...")

    geocoded_count = 0
    failed_count = 0

    for store in need_geocoding:
        address = store.get("address")
        if not address:
            logger.warning(f"Store '{store.get('name')}' has no address to geocode")
            failed_count += 1
            continue

        coords = await geocode_with_retry(address, region="New Zealand")

        if coords:
            store["lat"], store["lon"] = coords
            geocoded_count += 1
            logger.info(f"  ✓ {store.get('name')}: ({coords[0]:.6f}, {coords[1]:.6f})")
        else:
            logger.error(f"  ✗ Failed: {store.get('name')}")
            failed_count += 1

    logger.info(f"Geocoding: {geocoded_count} success, {failed_count} failed")
    return stores


async def save_stores_to_db(stores: List[Dict[str, Any]], chain: str) -> int:
    """Save stores to database using upsert."""
    logger.info(f"Saving {len(stores)} stores for {chain}...")

    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for store in stores:
            # Skip stores without coordinates
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

    logger.info(f"✓ Saved {saved_count}, skipped {skipped_count}")
    return saved_count


async def get_db_store_count(chain: str) -> int:
    """Get current count of stores in database for a chain."""
    async with async_transaction() as session:
        result = await session.execute(
            select(func.count()).select_from(Store).where(Store.chain == chain)
        )
        return result.scalar()


async def main():
    """Main function."""
    logger.info("="*60)
    logger.info("COMPREHENSIVE STORE LOCATION SCRAPER")
    logger.info("Scraping ALL stores for chains with product scrapers")
    logger.info("="*60)

    results = []
    total_expected = 0
    total_saved = 0

    # Scrape each chain
    for config in SCRAPER_CONFIGS:
        chain = config["chain"]
        display_name = config.get("display_name", chain)

        # Get current DB count before scraping
        db_count_before = await get_db_store_count(chain)

        # Scrape stores
        expected_count, stores = await scrape_chain_stores(config)

        if not stores:
            logger.warning(f"No stores found for {display_name}")
            results.append({
                "chain": display_name,
                "expected": expected_count,
                "db_before": db_count_before,
                "scraped": 0,
                "saved": 0,
                "db_after": db_count_before
            })
            continue

        total_expected += expected_count

        # Geocode if needed
        stores = await geocode_stores(stores, chain)

        # Save to database
        saved = await save_stores_to_db(stores, chain)
        total_saved += saved

        # Get new DB count
        db_count_after = await get_db_store_count(chain)

        results.append({
            "chain": display_name,
            "expected": expected_count,
            "db_before": db_count_before,
            "scraped": len(stores),
            "saved": saved,
            "db_after": db_count_after
        })

        # Rate limiting
        await asyncio.sleep(2)

    # Print results table
    logger.info("\n" + "="*80)
    logger.info("RESULTS")
    logger.info("="*80)

    print("\n")
    print(f"{'Store Chain':<20} {'Expected':<10} {'We Have':<10} {'Coverage':<10}")
    print("-" * 80)

    for r in results:
        coverage = f"{(r['db_after']/r['expected']*100):.0f}%" if r['expected'] > 0 else "N/A"
        status = "✅" if r['db_after'] >= r['expected'] else "⚠️ "
        print(f"{status} {r['chain']:<18} {r['expected']:<10} {r['db_after']:<10} {coverage:<10}")

    print("-" * 80)
    print(f"{'TOTAL':<20} {total_expected:<10} {sum(r['db_after'] for r in results):<10}")
    print("\n")

    # Save detailed results
    output_file = Path(__file__).parent.parent / "data" / "store_scraping_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Detailed results saved to: {output_file}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
