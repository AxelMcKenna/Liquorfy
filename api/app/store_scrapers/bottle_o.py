"""Bottle O store location scraper."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class BottleOLocationScraper(StoreLocationScraper):
    """Scraper for Bottle O store locations."""

    chain = "bottle_o"
    store_locator_url = "https://shop.thebottleo.co.nz/change"

    def __init__(self):
        # Bottle O needs browser for JS-rendered content
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Bottle O store locations from window.store_data."""
        logger.info(f"Fetching stores for {self.chain}")

        try:
            if not self.context:
                logger.error("Browser context not available")
                return []

            # Navigate to page
            page = await self.context.new_page()
            try:
                await page.goto(self.store_locator_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)  # Give JS time to render stores

                # Look for StoreCard sections (there are many divs with StoreCard in class)
                # We need the ones that contain the actual store info
                all_text = await page.inner_text('body')

                # Extract using JavaScript to get the actual store card containers
                stores_data = await page.evaluate("""() => {
                    // Find all elements with StoreCard class that have substantial content
                    const allElements = Array.from(document.querySelectorAll('[class*="StoreCard"]'));

                    const stores = [];
                    const seenTexts = new Set();

                    for (const el of allElements) {
                        const text = el.innerText || '';

                        // Must have operating hours info and decent length
                        if ((text.includes('Open') || text.includes('Closed')) &&
                            text.length > 50 && text.length < 1000 &&
                            !seenTexts.has(text)) {

                            seenTexts.add(text);

                            // Extract the shop now link
                            const shopLink = el.querySelector('a[href*="i_choose_you"]');
                            const url = shopLink ? shopLink.getAttribute('href') : null;

                            // Extract address from Google Maps link
                            const mapsLink = el.querySelector('a[href*="maps.google"]');
                            let address = null;
                            if (mapsLink) {
                                const href = mapsLink.getAttribute('href');
                                const match = href.match(/q=([^#]+)/);
                                if (match) {
                                    address = decodeURIComponent(match[1].replace(/\\+/g, ' '));
                                }
                            }

                            // Extract store name - skip hours lines
                            const lines = text.split('\\n').filter(l => l.trim());
                            let name = 'Unknown';

                            for (const line of lines) {
                                // Skip lines that are hours, not names
                                if (!line.includes('Open') && !line.includes('Closed') &&
                                    !line.includes('am') && !line.includes('pm') &&
                                    !line.includes(':') && line.length > 2 && line.length < 50) {
                                    name = line;
                                    break;
                                }
                            }

                            stores.push({
                                name: name.trim(),
                                address: address,
                                url: url,
                                rawText: text.substring(0, 200)
                            });
                        }
                    }

                    return stores;
                }""")

                if not stores_data:
                    logger.warning("No store data extracted")
                    return []

                logger.info(f"Found {len(stores_data)} stores")

                # Deduplicate by URL (some stores appear multiple times)
                seen_urls = set()
                stores = []

                for data in stores_data:
                    url = data.get('url')

                    # Skip stores without URLs or duplicates
                    if not url or url in seen_urls:
                        continue

                    seen_urls.add(url)

                    if not url.startswith('http'):
                        url = f"https://shop.thebottleo.co.nz{url}"

                    stores.append({
                        "name": data['name'],
                        "address": data.get('address'),
                        "region": None,
                        "lat": None,
                        "lon": None,
                        "url": url,
                    })

                logger.info(f"Successfully extracted {len(stores)} Bottle O stores")
                return stores

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Failed to fetch Bottle O stores: {e}", exc_info=True)
            return []

    def _parse_store_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from window.store_data array."""
        stores = []

        if not isinstance(data, list):
            logger.warning(f"Expected list but got {type(data)}")
            return stores

        for item in data:
            if not isinstance(item, dict):
                continue

            store = self._parse_store_dict(item)
            if store:
                stores.append(store)

        return stores

    def _parse_store_dict(self, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single store from dictionary."""
        # Extract name
        name = (
            data.get("name") or data.get("title") or
            data.get("storeName") or data.get("store_name") or
            data.get("label") or ""
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

        # Extract region/city
        region = (
            data.get("region") or data.get("city") or
            data.get("suburb") or data.get("state") or None
        )

        # Extract coordinates
        lat = data.get("lat") or data.get("latitude")
        lon = data.get("lng") or data.get("lon") or data.get("longitude")

        # Extract URL
        url = data.get("url") or data.get("link") or data.get("store_url")

        return {
            "name": name,
            "address": address,
            "region": region,
            "lat": float(lat) if lat and lat != "" and lat != "null" else None,
            "lon": float(lon) if lon and lon != "" and lon != "null" else None,
            "url": url,
        }


__all__ = ["BottleOLocationScraper"]
