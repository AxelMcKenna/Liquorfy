"""CLI runner for store location scrapers.

Usage:
    # Run all chains
    python -m app.store_scrapers.runner

    # Run specific chains (comma-separated)
    python -m app.store_scrapers.runner liquorland,super_liquor

    # Or via env var
    LIQUORFY_STORE_CHAINS=liquorland,black_bull python -m app.store_scrapers.runner
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Dict, Type

from sqlalchemy import text

from app.db.session import get_async_session
from app.store_scrapers.base import StoreLocationScraper
from app.store_scrapers.liquorland import LiquorlandLocationScraper
from app.store_scrapers.super_liquor import SuperLiquorLocationScraper
from app.store_scrapers.thirsty_liquor import ThirstyLiquorLocationScraper
from app.store_scrapers.black_bull import BlackBullLocationScraper
from app.store_scrapers.glengarry import GlengarryLocationScraper
from app.store_scrapers.bottle_o import BottleOLocationScraper
from app.store_scrapers.countdown import CountdownLocationScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

STORE_CHAINS: Dict[str, Type[StoreLocationScraper]] = {
    "liquorland": LiquorlandLocationScraper,
    "super_liquor": SuperLiquorLocationScraper,
    "thirsty_liquor": ThirstyLiquorLocationScraper,
    "black_bull": BlackBullLocationScraper,
    "glengarry": GlengarryLocationScraper,
    "bottle_o": BottleOLocationScraper,
    "countdown": CountdownLocationScraper,
}


async def upsert_stores(chain: str, stores: list[dict]) -> tuple[int, int]:
    """Upsert stores into DB. Returns (upserted, skipped)."""
    upserted = 0
    skipped = 0

    async with get_async_session() as session:
        for store in stores:
            name = store.get("name", "").strip()
            if not name:
                skipped += 1
                continue

            await session.execute(
                text("""
                    INSERT INTO stores (id, chain, name, address, region, lat, lon, url)
                    VALUES (gen_random_uuid(), :chain, :name, :address, :region, :lat, :lon, :url)
                    ON CONFLICT (chain, name) DO UPDATE SET
                        address = COALESCE(EXCLUDED.address, stores.address),
                        region  = COALESCE(EXCLUDED.region, stores.region),
                        lat     = COALESCE(EXCLUDED.lat, stores.lat),
                        lon     = COALESCE(EXCLUDED.lon, stores.lon),
                        url     = COALESCE(EXCLUDED.url, stores.url)
                """),
                {
                    "chain": chain,
                    "name": name,
                    "address": store.get("address"),
                    "region": store.get("region"),
                    "lat": store.get("lat"),
                    "lon": store.get("lon"),
                    "url": store.get("url"),
                },
            )
            upserted += 1

        await session.commit()

    return upserted, skipped


async def run_chain(chain: str) -> None:
    """Run a single store scraper and upsert results."""
    scraper_cls = STORE_CHAINS.get(chain)
    if not scraper_cls:
        logger.error(f"Unknown chain: {chain}. Available: {', '.join(STORE_CHAINS)}")
        return

    logger.info(f"[{chain}] Starting store scrape...")
    try:
        async with scraper_cls() as scraper:
            stores = await scraper.fetch_stores()

        logger.info(f"[{chain}] Fetched {len(stores)} stores")

        if stores:
            upserted, skipped = await upsert_stores(chain, stores)
            logger.info(f"[{chain}] Upserted {upserted}, skipped {skipped}")
        else:
            logger.warning(f"[{chain}] No stores returned")

    except Exception:
        logger.exception(f"[{chain}] Store scrape failed")


async def main(chains: list[str] | None = None) -> None:
    """Run store scrapers for given chains (or all)."""
    if not chains:
        chains = list(STORE_CHAINS.keys())

    logger.info(f"Running store scrapers for: {', '.join(chains)}")

    for chain in chains:
        await run_chain(chain)
        await asyncio.sleep(2)  # Be respectful between chains

    logger.info("Store scraping complete.")


if __name__ == "__main__":
    # Accept chains from CLI arg or env var
    raw = None
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = os.environ.get("LIQUORFY_STORE_CHAINS")

    target_chains = [c.strip() for c in raw.split(",") if c.strip()] if raw else None
    asyncio.run(main(target_chains))
