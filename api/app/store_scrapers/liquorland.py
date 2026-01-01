"""Liquorland store location scraper."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import List, Dict, Any

from playwright.async_api import Page

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class LiquorlandLocationScraper(StoreLocationScraper):
    """Scraper for Liquorland store locations using Playwright."""

    chain = "liquorland"
    store_locator_url = "https://www.liquorland.co.nz/store-locations"

    def __init__(self) -> None:
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Liquorland store locations."""
        logger.info(f"Fetching stores for {self.chain} using browser")

        try:
            page = await self.context.new_page()
            await page.goto(self.store_locator_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)  # Wait for stores to load

            # Try to extract from window object or page content
            stores = await self._extract_stores_from_page(page)

            await page.close()

            logger.info(f"Found {len(stores)} stores for {self.chain}")
            return stores

        except Exception as e:
            logger.error(f"Failed to fetch stores for {self.chain}: {e}")
            return []

    async def _extract_stores_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """Extract store data from page."""

        # Try to extract from window object
        store_data = await page.evaluate("""() => {
            // Look for store data in window
            if (window.storeData) return window.storeData;
            if (window.stores) return window.stores;
            if (window.storeLocations) return window.storeLocations;

            // Look for JSON in script tags
            const scripts = document.querySelectorAll('script');
            for (const script of scripts) {
                if (script.textContent && script.textContent.includes('store')) {
                    // Try to find JSON array
                    const matches = script.textContent.match(/(?:var|let|const)\\s+\\w+\\s*=\\s*(\\[.*?\\]);/s);
                    if (matches) {
                        try {
                            return JSON.parse(matches[1]);
                        } catch (e) {}
                    }
                }
            }

            return null;
        }""")

        if store_data:
            logger.info(f"Extracted {len(store_data) if isinstance(store_data, list) else 'unknown'} stores from window object")
            return self._parse_store_data(store_data)

        # Fallback: extract from DOM
        logger.info("No window data found, extracting from DOM")
        stores = await page.evaluate("""() => {
            const storeElements = document.querySelectorAll(
                '.store-item, .store-location, [data-store], li[class*="store"]'
            );
            const stores = [];

            storeElements.forEach((el) => {
                const nameEl = el.querySelector('h2, h3, h4, .store-name, [class*="name"]');
                const addressEl = el.querySelector('.address, [class*="address"]');

                if (nameEl || addressEl) {
                    stores.push({
                        name: nameEl ? nameEl.innerText.trim() : '',
                        address: addressEl ? addressEl.innerText.trim() : '',
                        lat: el.dataset.lat || el.dataset.latitude || null,
                        lon: el.dataset.lon || el.dataset.lng || el.dataset.longitude || null,
                    });
                }
            });

            return stores;
        }""")

        return self._parse_dom_stores(stores)

    def _parse_store_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from various formats."""
        stores = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    store = self._parse_store_dict(item)
                    if store:
                        stores.append(store)

        elif isinstance(data, dict):
            # Liquorland: dict with store IDs as keys
            logger.info(f"Parsing dict with {len(data)} stores")
            for key, value in data.items():
                if isinstance(value, dict):
                    store = self._parse_store_dict(value)
                    if store:
                        stores.append(store)

        return stores

    def _parse_store_dict(self, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single store from dictionary."""
        # Liquorland format: label, address (full string), latitude/longitude
        name = (
            data.get("label") or data.get("name") or data.get("title") or
            data.get("storeName") or data.get("store_name") or ""
        )

        # Address is provided as a complete string
        address = data.get("address", "")

        # If no full address, build from parts
        if not address:
            address_parts = [
                data.get("address1", ""),
                data.get("address2", ""),
                data.get("suburb", ""),
                data.get("city", ""),
                data.get("postcode", ""),
            ]
            address = ", ".join(filter(None, address_parts))

        if not name or not address:
            return None

        # Coordinates
        lat = data.get("latitude") or data.get("lat")
        lon = data.get("longitude") or data.get("lng") or data.get("lon")

        region = data.get("city") or data.get("suburb") or data.get("region")
        url = data.get("url")

        return {
            "name": name,
            "address": address.replace("\n", ", "),  # Clean up newlines in address
            "region": region,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "url": url,
        }

    def _parse_dom_stores(self, stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse stores extracted from DOM."""
        parsed = []

        for store in stores:
            name = store.get("name", "").strip()
            address = store.get("address", "").strip()

            if not name or not address:
                continue

            lat = store.get("lat")
            lon = store.get("lon")

            parsed.append({
                "name": name,
                "address": address,
                "region": None,
                "lat": float(lat) if lat else None,
                "lon": float(lon) if lon else None,
                "url": None,
            })

        return parsed


__all__ = ["LiquorlandLocationScraper"]
