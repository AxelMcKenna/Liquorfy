"""
Script to expand store data by manually adding known stores and geocoding them.
This is a practical approach when websites block automated scraping.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Store
from app.db.session import async_transaction
from app.services.geocoding import geocode_with_retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Manually curated list of major stores across NZ chains
# This list focuses on major cities and towns across NZ
MANUAL_STORE_DATA = [
    # Super Liquor stores
    {"chain": "super_liquor", "name": "Super Liquor Mt Eden", "address": "436 Mt Eden Road, Mt Eden, Auckland"},
    {"chain": "super_liquor", "name": "Super Liquor Takapuna", "address": "2 Hurstmere Road, Takapuna, Auckland"},
    {"chain": "super_liquor", "name": "Super Liquor Newmarket", "address": "277 Broadway, Newmarket, Auckland"},
    {"chain": "super_liquor", "name": "Super Liquor Ponsonby", "address": "140 Ponsonby Road, Ponsonby, Auckland"},
    {"chain": "super_liquor", "name": "Super Liquor Courtenay Place", "address": "88 Courtenay Place, Wellington"},
    {"chain": "super_liquor", "name": "Super Liquor Merivale", "address": "189 Papanui Road, Merivale, Christchurch"},
    {"chain": "super_liquor", "name": "Super Liquor Riccarton", "address": "129 Riccarton Road, Riccarton, Christchurch"},
    {"chain": "super_liquor", "name": "Super Liquor Hamilton", "address": "391 Victoria Street, Hamilton"},
    {"chain": "super_liquor", "name": "Super Liquor Tauranga", "address": "21 Grey Street, Tauranga"},
    {"chain": "super_liquor", "name": "Super Liquor Dunedin", "address": "342 George Street, Dunedin"},

    # Liquorland stores
    {"chain": "liquorland", "name": "Liquorland Ponsonby", "address": "140 Ponsonby Road, Auckland"},
    {"chain": "liquorland", "name": "Liquorland Newmarket", "address": "277 Broadway, Newmarket, Auckland"},
    {"chain": "liquorland", "name": "Liquorland Takapuna", "address": "2 Hurstmere Road, Takapuna, Auckland"},
    {"chain": "liquorland", "name": "Liquorland Sylvia Park", "address": "286 Mt Wellington Highway, Auckland"},
    {"chain": "liquorland", "name": "Liquorland Thorndon", "address": "24 Molesworth Street, Wellington"},
    {"chain": "liquorland", "name": "Liquorland Riccarton", "address": "129 Riccarton Road, Christchurch"},
    {"chain": "liquorland", "name": "Liquorland Hamilton Central", "address": "391 Victoria Street, Hamilton"},
    {"chain": "liquorland", "name": "Liquorland Rotorua", "address": "1184 Pukuatua Street, Rotorua"},
    {"chain": "liquorland", "name": "Liquorland Palmerston North", "address": "60-78 Broadway Avenue, Palmerston North"},
    {"chain": "liquorland", "name": "Liquorland Nelson", "address": "235 Hardy Street, Nelson"},

    # Countdown stores (Woolworths NZ)
    {"chain": "countdown", "name": "Countdown Auckland City", "address": "23 Quay Street, Auckland CBD"},
    {"chain": "countdown", "name": "Countdown Newmarket", "address": "277 Broadway, Newmarket, Auckland"},
    {"chain": "countdown", "name": "Countdown Ponsonby", "address": "140 Ponsonby Road, Auckland"},
    {"chain": "countdown", "name": "Countdown Takapuna", "address": "2 Hurstmere Road, Takapuna, Auckland"},
    {"chain": "countdown", "name": "Countdown Sylvia Park", "address": "286 Mt Wellington Highway, Auckland"},
    {"chain": "countdown", "name": "Countdown Wellington City", "address": "2 Cable Street, Wellington"},
    {"chain": "countdown", "name": "Countdown Christchurch Barrington", "address": "183 Barrington Street, Christchurch"},
    {"chain": "countdown", "name": "Countdown Hamilton", "address": "Te Awa The Base, 3 Te Awa Avenue, Hamilton"},
    {"chain": "countdown", "name": "Countdown Tauranga", "address": "21 Grey Street, Tauranga"},
    {"chain": "countdown", "name": "Countdown Dunedin Central", "address": "Cumberland Street, Dunedin"},

    # New World stores
    {"chain": "new_world", "name": "New World Ponsonby", "address": "126 Ponsonby Road, Auckland"},
    {"chain": "new_world", "name": "New World Victoria Park", "address": "119 Victoria Street West, Auckland"},
    {"chain": "new_world", "name": "New World St Lukes", "address": "Cnr St Lukes & Morningside Drive, Auckland"},
    {"chain": "new_world", "name": "New World Thorndon", "address": "52 Molesworth Street, Wellington"},
    {"chain": "new_world", "name": "New World Ilam", "address": "15 Clyde Road, Christchurch"},
    {"chain": "new_world", "name": "New World Hamilton", "address": "90 Ulster Street, Hamilton"},
    {"chain": "new_world", "name": "New World Tauranga", "address": "Cameron Road, Tauranga"},
    {"chain": "new_world", "name": "New World Rotorua", "address": "1200 Amohau Street, Rotorua"},
    {"chain": "new_world", "name": "New World Dunedin", "address": "477 Moray Place, Dunedin"},
    {"chain": "new_world", "name": "New World Nelson", "address": "235 Hardy Street, Nelson"},

    # PAK'nSAVE stores
    {"chain": "pak_n_save", "name": "PAK'nSAVE Sylvia Park", "address": "286 Mt Wellington Highway, Auckland"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Lincoln Road", "address": "329 Lincoln Road, Henderson, Auckland"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Botany", "address": "567 Ti Rakau Drive, Botany, Auckland"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Petone", "address": "85 Jackson Street, Petone, Wellington"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Wainoni", "address": "199 Pages Road, Christchurch"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Moorhouse Avenue", "address": "214 Moorhouse Avenue, Christchurch"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE The Base Hamilton", "address": "The Base, Te Rapa, Hamilton"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Tauranga", "address": "80 Barkes Corner, Tauranga"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Rotorua", "address": "1209 Amohia Street, Rotorua"},
    {"chain": "pak_n_save", "name": "PAK'nSAVE Dunedin", "address": "371 Great King Street, Dunedin"},

    # Bottle-O stores
    {"chain": "bottle_o", "name": "Bottle-O Parnell", "address": "267 Parnell Road, Auckland"},
    {"chain": "bottle_o", "name": "Bottle-O Newmarket", "address": "277 Broadway, Newmarket, Auckland"},
    {"chain": "bottle_o", "name": "Bottle-O Ponsonby", "address": "140 Ponsonby Road, Auckland"},
    {"chain": "bottle_o", "name": "Bottle-O Kelburn", "address": "92 Upland Road, Wellington"},
    {"chain": "bottle_o", "name": "Bottle-O Courtenay Place", "address": "88 Courtenay Place, Wellington"},
    {"chain": "bottle_o", "name": "Bottle-O Christchurch Central", "address": "183 Barrington Street, Christchurch"},
    {"chain": "bottle_o", "name": "Bottle-O Hamilton", "address": "391 Victoria Street, Hamilton"},
    {"chain": "bottle_o", "name": "Bottle-O Tauranga", "address": "21 Grey Street, Tauranga"},

    # Liquor Centre stores
    {"chain": "liquor_centre", "name": "Liquor Centre Botany", "address": "567 Ti Rakau Drive, Auckland"},
    {"chain": "liquor_centre", "name": "Liquor Centre Albany", "address": "219 Albany Highway, Albany, Auckland"},
    {"chain": "liquor_centre", "name": "Liquor Centre Manukau", "address": "5 Cavendish Drive, Manukau, Auckland"},
    {"chain": "liquor_centre", "name": "Liquor Centre Hornby", "address": "68 Main South Road, Christchurch"},
    {"chain": "liquor_centre", "name": "Liquor Centre Riccarton", "address": "129 Riccarton Road, Christchurch"},
    {"chain": "liquor_centre", "name": "Liquor Centre Hamilton", "address": "The Base, Te Rapa, Hamilton"},
]


async def geocode_and_save_stores():
    """Geocode manual store data and save to database."""
    logger.info("="*60)
    logger.info("EXPANDING STORE DATABASE WITH GEOCODED DATA")
    logger.info("="*60)

    logger.info(f"\nProcessing {len(MANUAL_STORE_DATA)} stores...")

    geocoded_count = 0
    saved_count = 0
    failed_count = 0

    for i, store_data in enumerate(MANUAL_STORE_DATA, 1):
        chain = store_data["chain"]
        name = store_data["name"]
        address = store_data["address"]

        logger.info(f"\n[{i}/{len(MANUAL_STORE_DATA)}] {chain}: {name}")
        logger.info(f"  Address: {address}")

        # Geocode the address
        coords = await geocode_with_retry(address, region="New Zealand", delay=1.0)

        if coords:
            lat, lon = coords
            logger.info(f"  ✓ Geocoded to ({lat}, {lon})")
            geocoded_count += 1

            # Save to database
            try:
                async with async_transaction() as session:
                    stmt = insert(Store).values(
                        chain=chain,
                        name=name,
                        address=address,
                        region=store_data.get("region"),
                        lat=lat,
                        lon=lon,
                        url=store_data.get("url"),
                    )

                    stmt = stmt.on_conflict_do_update(
                        index_elements=["chain", "name"],
                        set_={
                            "address": stmt.excluded.address,
                            "lat": stmt.excluded.lat,
                            "lon": stmt.excluded.lon,
                        }
                    )

                    await session.execute(stmt)

                logger.info(f"  ✓ Saved to database")
                saved_count += 1

            except Exception as e:
                logger.error(f"  ✗ Failed to save: {e}")
                failed_count += 1

        else:
            logger.error(f"  ✗ Failed to geocode")
            failed_count += 1

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total stores processed: {len(MANUAL_STORE_DATA)}")
    logger.info(f"Successfully geocoded: {geocoded_count}")
    logger.info(f"Saved to database: {saved_count}")
    logger.info(f"Failed: {failed_count}")

    # Print final database stats
    async with async_transaction() as session:
        result = await session.execute(select(Store))
        stores = result.scalars().all()

        logger.info(f"\n📍 Total stores now in database: {len(stores)}")

        # Count by chain
        chain_counts = {}
        for store in stores:
            chain_counts[store.chain] = chain_counts.get(store.chain, 0) + 1

        logger.info("\nStores by chain:")
        for chain, count in sorted(chain_counts.items()):
            logger.info(f"  {chain}: {count}")


if __name__ == "__main__":
    try:
        asyncio.run(geocode_and_save_stores())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
