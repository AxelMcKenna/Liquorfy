"""Geocode Super Liquor stores by city name only."""
import asyncio
import json
import logging
from pathlib import Path
from app.services.geocoding import geocode_with_retry

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STORES_FILE = "/Users/axelmckenna/Liquorfy/api/data/all_super_liquor_stores_scraped.json"
OUTPUT_FILE = "/Users/axelmckenna/Liquorfy/api/data/super_liquor_geocoded.json"


def extract_location_from_name(store_name: str) -> str:
    """Extract city/suburb name from store name.

    Examples:
        'Super Liquor Alexandra' -> 'Alexandra'
        'Super Liquor All Seasons' -> 'All Seasons'
    """
    # Remove 'Super Liquor' prefix
    location = store_name.replace("Super Liquor ", "").strip()
    return location


async def geocode_stores():
    """Geocode all stores by city name."""
    logger.info("=" * 60)
    logger.info("Geocoding Super Liquor Stores by City Name")
    logger.info("=" * 60)

    # Load stores
    with open(STORES_FILE, 'r') as f:
        stores = json.load(f)

    logger.info(f"Loaded {len(stores)} stores from file\n")

    geocoded_stores = []
    success_count = 0
    fail_count = 0

    for i, store in enumerate(stores, 1):
        name = store.get('name', '').strip()
        location = extract_location_from_name(name)

        logger.info(f"[{i}/{len(stores)}] {name}")
        logger.info(f"  Location: {location}")

        # Try to geocode - pass just the city name, function will add "New Zealand"
        coords = await geocode_with_retry(location, max_retries=2)

        if coords:
            # coords is a tuple (lat, lon)
            store['latitude'] = coords[0]
            store['longitude'] = coords[1]
            logger.info(f"  ✅ Success: ({coords[0]}, {coords[1]})")
            success_count += 1
        else:
            logger.info(f"  ❌ Failed")
            fail_count += 1

        geocoded_stores.append(store)

        # Rate limiting - be respectful to Nominatim
        await asyncio.sleep(1.5)

    # Save results
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Results: {success_count} succeeded, {fail_count} failed")
    logger.info(f"Saving to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geocoded_stores, f, indent=2)

    logger.info(f"✅ Done! Geocoded {success_count}/{len(stores)} stores")


if __name__ == "__main__":
    asyncio.run(geocode_stores())
