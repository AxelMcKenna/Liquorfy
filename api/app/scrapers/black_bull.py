"""
Black Bull scraper

Scrapes product data from Black Bull NZ stores using Shopify's JSON API.
Black Bull operates 60+ franchise stores, but only 3 have Shopify-based online ordering.

IMPORTANT: This scraper only covers 3 stores (~5% coverage) due to limited online presence.
Most Black Bull franchises do not offer e-commerce.
"""
import asyncio
import logging
from typing import List
import httpx

from app.scrapers.base import Scraper
from app.services.parser_utils import (
    parse_volume,
    extract_abv,
    infer_brand,
    infer_category,
)

logger = logging.getLogger(__name__)


class BlackBullScraper(Scraper):
    """
    Scraper for Black Bull stores using Shopify API.

    Coverage: 3 out of 60+ stores (~5%)
    - Porirua
    - Greenwood (Hamilton)
    - Hornby Hub (Christchurch)

    Each store operates independently with its own Shopify catalog and pricing.
    """

    chain = "black_bull"

    # Stores with Shopify e-commerce (only 3 out of 60+)
    stores = [
        {
            "name": "Porirua",
            "url": "https://blackbullporirua.co.nz",
            "store_id": "porirua",
        },
        {
            "name": "Greenwood Hamilton",
            "url": "https://blackbullliquorgreenwood.co.nz",
            "store_id": "greenwood",
        },
        {
            "name": "Hornby Hub Christchurch",
            "url": "https://blackbullliquorhornbyhub.co.nz",
            "store_id": "hornby_hub",
        },
    ]

    # Collections to scrape (Shopify collection handles)
    collections = [
        "beer-cider",
        "wine",
        "spirits",
        "rtds",
        "liqueurs",
        "mixers",
    ]

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Fetch all products from Black Bull Shopify stores.
        Returns JSON responses as strings for parsing.
        """
        pages = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for store in self.stores:
                logger.info(f"Fetching store: {store['name']}")

                for collection in self.collections:
                    page_num = 1
                    while True:
                        url = f"{store['url']}/collections/{collection}/products.json"
                        params = {"limit": 250, "page": page_num}

                        try:
                            response = await client.get(url, params=params)
                            response.raise_for_status()

                            data = response.json()
                            products = data.get("products", [])

                            if not products:
                                # No more products in this collection
                                break

                            logger.info(
                                f"  {store['name']} - {collection} page {page_num}: {len(products)} products"
                            )

                            # Add store context to the response for parsing
                            enriched_data = {
                                "products": products,
                                "store_id": store["store_id"],
                                "store_name": store["name"],
                            }
                            pages.append(enriched_data)

                            # If we got fewer than 250 products, we're on the last page
                            if len(products) < 250:
                                break

                            page_num += 1
                            await asyncio.sleep(0.5)  # Rate limiting

                        except httpx.HTTPError as e:
                            logger.error(
                                f"Error fetching {store['name']} {collection} page {page_num}: {e}"
                            )
                            break

                    # Delay between collections
                    await asyncio.sleep(0.5)

                # Delay between stores
                await asyncio.sleep(1.0)

        logger.info(f"Fetched {len(pages)} pages total")
        return pages

    async def parse_products(self, payload: dict | str) -> List[dict]:
        """
        Parse products from Shopify JSON response.

        Args:
            payload: Either a dict with store context or JSON string from Shopify API

        Returns:
            List of standardized product dictionaries
        """
        import json

        # Handle both dict (with store context) and string (JSON) payloads
        if isinstance(payload, str):
            data = json.loads(payload)
            store_id = None
            store_name = None
        else:
            data = payload
            store_id = data.get("store_id")
            store_name = data.get("store_name")

        products = data.get("products", [])
        parsed_products = []

        for product in products:
            try:
                parsed = self._parse_product(product, store_id, store_name)
                if parsed:
                    parsed_products.append(parsed)
            except Exception as e:
                logger.error(f"Error parsing product {product.get('id')}: {e}")

        return parsed_products

    def _parse_product(
        self, product: dict, store_id: str = None, store_name: str = None
    ) -> dict:
        """
        Parse a single Shopify product into our standard format.

        Args:
            product: Shopify product dict
            store_id: Store identifier (e.g., "porirua")
            store_name: Store display name (e.g., "Porirua")

        Returns:
            Standardized product dict
        """
        # Basic product info
        product_id = str(product.get("id", ""))
        title = product.get("title", "")
        vendor = product.get("vendor", "")
        handle = product.get("handle", "")

        # Get the default variant (or first variant)
        variants = product.get("variants", [])
        if not variants:
            return None

        variant = variants[0]  # Use first variant

        # Price (Shopify stores price as string like "21.99")
        price_str = variant.get("price", "0")
        price = float(price_str)

        # Check if product is available
        available = variant.get("available", False)
        if not available:
            # Skip out-of-stock products
            return None

        # Compare price - Shopify stores compare_at_price for sale items
        compare_price_str = variant.get("compare_at_price")
        promo_price = None
        promo_text = None
        if compare_price_str:
            compare_price = float(compare_price_str)
            if compare_price > price:
                # This is a sale - compare_at_price is the original price
                promo_price = price
                price = compare_price  # Use original price as base price
                promo_text = "Sale"

        # Image URL
        image_url = None
        images = product.get("images", [])
        if images:
            image_url = images[0].get("src")

        # Product URL - use store-specific URL if available
        base_url = None
        for store in self.stores:
            if store["store_id"] == store_id:
                base_url = store["url"]
                break

        url = f"{base_url}/products/{handle}" if base_url else None

        # Parse volume and attributes from title
        volume = parse_volume(title)
        abv = extract_abv(title)
        inferred_brand = infer_brand(title)
        category = infer_category(title)

        # Create source_id with store context
        source_id = f"{store_id}_{product_id}" if store_id else product_id

        return {
            "chain": self.chain,
            "source_id": source_id,
            "name": title,
            "brand": inferred_brand or vendor,
            "category": category,
            "price_nzd": price,
            "promo_price_nzd": promo_price,
            "promo_text": promo_text,
            "promo_ends_at": None,  # Shopify doesn't provide end dates
            "is_member_only": False,
            "pack_count": volume.pack_count,
            "unit_volume_ml": volume.unit_volume_ml,
            "total_volume_ml": volume.total_volume_ml,
            "abv_percent": abv,
            "url": url,
            "image_url": image_url,
            "store_id": store_id,  # Include store context
            "store_name": store_name,
        }


__all__ = ["BlackBullScraper"]
