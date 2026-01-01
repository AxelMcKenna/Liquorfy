"""Generic store location scraper for chains with similar store locator pages."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from playwright.async_api import Page

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class GenericLocationScraper(StoreLocationScraper):
    """Generic scraper that can be configured for different chains."""

    def __init__(self, chain: str, store_locator_url: str) -> None:
        """
        Initialize generic scraper.

        Args:
            chain: Chain identifier (e.g., 'new_world', 'pak_n_save')
            store_locator_url: URL of the store locator page
        """
        super().__init__(use_browser=True)
        self.chain = chain
        self.store_locator_url = store_locator_url

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all store locations."""
        logger.info(f"Fetching stores for {self.chain} from {self.store_locator_url}")

        try:
            page = await self.context.new_page()
            await page.goto(self.store_locator_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            stores = await self._extract_stores_from_page(page)

            await page.close()

            logger.info(f"Found {len(stores)} stores for {self.chain}")
            return stores

        except Exception as e:
            logger.error(f"Failed to fetch stores for {self.chain}: {e}")
            return []

    async def _extract_stores_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """Extract store data using multiple strategies."""

        # Strategy 1: Look in window object
        store_data = await page.evaluate("""() => {
            const possibleKeys = [
                'stores', 'storeData', 'storeLocations', 'locations',
                'storeList', 'allStores', 'storeInfo'
            ];

            for (const key of possibleKeys) {
                if (window[key]) return window[key];
            }

            // Look in script tags for JSON
            const scripts = document.querySelectorAll('script');
            for (const script of scripts) {
                if (!script.textContent) continue;

                // Try to find store-related JSON
                const patterns = [
                    /(?:var|let|const)\\s+stores\\s*=\\s*(\\[.*?\\]);/s,
                    /(?:var|let|const)\\s+storeData\\s*=\\s*(\\[.*?\\]);/s,
                    /(?:var|let|const)\\s+locations\\s*=\\s*(\\[.*?\\]);/s,
                ];

                for (const pattern of patterns) {
                    const match = script.textContent.match(pattern);
                    if (match) {
                        try {
                            return JSON.parse(match[1]);
                        } catch (e) {}
                    }
                }
            }

            return null;
        }""")

        if store_data:
            logger.info("Found store data in window object or scripts")
            return self._parse_store_data(store_data)

        # Strategy 2: DOM extraction
        logger.info("Extracting stores from DOM")
        stores = await page.evaluate("""() => {
            // Try multiple selectors
            const selectors = [
                '.store-item', '.store-location', '.store-card', '.store',
                '[data-store]', '[data-storeid]', '[data-store-id]',
                'li[class*="store"]', 'div[class*="store"]'
            ];

            let storeElements = [];
            for (const selector of selectors) {
                storeElements = document.querySelectorAll(selector);
                if (storeElements.length > 0) break;
            }

            const stores = [];

            storeElements.forEach((el) => {
                // Try multiple selectors for name
                const nameEl = el.querySelector([
                    'h1', 'h2', 'h3', 'h4',
                    '.store-name', '.name', '[class*="name"]',
                    '.store-title', '.title'
                ].join(','));

                // Try multiple selectors for address
                const addressEl = el.querySelector([
                    '.address', '.store-address', '[class*="address"]',
                    '.location', '[class*="location"]'
                ].join(','));

                const name = nameEl ? nameEl.innerText.trim() : '';
                const address = addressEl ? addressEl.innerText.trim() : '';

                // Try to get coordinates from data attributes
                const lat = (
                    el.dataset.lat || el.dataset.latitude ||
                    el.getAttribute('data-lat') || el.getAttribute('data-latitude')
                );

                const lon = (
                    el.dataset.lon || el.dataset.lng || el.dataset.longitude ||
                    el.getAttribute('data-lon') || el.getAttribute('data-lng') ||
                    el.getAttribute('data-longitude')
                );

                if (name || address) {
                    stores.push({
                        name: name,
                        address: address,
                        lat: lat,
                        lon: lon,
                    });
                }
            });

            return stores;
        }""")

        parsed_stores = []
        for store in stores:
            name = store.get("name", "").strip()
            address = store.get("address", "").strip()

            if not name or not address:
                continue

            lat = store.get("lat")
            lon = store.get("lon")

            parsed_stores.append({
                "name": name,
                "address": address,
                "region": None,
                "lat": float(lat) if lat and lat != "null" else None,
                "lon": float(lon) if lon and lon != "null" else None,
                "url": None,
            })

        return parsed_stores

    def _parse_store_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from various formats."""
        stores = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    store = self._parse_single_store(item)
                    if store:
                        stores.append(store)

        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    store = self._parse_single_store(value)
                    if store:
                        stores.append(store)

        return stores

    def _parse_single_store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single store from dictionary."""
        # Try various key names
        name = (
            data.get("name") or data.get("title") or
            data.get("storeName") or data.get("store_name") or
            data.get("displayName") or ""
        )

        # Handle address
        address = ""
        if "address" in data:
            if isinstance(data["address"], str):
                address = data["address"]
            elif isinstance(data["address"], dict):
                parts = [
                    data["address"].get("street", ""),
                    data["address"].get("suburb", ""),
                    data["address"].get("city", ""),
                    data["address"].get("postcode", ""),
                ]
                address = ", ".join(filter(None, parts))
        else:
            parts = [
                data.get("street", ""),
                data.get("address1", ""),
                data.get("address2", ""),
                data.get("suburb", ""),
                data.get("city", ""),
                data.get("postcode", ""),
            ]
            address = ", ".join(filter(None, parts))

        lat = (
            data.get("lat") or data.get("latitude") or
            data.get("geo", {}).get("lat") or
            data.get("coordinates", {}).get("lat")
        )

        lon = (
            data.get("lng") or data.get("lon") or data.get("longitude") or
            data.get("geo", {}).get("lng") or data.get("geo", {}).get("lon") or
            data.get("coordinates", {}).get("lng") or data.get("coordinates", {}).get("lon")
        )

        region = (
            data.get("region") or data.get("city") or
            data.get("suburb") or data.get("area") or None
        )

        url = data.get("url") or data.get("link") or data.get("storeUrl") or None

        if not name or not address:
            return None

        return {
            "name": name,
            "address": address,
            "region": region,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "url": url,
        }


__all__ = ["GenericLocationScraper"]
