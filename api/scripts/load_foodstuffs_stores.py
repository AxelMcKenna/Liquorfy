"""
Load Foodstuffs chain stores (New World, Pak'nSave, Liquor Centre) from JSON files to database.
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
from app.services.geocoding import geocode_with_retry

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


async def load_and_geocode_chain(chain: str, config: Dict[str, Any]) -> int:
    """Load stores for a chain from JSON file, geocode, and save to database."""
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

    # Geocode and save
    saved_count = 0
    geocoded_count = 0
    already_geocoded = 0
    failed_count = 0

    async with async_transaction() as session:
        for i, store in enumerate(stores, 1):
            name = store.get("name")
            address = store.get("address")
            region = store.get("region")
            api_id = store.get("id")

            if not name or not address:
                logger.warning(f"Skipping store with missing name or address: {store}")
                continue

            # Check if we already have coordinates
            lat = store.get("lat")
            lon = store.get("lon")

            if not lat or not lon:
                # Need to geocode
                # Construct a search query
                search_query = f"{name}, {address}, New Zealand"
                logger.info(f"[{i}/{len(stores)}] Geocoding: {name} - {address}")

                coords = await geocode_with_retry(search_query, region="New Zealand")

                if coords:
                    lat, lon = coords
                    geocoded_count += 1
                    logger.info(f"  ✓ Geocoded to ({lat:.4f}, {lon:.4f})")
                else:
                    logger.error(f"  ✗ Failed to geocode {name}")
                    failed_count += 1
                    continue  # Skip stores we can't geocode

                # Rate limit
                await asyncio.sleep(0.5)
            else:
                already_geocoded += 1

            # Save to database
            stmt = insert(Store).values(
                chain=config["chain_key"],
                name=name,
                address=address,
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

    logger.info(f"\n✓ Summary for {chain}:")
    logger.info(f"  - Saved to DB: {saved_count}")
    logger.info(f"  - Already had coords: {already_geocoded}")
    logger.info(f"  - Newly geocoded: {geocoded_count}")
    logger.info(f"  - Failed to geocode: {failed_count}")

    return saved_count


async def main():
    """Load all Foodstuffs chain stores."""
    logger.info("="*80)
    logger.info("LOADING FOODSTUFFS CHAIN STORES")
    logger.info("="*80)

    total_saved = 0

    for chain, config in STORE_FILES.items():
        saved = await load_and_geocode_chain(chain, config)
        total_saved += saved

        # Wait between chains
        await asyncio.sleep(2)

    logger.info(f"\n{'='*80}")
    logger.info(f"ALL DONE - Total stores saved: {total_saved}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
