"""Run just Bottle O scraper."""
import asyncio
import logging
from sqlalchemy import select
from app.store_scrapers.bottle_o import BottleOLocationScraper
from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run Bottle O scraper."""

    async with BottleOLocationScraper() as scraper:
        stores_data = await scraper.fetch_stores()

        logger.info(f"Scraped {len(stores_data)} stores")

        # Print first few
        for i, store in enumerate(stores_data[:5]):
            print(f"\nStore {i+1}:")
            print(f"  Name: {store['name']}")
            print(f"  Address: {store.get('address', 'N/A')}")
            print(f"  URL: {store.get('url', 'N/A')}")

        if not stores_data:
            return

        # Save to DB
        async with async_transaction() as session:
            result = await session.execute(
                select(Store).where(Store.chain == "bottle_o")
            )
            existing = {s.name: s for s in result.scalars().all()}

            created = 0
            updated = 0

            # Deduplicate by name too (some stores have same name, different URLs)
            seen_names = set(existing.keys())

            for data in stores_data:
                name = data['name']

                # Skip duplicates
                if name in seen_names:
                    continue

                seen_names.add(name)

                if name in existing:
                    store = existing[name]
                    store.address = data.get('address')
                    store.url = data.get('url')
                    store.lat = data.get('lat') or 0.0
                    store.lon = data.get('lon') or 0.0
                    updated += 1
                else:
                    url = data.get('url')
                    if url and not url.startswith('http'):
                        url = f"https://shop.thebottleo.co.nz{url}"

                    store = Store(
                        chain="bottle_o",
                        name=name,
                        address=data.get('address'),
                        lat=data.get('lat') or 0.0,
                        lon=data.get('lon') or 0.0,
                        url=url,
                    )
                    session.add(store)
                    created += 1

            logger.info(f"Created {created}, updated {updated}, skipped {len(stores_data) - created - updated} duplicates")


if __name__ == "__main__":
    asyncio.run(main())
