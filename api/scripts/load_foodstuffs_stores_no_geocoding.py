"""
Load Foodstuffs chain stores (New World, Pak'nSave, Liquor Centre) WITHOUT geocoding.

NOTE: These stores only have city names as addresses, not full street addresses.
Since we use API-based scrapers that work with store IDs (not coordinates),
we're loading them with placeholder coordinates (0, 0) for now.

This allows product price scraping to work while we decide on a strategy
for getting proper addresses later.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


STORE_FILES = {
    "new_world": {
        "file": "app/data/newworld_stores.json",
        "chain_key": "new_world",
    },
    "paknsave": {
        "file": "app/data/paknsave_stores.json",
        "chain_key": "paknsave",
    },
    "liquor_centre": {
        "file": "app/data/liquor_centre_stores.json",
        "chain_key": "liquor_centre",
    },
}


async def load_chain_stores(chain: str, config: Dict[str, Any]) -> int:
    """Load stores for a chain from JSON file without geocoding."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Loading {chain.upper().replace('_', ' ')} stores")
    logger.info(f"{'='*80}")

    # Load JSON file
    file_path = Path(__file__).parent.parent / config["file"]
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    with open(file_path, 'r') as f:
        stores = json.load(f)

    logger.info(f"Loaded {len(stores)} stores from {file_path}")

    # Save to database WITHOUT geocoding
    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for store in stores:
            name = store.get("name")
            address = store.get("address")  # Just city name
            region = store.get("region")
            api_id = store.get("id")

            if not name or not api_id:
                logger.warning(f"Skipping store with missing name or ID: {store}")
                skipped_count += 1
                continue

            # Use placeholder coordinates (0, 0) since we don't have real addresses
            # This is acceptable because we use API-based scraping with store IDs
            lat = 0.0
            lon = 0.0

            # Save to database
            stmt = insert(Store).values(
                chain=config["chain_key"],
                name=name,
                address=address or "Address not available",
                region=region,
                lat=lat,
                lon=lon,
                api_id=api_id,
            )

            # On conflict, update the record
            stmt = stmt.on_conflict_do_update(
                index_elements=["chain", "api_id"],
                set_={
                    "name": stmt.excluded.name,
                    "address": stmt.excluded.address,
                    "region": stmt.excluded.region,
                    "lat": stmt.excluded.lat,
                    "lon": stmt.excluded.lon,
                }
            )

            await session.execute(stmt)
            saved_count += 1

    logger.info(f"✓ Saved {saved_count} stores to database")
    logger.info(f"  Skipped {skipped_count} stores (missing data)")
    logger.info(f"  Note: Using placeholder coordinates (0, 0) - API-based scraper uses store IDs")

    return saved_count


async def main():
    """Load all Foodstuffs chain stores."""
    logger.info("="*80)
    logger.info("LOADING FOODSTUFFS CHAIN STORES (WITHOUT GEOCODING)")
    logger.info("="*80)
    logger.info("")
    logger.info("NOTE: These chains use API-based scraping with store IDs.")
    logger.info("Exact coordinates are not required for product price scraping.")
    logger.info("Stores will have placeholder coordinates (0, 0).")
    logger.info("")

    total_saved = 0

    for chain, config in STORE_FILES.items():
        saved = await load_chain_stores(chain, config)
        total_saved += saved
        await asyncio.sleep(1)

    logger.info(f"\n{'='*80}")
    logger.info(f"COMPLETE - Total stores saved: {total_saved}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
