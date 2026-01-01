"""Black Bull store location scraper."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class BlackBullLocationScraper(StoreLocationScraper):
    """Scraper for Black Bull store locations."""

    chain = "black_bull"
    store_locator_url = "https://blackbullliquor.co.nz/store-locator"

    def __init__(self):
        # Black Bull needs browser for JS-rendered content
        super().__init__(use_browser=True)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Black Bull store locations from the embedded map data."""
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

                # Extract store data from the embedded map script
                # The data is in a markers array within the map configuration
                store_data = await page.evaluate("""() => {
                    // Look for the script containing store data
                    const scripts = Array.from(document.querySelectorAll('script'));
                    for (const script of scripts) {
                        const content = script.textContent;
                        if (content && content.includes('"markers"')) {
                            try {
                                // Find the start of markers array
                                const markerStart = content.indexOf('"markers":');
                                if (markerStart === -1) continue;

                                // Find the opening bracket
                                const arrayStart = content.indexOf('[', markerStart);
                                if (arrayStart === -1) continue;

                                // Find the matching closing bracket by counting brackets
                                let bracketCount = 0;
                                let arrayEnd = -1;
                                for (let i = arrayStart; i < content.length; i++) {
                                    if (content[i] === '[') bracketCount++;
                                    if (content[i] === ']') {
                                        bracketCount--;
                                        if (bracketCount === 0) {
                                            arrayEnd = i;
                                            break;
                                        }
                                    }
                                }

                                if (arrayEnd === -1) continue;

                                // Extract the markers JSON
                                const markersStr = content.substring(arrayStart, arrayEnd + 1);
                                const markers = JSON.parse(markersStr);

                                if (markers && markers.length > 0) {
                                    return markers;
                                }
                            } catch (e) {
                                console.error('Failed to parse markers:', e);
                            }
                        }
                    }
                    return null;
                }
                """)

                if not store_data:
                    logger.warning("Store data not found in embedded map script")
                    return []

                logger.info(f"Found {len(store_data)} stores in map data")

                stores = self._parse_map_marker_data(store_data)
                logger.info(f"Successfully extracted {len(stores)} Black Bull stores")
                return stores

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Failed to fetch Black Bull stores: {e}", exc_info=True)
            return []

    def _parse_map_marker_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from embedded map markers array."""
        stores = []

        if not isinstance(data, list):
            logger.warning(f"Expected list but got {type(data)}")
            return stores

        for item in data:
            if not isinstance(item, dict):
                continue

            store = self._parse_map_marker(item)
            if store:
                stores.append(store)

        return stores

    def _parse_map_marker(self, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single store from map marker data."""
        import re

        # Extract name from title
        name = data.get("title", "").strip()
        if not name:
            return None

        # Extract coordinates from position object
        position = data.get("position", {})
        lat = position.get("latitude") or position.get("lat")
        lon = position.get("longitude") or position.get("lng")

        # Extract address from listHtml or html field
        address_html = data.get("listHtml") or data.get("html") or ""

        # Clean HTML and extract address
        # Remove HTML tags and get just the address text
        address = re.sub(r'<[^>]+>', '', address_html)
        address = re.sub(r'\s+', ' ', address).strip()

        # Extract just the address portion (before phone number)
        # Addresses typically come before "Phone:" or tel: links
        if "Phone:" in address:
            address = address.split("Phone:")[0].strip()
        elif address.count(',') >= 2:
            # Take first few comma-separated parts as address
            parts = [p.strip() for p in address.split(',')]
            # Filter out empty parts and phone numbers
            address_parts = [p for p in parts if p and not p.startswith('0') or len(p) > 15]
            address = ', '.join(address_parts[:3]) if address_parts else address

        # Extract region from mapsCategories
        region = None
        categories = data.get("mapsCategories", [])
        if categories and isinstance(categories, list) and len(categories) > 0:
            # Extract category from first element
            first_cat = categories[0]
            if isinstance(first_cat, dict):
                # Use CategoryName if available
                region = first_cat.get("CategoryName")

                # Or map CategoryID to region name
                if not region:
                    category_id = first_cat.get("CategoryID")
                    category_map = {
                        12: "Auckland",
                        13: "Waikato",
                        14: "Bay of Plenty-Hawkes Bay",
                        15: "Gisborne",
                        16: "Manawatu-Wanganui",
                        17: "Taranaki",
                        18: "Wellington",
                        19: "South Island"
                    }
                    region = category_map.get(category_id)
            elif isinstance(first_cat, (int, str)):
                # If it's just an ID
                category_map = {
                    12: "Auckland",
                    13: "Waikato",
                    14: "Bay of Plenty-Hawkes Bay",
                    15: "Gisborne",
                    16: "Manawatu-Wanganui",
                    17: "Taranaki",
                    18: "Wellington",
                    19: "South Island"
                }
                region = category_map.get(first_cat)

        # Check if there's a specific store URL in the markerHtml
        url = None
        marker_html = data.get("markerHtml", "")
        url_match = re.search(r'https?://[^\s<>"]+', marker_html)
        if url_match:
            url = url_match.group(0)

        return {
            "name": name,
            "address": address,
            "region": region,
            "lat": float(lat) if lat and lat != "" and lat != "null" else None,
            "lon": float(lon) if lon and lon != "" and lon != "null" else None,
            "url": url,
        }

    def _parse_store_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse store data from window.storeLocationsData array."""
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


__all__ = ["BlackBullLocationScraper"]
