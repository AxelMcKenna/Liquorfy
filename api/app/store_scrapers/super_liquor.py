"""Super Liquor store location scraper - using API."""
from __future__ import annotations

import logging
from typing import List, Dict, Any
import httpx

from app.store_scrapers.base import StoreLocationScraper

logger = logging.getLogger(__name__)


class SuperLiquorLocationScraper(StoreLocationScraper):
    """Scraper for Super Liquor store locations using their API."""

    chain = "super_liquor"
    store_locator_url = "https://www.superliquor.co.nz/getstorelocatordetails"

    def __init__(self):
        # Super Liquor uses an API, no browser needed
        super().__init__(use_browser=False)

    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """Fetch all Super Liquor store locations from API."""
        logger.info(f"Fetching stores for {self.chain}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.store_locator_url)
                response.raise_for_status()

                data = response.json()

                if not data or 'Locations' not in data:
                    logger.error(f"No Locations found in API response for {self.chain}")
                    return []

                logger.info(f"Found {len(data['Locations'])} stores in API response")
                return data['Locations']

        except Exception as e:
            logger.error(f"Failed to fetch stores from API: {e}")
            raise

    async def parse_store(self, store_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Super Liquor store data from API into standardized format.

        Example data:
        {
            "Id": 1,
            "Name": "Alexandra",
            "Address": "114 Centennial Avenue",
            "FullAddress": "114 Centennial Avenue, Alexandra",
            "City": "Alexandra",
            "State": "Otago",
            "Country": "New Zealand",
            "ZipPostalCode": "9320",
            "PhoneNumber": "03 448 8314",
            "Email": "alexandra.superliquor@gmail.com",
            "Latitude": -45.254913,
            "Longitude": 169.392822,
            "AreaName": "Otago",
            "Description": "...",
            "ImageUrl": "https://...",
            "GoogleMapLocation": "https://maps.google.com/?q=...",
            "StoreLocationUrl": "/alexandra",
            "StoreDetailsUrl": "/storedetails/alexandra",
            ...
        }
        """
        try:
            # Extract basic info
            name = store_data.get('Name', '').strip()
            address = store_data.get('Address', '').strip()
            city = store_data.get('City', '').strip()
            region = store_data.get('State', '').strip()
            postcode = store_data.get('ZipPostalCode', '').strip()
            phone = store_data.get('PhoneNumber', '').strip()

            # Coordinates
            lat = store_data.get('Latitude')
            lng = store_data.get('Longitude')

            # Validate
            if not name:
                raise ValueError("Store name is required")

            if not lat or not lng:
                raise ValueError(f"Coordinates missing for {name}")

            result = {
                'name': name,
                'address': address,
                'suburb': None,  # Not provided by API
                'city': city,
                'region': region,
                'postcode': postcode,
                'phone': phone,
                'latitude': float(lat),
                'longitude': float(lng),
            }

            logger.debug(f"Parsed store: {result['name']}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse store {store_data.get('Name', 'Unknown')}: {e}")
            raise


__all__ = ["SuperLiquorLocationScraper"]
