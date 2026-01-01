"""Thirsty Liquor store location scraper."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class ThirstyLiquorLocationScraper(StoreLocationScraper):
    """Scraper for Thirsty Liquor store locations."""

    chain = "thirsty_liquor"
    store_locator_url = "https://thirstyliquor.co.nz"

    def __init__(self):
        # Thirsty Liquor needs browser for JS-rendered content
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Thirsty Liquor store locations from window.storeData."""
        logger.info(f"Fetching stores for {self.chain}")

        try:
            if not self.context:
                logger.error("Browser context not available")
                return []

            # Navigate to page
            page = await self.context.new_page()
            try:
                await page.goto(self.store_locator_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)  # Give JS time to load

                # Extract store data from window.storeData
                store_data = await page.evaluate("() => window.storeData")

                if not store_data:
                    logger.warning("window.storeData not found or empty")
                    return []

                logger.info(f"Found window.storeData with {len(store_data) if isinstance(store_data, (list, dict)) else 0} items")

                stores = self._parse_store_data(store_data)
                logger.info(f"Successfully extracted {len(stores)} Thirsty Liquor stores")
                return stores

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Failed to fetch Thirsty Liquor stores: {e}", exc_info=True)
            return []

    def _parse_store_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from window.storeData (could be dict or list)."""
        stores = []

        if isinstance(data, list):
            # If it's a list, parse each item
            for item in data:
                if isinstance(item, dict):
                    store = self._parse_store_dict(item)
                    if store:
                        stores.append(store)

        elif isinstance(data, dict):
            # If it's a dict, values might be stores
            logger.info(f"Parsing dict with {len(data)} stores")
            for key, value in data.items():
                if isinstance(value, dict):
                    # Add the key as an ID if not present
                    if "id" not in value:
                        value["id"] = key
                    store = self._parse_store_dict(value)
                    if store:
                        stores.append(store)

        return stores

    def _parse_store_dict(self, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single store from dictionary."""
        # Extract name
        name = (
            data.get("name") or data.get("title") or
            data.get("storeName") or data.get("store_name") or
            data.get("label") or data.get("description") or ""
        )

        if not name:
            return None

        # Extract address - might be string or dict
        address = ""
        if isinstance(data.get("address"), str):
            address = data["address"]
        elif isinstance(data.get("address"), dict):
            addr_parts = [
                data["address"].get("street", ""),
                data["address"].get("suburb", ""),
                data["address"].get("city", ""),
                data["address"].get("postcode", ""),
            ]
            address = ", ".join(filter(None, addr_parts))

        # Extract URL
        url = data.get("url") or data.get("link") or data.get("store_url")

        # Extract region/city
        region = (
            data.get("region") or data.get("city") or
            data.get("suburb") or data.get("state") or None
        )

        # Extract coordinates
        lat = data.get("lat") or data.get("latitude")
        lon = data.get("lng") or data.get("lon") or data.get("longitude")

        return {
            "name": name,
            "address": address or None,
            "region": region,
            "lat": float(lat) if lat and lat != "" and lat != "null" else None,
            "lon": float(lon) if lon and lon != "" and lon != "null" else None,
            "url": url,
        }


__all__ = ["ThirstyLiquorLocationScraper"]
