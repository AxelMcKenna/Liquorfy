"""Bulk geocode all stores using existing data files and efficient batching."""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting settings for Nominatim
GEOCODE_DELAY = 1.1  # Seconds between requests (max 1 req/sec for Nominatim)
MAX_RETRIES = 2


async def geocode_address(address: str, client: httpx.AsyncClient, retry=0) -> tuple:
    """Geocode an address using Nominatim."""
    try:
        await asyncio.sleep(GEOCODE_DELAY)  # Rate limiting

        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": address,
                "format": "json",
                "limit": 1,
                "countrycodes": "nz"
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])

    except Exception as e:
        if retry < MAX_RETRIES:
            await asyncio.sleep(2)
            return await geocode_address(address, client, retry + 1)
        logger.error(f"Geocoding failed for '{address}': {e}")

    return None, None


async def load_and_geocode_paknsave():
    """Load PAK'nSAVE stores and geocode them."""
    logger.info("Processing PAK'nSAVE stores...")

    file_path = Path(__file__).parent.parent / "app" / "data" / "paknsave_stores.json"
    with open(file_path) as f:
        stores_data = json.load(f)

    stores = []
    headers = {"User-Agent": "Liquorfy/1.0 (Store Locator; +https://liquorfy.co.nz)"}

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for i, store_data in enumerate(stores_data, 1):
            name = f"PAK'nSAVE {store_data['name']}"
            address = store_data.get('address', store_data['name'])

            logger.info(f"[{i}/{len(stores_data)}] Geocoding {name}...")

            lat, lon = await geocode_address(f"{address}, New Zealand", client)

            if lat and lon:
                stores.append({
                    "chain": "paknsave",
                    "name": name,
                    "address": address,
                    "region": None,
                    "lat": lat,
                    "lon": lon,
                })
                logger.info(f"  ✓ ({lat:.4f}, {lon:.4f})")
            else:
                logger.warning(f"  ✗ Failed to geocode")

    logger.info(f"Successfully geocoded {len(stores)}/{len(stores_data)} PAK'nSAVE stores\n")
    return stores


async def load_and_geocode_newworld():
    """Load New World stores and geocode them."""
    logger.info("Processing New World stores...")

    file_path = Path(__file__).parent.parent / "app" / "data" / "newworld_stores.json"
    with open(file_path) as f:
        stores_data = json.load(f)

    stores = []
    headers = {"User-Agent": "Liquorfy/1.0 (Store Locator; +https://liquorfy.co.nz)"}

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for i, store_data in enumerate(stores_data, 1):
            name = store_data['name']
            # Extract location from name (e.g., "New World Albany" -> "Albany, New Zealand")
            location = name.replace("New World ", "")
            address = store_data.get('address', location)

            logger.info(f"[{i}/{len(stores_data)}] Geocoding {name}...")

            lat, lon = await geocode_address(f"{address}, New Zealand", client)

            if lat and lon:
                stores.append({
                    "chain": "new_world",
                    "name": name,
                    "address": address,
                    "region": store_data.get('region'),
                    "lat": lat,
                    "lon": lon,
                })
                logger.info(f"  ✓ ({lat:.4f}, {lon:.4f})")
            else:
                logger.warning(f"  ✗ Failed to geocode")

    logger.info(f"Successfully geocoded {len(stores)}/{len(stores_data)} New World stores\n")
    return stores


async def save_stores_to_db(stores: List[Dict[str, Any]]) -> int:
    """Save stores to database."""
    logger.info(f"Saving {len(stores)} stores to database...")

    saved_count = 0
    async with async_transaction() as session:
        for store in stores:
            if not store.get("lat") or not store.get("lon"):
                continue

            stmt = insert(Store).values(
                chain=store["chain"],
                name=store["name"],
                address=store.get("address"),
                region=store.get("region"),
                lat=store["lat"],
                lon=store["lon"],
            ).on_conflict_do_update(
                index_elements=["chain", "name"],
                set_={
                    "address": store.get("address"),
                    "region": store.get("region"),
                    "lat": store["lat"],
                    "lon": store["lon"],
                }
            )

            await session.execute(stmt)
            saved_count += 1

    logger.info(f"✓ Saved {saved_count} stores")
    return saved_count


async def print_summary():
    """Print database summary."""
    async with async_transaction() as session:
        result = await session.execute(select(func.count()).select_from(Store))
        total = result.scalar()

        result = await session.execute(
            select(Store.chain, func.count(Store.id))
            .group_by(Store.chain)
            .order_by(func.count(Store.id).desc())
        )
        chains = result.all()

        print("\n" + "="*60)
        print("STORE DATABASE SUMMARY")
        print("="*60)
        print(f"\nTotal: {total} stores\n")
        print("-"*60)
        print(f"{'Chain':<20} {'Stores':>8}")
        print("-"*60)
        for chain, count in chains:
            print(f"{chain:<20} {count:>8}")
        print("-"*60)
        print(f"{'TOTAL':<20} {total:>8}")
        print("="*60 + "\n")


async def main():
    """Main function."""
    print("="*60)
    print("BULK STORE GEOCODER")
    print("="*60)
    print(f"\nRate limit: 1 request per {GEOCODE_DELAY}s")
    print("This will take approximately:")
    print("  - PAK'nSAVE (57 stores): ~1 minute")
    print("  - New World (144 stores): ~3 minutes")
    print("  - Total: ~4-5 minutes\n")
    print("="*60 + "\n")

    all_stores = []

    # Geocode PAK'nSAVE stores
    paknsave_stores = await load_and_geocode_paknsave()
    all_stores.extend(paknsave_stores)

    # Geocode New World stores
    newworld_stores = await load_and_geocode_newworld()
    all_stores.extend(newworld_stores)

    # Save to database
    saved = await save_stores_to_db(all_stores)

    # Print summary
    await print_summary()

    logger.info(f"Complete! Geocoded and saved {saved} stores with precise coordinates.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
