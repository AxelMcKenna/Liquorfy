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
    store_locator_url = "https://www.glengarrywines.co.nz/stores"
    fallback_store_locator_url = "https://www.glengarry.co.nz/stores"

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
                    await self._navigate_with_retry(page)
                    # Wait for store elements to load
                    await page.wait_for_timeout(3000)  # Give JS time to render
                    html = await page.content()
                    structured_data = await self._extract_structured_data(page)
                finally:
                    await page.close()
            else:
                # Fallback to HTTP (if store list is static HTML)
                response = await self.client.get(self.store_locator_url)
                response.raise_for_status()
                html = response.text
                structured_data = None

            tree = HTMLParser(html)

            # Try multiple possible selectors for store cards
            store_selectors = [
                '.store-card',
                '.store-locator-item',
                '.store-list-item',
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
                logger.warning("No store elements found with any selector; trying structured data fallback")
                if structured_data:
                    stores = self._parse_structured_data(structured_data)
                    logger.info(f"Structured data fallback extracted {len(stores)} Glengarry stores")
                else:
                    logger.warning("No structured store data found")
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

    async def _navigate_with_retry(self, page) -> None:
        """Navigate to the store locator with retries and hostname fallback."""
        targets = [self.store_locator_url, self.fallback_store_locator_url]
        last_error: Exception | None = None

        for url in targets:
            for attempt in range(1, 4):
                try:
                    logger.info("Navigating to %s (attempt %s/3)", url, attempt)
                    await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                    return
                except Exception as exc:
                    last_error = exc
                    logger.warning("Navigation failed for %s (attempt %s/3): %s", url, attempt, exc)
                    await page.wait_for_timeout(1500 * attempt)

        if last_error:
            raise last_error

    async def _extract_structured_data(self, page):
        """Extract store data from window globals or JSON script blobs."""
        return await page.evaluate("""() => {
            const maybeStoreKeys = ['storeData', 'stores', 'storeLocations', 'locations', '__NEXT_DATA__'];
            for (const key of maybeStoreKeys) {
                if (window[key]) return window[key];
            }

            const scripts = Array.from(document.querySelectorAll('script'));
            for (const script of scripts) {
                const text = script.textContent || '';
                if (!text || text.length < 20) continue;

                try {
                    const parsed = JSON.parse(text);
                    if (!parsed) continue;
                    if (Array.isArray(parsed)) return parsed;
                    if (parsed.stores || parsed.locations || parsed.storeData || parsed.props || parsed['@graph']) {
                        return parsed;
                    }
                } catch (_) {
                    // Ignore non-JSON scripts
                }
            }
            return null;
        }""")

    def _parse_structured_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store objects from common structured-data shapes."""
        stores: List[Dict[str, Any]] = []

        def add_store(raw: Dict[str, Any]) -> None:
            parsed = self._parse_structured_store(raw)
            if parsed:
                stores.append(parsed)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    add_store(item)
            return stores

        if not isinstance(data, dict):
            return stores

        # Direct keyed arrays
        for key in ("stores", "locations", "storeData"):
            raw_items = data.get(key)
            if isinstance(raw_items, list):
                for item in raw_items:
                    if isinstance(item, dict):
                        add_store(item)
                if stores:
                    return stores

        # Next.js payload shape
        props = data.get("props", {})
        if isinstance(props, dict):
            page_props = props.get("pageProps", {})
            if isinstance(page_props, dict):
                for key in ("stores", "locations", "storeData"):
                    raw_items = page_props.get(key)
                    if isinstance(raw_items, list):
                        for item in raw_items:
                            if isinstance(item, dict):
                                add_store(item)
                        if stores:
                            return stores

        # JSON-LD graph shape
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    add_store(item)

        return stores

    def _parse_structured_store(self, raw: Dict[str, Any]) -> Dict[str, Any] | None:
        """Normalize varied store-object shapes into the runner's schema."""
        name = (
            raw.get("name")
            or raw.get("Name")
            or raw.get("title")
            or raw.get("label")
            or raw.get("storeName")
        )
        if not name:
            return None

        address = raw.get("address") or raw.get("Address")
        if isinstance(address, dict):
            address_parts = [
                address.get("streetAddress"),
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("postalCode"),
            ]
            address = ", ".join([p for p in address_parts if p]) or None
        elif isinstance(address, str):
            address = re.sub(r"\s+", " ", address).strip()
        else:
            address = None

        region = (
            raw.get("region")
            or raw.get("city")
            or raw.get("state")
            or raw.get("addressRegion")
            or raw.get("addressLocality")
        )
        url = raw.get("url") or raw.get("link")

        lat = raw.get("lat") or raw.get("latitude")
        lon = raw.get("lon") or raw.get("lng") or raw.get("longitude")
        geo = raw.get("geo")
        if isinstance(geo, dict):
            lat = lat or geo.get("latitude")
            lon = lon or geo.get("longitude")

        try:
            lat_f = float(lat) if lat not in (None, "") else None
        except (TypeError, ValueError):
            lat_f = None
        try:
            lon_f = float(lon) if lon not in (None, "") else None
        except (TypeError, ValueError):
            lon_f = None

        return {
            "name": str(name).strip(),
            "address": address,
            "region": str(region).strip() if region else None,
            "lat": lat_f,
            "lon": lon_f,
            "url": str(url).strip() if url else None,
        }


__all__ = ["GlengarryLocationScraper"]
