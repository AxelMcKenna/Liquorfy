"""
Import Countdown/Woolworths stores from scraped JSON into database.
"""
import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select
from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_stores():
    """Import Countdown stores from JSON file."""

    # Load scraped stores
    json_path = Path(__file__).parent.parent / "app" / "data" / "countdown_stores.json"

    if not json_path.exists():
        logger.error(f"Store data not found at {json_path}")
        return

    with open(json_path) as f:
        stores_data = json.load(f)

    logger.info(f"Loaded {len(stores_data)} stores from JSON")

    async with async_transaction() as session:
        # Check existing stores
        result = await session.execute(
            select(Store).where(Store.chain == "countdown")
        )
        existing_stores = {s.api_id: s for s in result.scalars().all()}
        logger.info(f"Found {len(existing_stores)} existing Countdown stores in DB")

        created = 0
        updated = 0

        for store_data in stores_data:
            store_id = store_data.get("id")
            name = store_data.get("name", "")
            suburb = store_data.get("suburb", "")
            postcode = store_data.get("postcode", "")
            state = store_data.get("state", "")

            # Build display name and address
            display_name = name.replace(" Woolworths", "").replace(" Countdown", "")

            # Use suburb + postcode as address
            address = f"{suburb}, {state} {postcode}".strip()

            # Use placeholder coordinates (can geocode later if needed)
            # For now, just use 0,0 since products aren't location-specific
            lat = 0.0
            lon = 0.0

            if store_id in existing_stores:
                # Update existing store
                store = existing_stores[store_id]
                store.name = display_name
                store.address = address
                store.lat = lat
                store.lon = lon
                updated += 1
            else:
                # Create new store
                store = Store(
                    chain="countdown",
                    api_id=store_id,
                    name=display_name,
                    address=address,
                    lat=lat,
                    lon=lon,
                )
                session.add(store)
                created += 1

        logger.info(f"✓ Created {created} stores, updated {updated} stores")


if __name__ == "__main__":
    asyncio.run(import_stores())
