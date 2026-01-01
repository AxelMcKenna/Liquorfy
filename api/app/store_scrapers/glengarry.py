"""Glengarry store location scraper."""
from __future__ import annotations

import logging
import re
from typing import List, Dict, Any

from selectolax.parser import HTMLParser

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)

# Common NZ cities/regions to extract from addresses
NZ_REGIONS = [
    "Porirua", "Wellington", "Lower Hutt", "Upper Hutt", "Petone",
    "Auckland", "Christchurch", "Hamilton", "Tauranga", "Dunedin",
    "Palmerston North", "Napier", "Hastings", "New Plymouth", "Rotorua",
    "Whangarei", "Nelson", "Invercargill", "Gisborne", "Queenstown",
]


class GlengarryLocationScraper(StoreLocationScraper):
    """Scraper for Glengarry store locations."""

    chain = "glengarry"
    store_locator_url = "https://www.glengarry.co.nz/stores"

    def __init__(self):
        # Glengarry may need browser for JS-rendered content
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """
        Fetch Glengarry store locations.

        Returns:
            List of store dictionaries with name, address, region, lat, lon, url
        """
        stores = []

        try:
            if self.use_browser and self.context:
                # Use browser for JS-rendered content
                page = await self.context.new_page()
                try:
                    await page.goto(self.store_locator_url, wait_until="domcontentloaded")
                    # Wait for store elements to load
                    await page.wait_for_timeout(3000)  # Give JS time to render
                    html = await page.content()
                finally:
                    await page.close()
            else:
                # Fallback to HTTP (if store list is static HTML)
                response = await self.client.get(self.store_locator_url)
                response.raise_for_status()
                html = response.text

            tree = HTMLParser(html)

            # Try multiple possible selectors for store cards
            store_selectors = [
                '.store-card',
                '.store-item',
                '.store',
                '[class*="store"]',
                'article',
                '.location',
                '[class*="location"]',
            ]

            store_elements = []
            for selector in store_selectors:
                store_elements = tree.css(selector)
                if store_elements:
                    logger.info(f"Found {len(store_elements)} stores using selector: {selector}")
                    break

            if not store_elements:
                logger.warning("No store elements found with any selector")
                return stores

            for store_elem in store_elements:
                try:
                    # Extract store name
                    name = None
                    name_selectors = ['h2', 'h3', '.store-name', '.name', '[class*="name"]', '.title']
                    for name_sel in name_selectors:
                        name_elem = store_elem.css_first(name_sel)
                        if name_elem and name_elem.text(strip=True):
                            name = name_elem.text(strip=True)
                            break

                    if not name:
                        logger.debug("Store element missing name, skipping")
                        continue

                    # Extract address
                    address = None
                    address_selectors = ['.store-address', 'address', '.address', '[class*="address"]', 'p']
                    for addr_sel in address_selectors:
                        addr_elem = store_elem.css_first(addr_sel)
                        if addr_elem and addr_elem.text(strip=True):
                            address_text = addr_elem.text(strip=True)
                            # Clean up address (remove extra whitespace, newlines)
                            address = re.sub(r'\s+', ' ', address_text).strip()
                            break

                    # Extract region/city from address or separate field
                    region = None
                    if address:
                        # Look for NZ regions in the address
                        address_lower = address.lower()
                        for city in NZ_REGIONS:
                            if city.lower() in address_lower:
                                region = city
                                break

                    # If no region found in address, try to find a separate region element
                    if not region:
                        region_selectors = ['.region', '.city', '[class*="region"]', '[class*="city"]']
                        for reg_sel in region_selectors:
                            reg_elem = store_elem.css_first(reg_sel)
                            if reg_elem and reg_elem.text(strip=True):
                                region = reg_elem.text(strip=True)
                                break

                    # Extract URL if available
                    url = None
                    url_elem = store_elem.css_first('a[href]')
                    if url_elem:
                        href = url_elem.attributes.get('href')
                        if href:
                            if href.startswith('http'):
                                url = href
                            elif href.startswith('/'):
                                url = f"https://www.glengarry.co.nz{href}"

                    # Extract coordinates (may be in data attributes or JSON)
                    lat = None
                    lon = None

                    # Try data attributes
                    for attr_name in ['data-lat', 'data-latitude', 'lat']:
                        if store_elem.attributes.get(attr_name):
                            try:
                                lat = float(store_elem.attributes[attr_name])
                            except ValueError:
                                pass

                    for attr_name in ['data-lon', 'data-lng', 'data-longitude', 'lon', 'lng']:
                        if store_elem.attributes.get(attr_name):
                            try:
                                lon = float(store_elem.attributes[attr_name])
                            except ValueError:
                                pass

                    # If no lat/lon, geocoding service will handle it later
                    stores.append({
                        "name": name,
                        "address": address,
                        "region": region,
                        "lat": lat,
                        "lon": lon,
                        "url": url,
                    })

                    logger.debug(f"Extracted store: {name} in {region or 'Unknown'}")

                except Exception as e:
                    logger.error(f"Failed to parse Glengarry store: {e}")
                    continue

            logger.info(f"Successfully extracted {len(stores)} Glengarry stores")

        except Exception as e:
            logger.error(f"Failed to fetch Glengarry stores: {e}", exc_info=True)

        return stores


__all__ = ["GlengarryLocationScraper"]
