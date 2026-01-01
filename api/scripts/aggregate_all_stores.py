"""
Aggregate all store data from JSON files into PostgreSQL database.
This script consolidates all store location data into a single source of truth.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.db.models import Store
from app.db.session import async_transaction
from app.services.geocoding import geocode_with_retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# All JSON files to aggregate
JSON_DATA_FILES = [
    {
        "file": "data/manual_stores.json",
        "type": "dict_of_chains",  # {"chain": [stores]}
        "needs_geocoding": True,
    },
    {
        "file": "data/scraped_stores_20260101_112851.json",
        "type": "dict_of_chains",
        "needs_geocoding": False,  # Already has coords
    },
]


async def load_json_file(file_path: Path, file_type: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load and parse a JSON data file."""
    logger.info(f"Loading: {file_path.name}")

    try:
        with open(file_path) as f:
            data = json.load(f)

        if file_type == "dict_of_chains":
            # Format: {"chain_name": [stores]}
            result = {}
            for chain, stores in data.items():
                if isinstance(stores, list):
                    result[chain] = stores
                else:
                    logger.warning(f"Unexpected format for {chain}: {type(stores)}")
            return result
        else:
            logger.error(f"Unknown file type: {file_type}")
            return {}

    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return {}


async def geocode_store(store: Dict[str, Any], chain: str) -> bool:
    """Geocode a store if it doesn't have coordinates."""
    if store.get("lat") and store.get("lon"):
        return True  # Already has coords

    address = store.get("address")
    if not address:
        logger.warning(f"No address for {store.get('name')}")
        return False

    logger.info(f"Geocoding: {store.get('name')} - {address[:60]}...")
    coords = await geocode_with_retry(address, region="New Zealand")

    if coords:
        store["lat"], store["lon"] = coords
        logger.info(f"  ✓ ({coords[0]:.4f}, {coords[1]:.4f})")
        return True
    else:
        logger.error(f"  ✗ Failed to geocode")
        return False


async def save_stores_to_db(stores: List[Dict[str, Any]], chain: str) -> tuple[int, int]:
    """Save stores to database. Returns (saved, skipped) counts."""
    if not stores:
        return 0, 0

    saved = 0
    skipped = 0

    async with async_transaction() as session:
        for store in stores:
            # Validate required fields
            name = store.get("name")
            lat = store.get("lat")
            lon = store.get("lon")

            if not name:
                logger.warning(f"Skipping (no name): {store}")
                skipped += 1
                continue

            if not lat or not lon:
                logger.warning(f"Skipping (no coords): {name}")
                skipped += 1
                continue

            # Extract other fields
            address = store.get("address")
            region = store.get("region") or store.get("city") or store.get("suburb")
            url = store.get("url") or store.get("link")

            # Upsert store
            stmt = insert(Store).values(
                chain=chain,
                name=name,
                address=address,
                region=region,
                lat=float(lat),
                lon=float(lon),
                url=url,
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
            saved += 1

    return saved, skipped


async def get_db_stats() -> Dict[str, int]:
    """Get current store counts from database."""
    async with async_transaction() as session:
        result = await session.execute(
            select(Store.chain, func.count()).group_by(Store.chain)
        )
        return dict(result.all())


async def aggregate_all_stores():
    """Main function to aggregate all store data."""
    logger.info("="*80)
    logger.info("AGGREGATE ALL STORE DATA INTO PostgreSQL")
    logger.info("="*80)

    # Get initial database state
    logger.info("\nInitial database state:")
    initial_stats = await get_db_stats()
    initial_total = sum(initial_stats.values())
    for chain, count in sorted(initial_stats.items()):
        logger.info(f"  {chain}: {count} stores")
    logger.info(f"  TOTAL: {initial_total} stores")

    # Process each JSON file
    all_chains_data: Dict[str, List[Dict[str, Any]]] = {}

    for config in JSON_DATA_FILES:
        file_path = Path(__file__).parent.parent / config["file"]

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        # Load file
        chains_data = await load_json_file(file_path, config["type"])

        # Merge with existing data
        for chain, stores in chains_data.items():
            if chain not in all_chains_data:
                all_chains_data[chain] = []
            all_chains_data[chain].extend(stores)

    # Process each chain
    logger.info(f"\n{'='*80}")
    logger.info("PROCESSING STORES BY CHAIN")
    logger.info(f"{'='*80}\n")

    total_saved = 0
    total_skipped = 0
    total_geocoded = 0

    for chain, stores in sorted(all_chains_data.items()):
        logger.info(f"\n{'='*60}")
        logger.info(f"Chain: {chain.upper().replace('_', ' ')}")
        logger.info(f"Stores to process: {len(stores)}")
        logger.info(f"{'='*60}")

        # Geocode if needed
        geocoded_count = 0
        for store in stores:
            if not store.get("lat") or not store.get("lon"):
                if await geocode_store(store, chain):
                    geocoded_count += 1
                await asyncio.sleep(0.5)  # Rate limit

        if geocoded_count > 0:
            logger.info(f"Geocoded {geocoded_count} stores")
            total_geocoded += geocoded_count

        # Save to database
        saved, skipped = await save_stores_to_db(stores, chain)
        total_saved += saved
        total_skipped += skipped

        logger.info(f"✓ Saved: {saved}, Skipped: {skipped}")

    # Get final database state
    logger.info(f"\n{'='*80}")
    logger.info("FINAL RESULTS")
    logger.info(f"{'='*80}")

    final_stats = await get_db_stats()
    final_total = sum(final_stats.values())

    logger.info("\nFinal database state:")
    for chain, count in sorted(final_stats.items()):
        initial = initial_stats.get(chain, 0)
        change = count - initial
        indicator = f"(+{change})" if change > 0 else ""
        logger.info(f"  {chain}: {count} stores {indicator}")
    logger.info(f"  TOTAL: {final_total} stores")

    logger.info(f"\nSummary:")
    logger.info(f"  Initial stores: {initial_total}")
    logger.info(f"  Final stores: {final_total}")
    logger.info(f"  Net change: +{final_total - initial_total}")
    logger.info(f"  Geocoded: {total_geocoded}")
    logger.info(f"  Saved: {total_saved}")
    logger.info(f"  Skipped: {total_skipped}")

    logger.info("\n✓ AGGREGATION COMPLETE!")


if __name__ == "__main__":
    try:
        asyncio.run(aggregate_all_stores())
    except KeyboardInterrupt:
        logger.info("\nInterrupted")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
