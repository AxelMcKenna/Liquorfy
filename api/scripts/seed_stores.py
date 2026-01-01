"""Seed stores data into the database."""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from app.db.models import Store
from app.db.session import async_transaction


async def seed_stores():
    """Load stores from JSON and insert into database."""
    # Load stores data
    data_file = Path(__file__).parent.parent / "data" / "stores_seed.json"

    with open(data_file, "r") as f:
        stores_data = json.load(f)

    print(f"Loading {len(stores_data)} stores...")

    async with async_transaction() as session:
        # Check if stores already exist
        existing_count = await session.execute(select(func.count()).select_from(Store))
        count = existing_count.scalar()

        if count > 0:
            print(f"Database already has {count} stores. Skipping seed.")
            print("To re-seed, truncate the stores table first.")
            return

        # Insert stores
        for store_data in stores_data:
            store = Store(
                name=store_data["name"],
                chain=store_data["chain"],
                lat=store_data["lat"],
                lon=store_data["lon"],
                address=store_data.get("address"),
                region=store_data.get("region"),
                url=store_data.get("url"),
            )
            session.add(store)

        print(f"Successfully seeded {len(stores_data)} stores!")


if __name__ == "__main__":
    asyncio.run(seed_stores())
