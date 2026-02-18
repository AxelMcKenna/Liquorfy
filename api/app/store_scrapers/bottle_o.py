"""Bottle O store location scraper."""
from __future__ import annotations

import logging
import re
from typing import List, Dict, Any

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)

# Pattern to extract the store subdomain from a resolved shop URL
_SHOP_URL_PATTERN = re.compile(
    r"https?://([a-z0-9-]+)\.shop\.thebottleo\.co\.nz", re.IGNORECASE
)


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

                # Deduplicate by URL and resolve i_choose_you redirects
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

                    # Resolve i_choose_you redirect to get real store subdomain
                    resolved_url = await self._resolve_shop_url(page, url)

                    stores.append({
                        "name": data['name'],
                        "address": data.get('address'),
                        "region": None,
                        "lat": None,
                        "lon": None,
                        "url": resolved_url,
                    })

                logger.info(f"Successfully extracted {len(stores)} Bottle O stores")
                return stores

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Failed to fetch Bottle O stores: {e}", exc_info=True)
            return []

    async def _resolve_shop_url(self, page, i_choose_you_url: str) -> str:
        """
        Follow an i_choose_you redirect to discover the store's actual
        subdomain URL (e.g. https://albany.shop.thebottleo.co.nz).

        Falls back to the original URL if the redirect cannot be resolved.
        """
        try:
            response = await page.request.fetch(
                i_choose_you_url,
                max_redirects=0,  # Don't follow — just read the Location header
            )
            location = response.headers.get("location", "")
            match = _SHOP_URL_PATTERN.search(location)
            if match:
                resolved = f"https://{match.group(1)}.shop.thebottleo.co.nz"
                logger.debug(f"Resolved {i_choose_you_url} -> {resolved}")
                return resolved
        except Exception as e:
            logger.debug(f"Could not resolve redirect for {i_choose_you_url}: {e}")

        # Fallback: return the original URL
        return i_choose_you_url


__all__ = ["BottleOLocationScraper"]
