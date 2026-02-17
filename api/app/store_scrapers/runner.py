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

CHAIN_DISPLAY_NAMES: Dict[str, str] = {
    "liquorland": "Liquorland",
    "super_liquor": "Super Liquor",
    "thirsty_liquor": "Thirsty Liquor",
    "black_bull": "Black Bull",
    "glengarry": "Glengarry",
    "bottle_o": "Bottle-O",
    "countdown": "Countdown",
    "new_world": "New World",
    "paknsave": "PAK'nSAVE",
    "liquor_centre": "Liquor Centre",
    "big_barrel": "Big Barrel",
}


def _pick_str(store: dict, *keys: str) -> str | None:
    """Return first non-empty string-like value from provided keys."""
    for key in keys:
        value = store.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if value:
                return value
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _pick_float(store: dict, *keys: str) -> float | None:
    """Return first value parseable as float from provided keys."""
    for key in keys:
        value = store.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


async def upsert_stores(chain: str, stores: list[dict]) -> tuple[int, int]:
    """Upsert stores into DB. Returns (upserted, skipped)."""
    upserted = 0
    skipped = 0

    async with get_async_session() as session:
        for store in stores:
            name = _pick_str(store, "name", "Name", "label", "title", "storeName", "store_name")
            if not name:
                skipped += 1
                continue

            # Normalize ALL-CAPS names (e.g. Bottle-O feeds "ASHHURST") to title case
            if name == name.upper() and not name.isnumeric():
                name = name.title()

            # Prepend chain display name if not already present (e.g. "Ashhurst" → "Bottle-O Ashhurst")
            display = CHAIN_DISPLAY_NAMES.get(chain, "")
            if display and not name.lower().startswith(display.lower()):
                name = f"{display} {name}"

            address = _pick_str(store, "address", "Address", "FullAddress")
            if not address:
                address_parts = [
                    _pick_str(store, "Address", "address"),
                    _pick_str(store, "City", "city"),
                    _pick_str(store, "State", "state", "region"),
                    _pick_str(store, "ZipPostalCode", "postcode"),
                ]
                address = ", ".join([part for part in address_parts if part]) or None

            region = _pick_str(store, "region", "Region", "State", "state", "AreaName", "City", "city")
            lat = _pick_float(store, "lat", "latitude", "Latitude")
            lon = _pick_float(store, "lon", "lng", "longitude", "Longitude")
            url = _pick_str(store, "url", "StoreLocationUrl", "StoreDetailsUrl", "GoogleMapLocation")

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
                    "address": address,
                    "region": region,
                    "lat": lat,
                    "lon": lon,
                    "url": url,
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
