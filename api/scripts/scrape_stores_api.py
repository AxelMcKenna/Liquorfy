"""
Script to scrape store locations using API endpoints where possible.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction
from app.services.geocoding import geocode_with_retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_super_liquor_stores() -> List[Dict[str, Any]]:
    """Fetch Super Liquor stores from their API."""
    logger.info("Fetching Super Liquor stores from API...")

    stores = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
        try:
            # Try to get store data from the API endpoint
            response = await client.post(
                "https://www.superliquor.co.nz/getstorelocatordetails",
                json={"country": "New Zealand", "region": "", "city": ""}
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Got response from API: {type(data)}")

                # Parse the response
                if isinstance(data, list):
                    for store_data in data:
                        store = parse_super_liquor_store(store_data)
                        if store:
                            stores.append(store)
                elif isinstance(data, dict) and "stores" in data:
                    for store_data in data["stores"]:
                        store = parse_super_liquor_store(store_data)
                        if store:
                            stores.append(store)

                logger.info(f"Found {len(stores)} Super Liquor stores")
            else:
                logger.error(f"API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to fetch Super Liquor stores: {e}", exc_info=True)

    return stores


def parse_super_liquor_store(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse a Super Liquor store from API response."""
    try:
        name = data.get("name") or data.get("storeName") or data.get("title")
        address = data.get("address") or data.get("fullAddress")

        if not name or not address:
            return None

        lat = data.get("lat") or data.get("latitude")
        lon = data.get("lng") or data.get("lon") or data.get("longitude")

        return {
            "chain": "super_liquor",
            "name": name,
            "address": address,
            "region": data.get("city") or data.get("region"),
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "url": data.get("url"),
        }
    except Exception as e:
        logger.warning(f"Failed to parse store: {e}")
        return None


async def fetch_bottle_o_stores() -> List[Dict[str, Any]]:
    """Fetch Bottle O stores."""
    logger.info("Fetching Bottle O stores from website...")

    stores = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get("https://www.thebottleo.co.nz/pages/find-a-store")

            if response.status_code == 200:
                html = response.text

                # Try to find store data in the HTML
                import re

                # Look for JSON data in script tags
                json_pattern = r'var\s+stores\s*=\s*(\[.*?\]);'
                match = re.search(json_pattern, html, re.DOTALL)

                if match:
                    try:
                        stores_data = json.loads(match.group(1))
                        for store_data in stores_data:
                            store = {
                                "chain": "bottle_o",
                                "name": store_data.get("name", ""),
                                "address": store_data.get("address", ""),
                                "region": store_data.get("city") or store_data.get("region"),
                                "lat": float(store_data["lat"]) if "lat" in store_data else None,
                                "lon": float(store_data.get("lng") or store_data.get("lon")) if ("lng" in store_data or "lon" in store_data) else None,
                                "url": store_data.get("url"),
                            }
                            if store["name"] and store["address"]:
                                stores.append(store)

                        logger.info(f"Found {len(stores)} Bottle O stores")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch Bottle O stores: {e}", exc_info=True)

    return stores


async def geocode_stores(stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Geocode stores that don't have coordinates."""
    logger.info(f"\nGeocoding stores without coordinates...")

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


async def save_stores_to_db(stores: List[Dict[str, Any]]) -> int:
    """Save stores to database."""
    logger.info(f"\nSaving {len(stores)} stores to database...")

    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for store in stores:
            # Skip stores without coordinates
            if not store.get("lat") or not store.get("lon"):
                logger.warning(f"Skipping store without coordinates: {store.get('name')}")
                skipped_count += 1
                continue

            # Upsert store
            stmt = insert(Store).values(
                chain=store["chain"],
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


async def main():
    """Main function."""
    logger.info("="*60)
    logger.info("LIQUORFY STORE SCRAPER (API-based)")
    logger.info("="*60)

    all_stores = []

    # Fetch Super Liquor stores
    super_liquor_stores = await fetch_super_liquor_stores()
    all_stores.extend(super_liquor_stores)

    # Rate limiting
    await asyncio.sleep(2)

    # Fetch Bottle O stores
    bottle_o_stores = await fetch_bottle_o_stores()
    all_stores.extend(bottle_o_stores)

    logger.info(f"\nTotal stores fetched: {len(all_stores)}")

    # Geocode any stores missing coordinates
    all_stores = await geocode_stores(all_stores)

    # Save to database
    saved = await save_stores_to_db(all_stores)

    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETE: Saved {saved} stores to database")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
