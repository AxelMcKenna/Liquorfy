"""
Load Liquor Centre stores from store slugs WITHOUT geocoding.

NOTE: Liquor Centre uses API-based scraping with store slugs as identifiers.
We're loading them with placeholder coordinates (0, 0) similar to other API-based chains.
The slug can be used as the api_id for product price scraping.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def slug_to_name(slug: str) -> str:
    """Convert a slug to a human-readable store name."""
    # Replace hyphens with spaces and title case
    name = slug.replace('-', ' ').title()

    # Special handling for common patterns
    name = name.replace('Lw ', 'LW ')
    name = name.replace('Vjs', 'VJs')
    name = name.replace('Gs ', 'GS ')
    name = name.replace('Pt ', 'Point ')

    # Add "Liquor Centre" prefix if not already descriptive
    if not any(word in name.lower() for word in ['liquor', 'cellars', 'drinkz', 'inn', 'hotel', 'tavern', 'brewery']):
        name = f"Liquor Centre {name}"

    return name


async def load_liquor_centre_stores() -> int:
    """Load Liquor Centre stores from slugs file."""
    logger.info("="*80)
    logger.info("LOADING LIQUOR CENTRE STORES")
    logger.info("="*80)

    # Load JSON file
    file_path = Path(__file__).parent.parent / "app/data/liquor_centre_stores.json"
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    with open(file_path, 'r') as f:
        slugs = json.load(f)

    logger.info(f"Loaded {len(slugs)} store slugs from {file_path}")
    logger.info("")
    logger.info("NOTE: Using placeholder coordinates (0, 0) - API-based scraper uses store slugs")
    logger.info("")

    # Save to database WITHOUT geocoding
    saved_count = 0
    skipped_count = 0

    async with async_transaction() as session:
        for slug in slugs:
            if not slug or not isinstance(slug, str):
                logger.warning(f"Skipping invalid slug: {slug}")
                skipped_count += 1
                continue

            # Generate name from slug
            name = slug_to_name(slug)

            # Use placeholder coordinates (0, 0) since we don't have addresses
            # This is acceptable because we use API-based scraping with store slugs
            lat = 0.0
            lon = 0.0

            logger.info(f"Loading: {slug} -> {name}")

            # Save to database
            stmt = insert(Store).values(
                chain="liquor_centre",
                name=name,
                address="Address not available",
                region=None,
                lat=lat,
                lon=lon,
                api_id=slug,  # Use slug as API identifier
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

    logger.info("")
    logger.info(f"✓ Saved {saved_count} stores to database")
    logger.info(f"  Skipped {skipped_count} stores (invalid data)")
    logger.info(f"  Note: Using placeholder coordinates (0, 0) - API-based scraper uses store slugs")

    return saved_count


async def main():
    """Load Liquor Centre stores."""
    logger.info("="*80)
    logger.info("LIQUOR CENTRE STORE LOADER")
    logger.info("="*80)
    logger.info("")

    total_saved = await load_liquor_centre_stores()

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
