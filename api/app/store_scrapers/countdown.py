"""Countdown/Woolworths store location scraper."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import List, Dict, Any

import httpx
from playwright.async_api import Page

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class CountdownLocationScraper(StoreLocationScraper):
    """Scraper for Countdown store locations using Playwright."""

    chain = "countdown"
    store_locator_url = "https://www.countdown.co.nz/store-finder"
    cdx_api_url = "https://api.cdx.nz/site-location/api/v1/sites/search"

    def __init__(self) -> None:
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Countdown store locations."""
        logger.info(f"Fetching stores for {self.chain} using browser")

        # Primary path: CDX API is more stable than the browser store-finder page.
        cdx_stores = await self._fetch_stores_from_cdx_api()
        if cdx_stores:
            logger.info(f"Found {len(cdx_stores)} stores for {self.chain} via CDX API")
            return cdx_stores

        try:
            page = await self.context.new_page()
            await page.goto(self.store_locator_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # Try to extract from window or API
            stores = await self._extract_stores_from_page(page)

            await page.close()

            logger.info(f"Found {len(stores)} stores for {self.chain}")
            return stores

        except Exception as e:
            logger.error(f"Failed to fetch stores for {self.chain}: {e}")
            return []

    async def _fetch_stores_from_cdx_api(self) -> List[Dict[str, Any]]:
        """Fetch Countdown stores from the public CDX site-location API."""
        headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        # Empty query often returns all stores, but keep fallbacks.
        queries = ["", "NZ", "Auckland", "Wellington", "Christchurch"]
        seen_ids: set[str] = set()
        raw_items: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for query in queries:
                    try:
                        response = await client.get(self.cdx_api_url, params={"q": query}, headers=headers)
                        response.raise_for_status()
                        payload = response.json()
                        items = payload.get("items", [])
                        logger.info("CDX query '%s' returned %s stores", query, len(items))

                        for item in items:
                            store_id = str(item.get("id", "")).strip()
                            if not store_id or store_id in seen_ids:
                                continue
                            seen_ids.add(store_id)
                            raw_items.append(item)
                    except Exception as exc:
                        logger.warning("CDX query '%s' failed: %s", query, exc)

            return self._parse_generic_store_data(raw_items)
        except Exception as exc:
            logger.warning("CDX API store fetch failed: %s", exc)
            return []

    async def _extract_stores_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """Extract store data from page."""

        # Countdown might have a store API endpoint
        try:
            # Look for API calls
            api_data = await page.evaluate("""async () => {
                try {
                    const response = await fetch('/api/stores');
                    if (response.ok) {
                        return await response.json();
                    }
                } catch (e) {}

                // Look in window object
                if (window.stores) return window.stores;
                if (window.storeData) return window.storeData;
                if (window.woolworthsStores) return window.woolworthsStores;

                return null;
            }""")

            if api_data:
                logger.info("Found store data from API or window object")
                return self._parse_generic_store_data(api_data)

        except Exception as e:
            logger.warning(f"Failed to fetch from API: {e}")

        # Fallback: DOM extraction
        logger.info("Extracting stores from DOM")
        stores = await page.evaluate("""() => {
            const storeElements = document.querySelectorAll(
                '.store, .store-card, [data-storeid], [data-store-id]'
            );
            const stores = [];

            storeElements.forEach((el) => {
                const nameEl = el.querySelector('h2, h3, h4, .store-name, [class*="name"]');
                const addressEl = el.querySelector('.address, [class*="address"]');

                stores.push({
                    name: nameEl ? nameEl.innerText.trim() : '',
                    address: addressEl ? addressEl.innerText.trim() : '',
                    lat: el.dataset.lat || el.dataset.latitude || null,
                    lon: el.dataset.lon || el.dataset.lng || el.dataset.longitude || null,
                });
            });

            return stores;
        }""")

        return [s for s in self._parse_generic_store_data(stores) if s.get("name") and s.get("address")]

    def _parse_generic_store_data(self, data: Any) -> List[Dict[str, Any]]:
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
        name = (
            data.get("name") or data.get("title") or
            data.get("storeName") or data.get("store_name") or ""
        )

        # Handle address - might be string or object
        address = ""
        if "address" in data:
            if isinstance(data["address"], str):
                address = data["address"]
            elif isinstance(data["address"], dict):
                parts = [
                    data["address"].get("street", ""),
                    data["address"].get("suburb", ""),
                    data["address"].get("city", ""),
                ]
                address = ", ".join(filter(None, parts))
        else:
            parts = [
                data.get("street", ""),
                data.get("suburb", ""),
                data.get("city", ""),
            ]
            address = ", ".join(filter(None, parts))
            if not address:
                # CDX format fallback
                cdx_parts = [
                    data.get("suburb", ""),
                    data.get("state", ""),
                    data.get("postcode", ""),
                ]
                address = ", ".join(filter(None, cdx_parts))

        lat = data.get("lat") or data.get("latitude")
        lon = data.get("lng") or data.get("lon") or data.get("longitude")

        region = (
            data.get("region") or data.get("city") or
            data.get("suburb") or None
        )

        url = data.get("url") or data.get("link") or None

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


__all__ = ["CountdownLocationScraper"]
