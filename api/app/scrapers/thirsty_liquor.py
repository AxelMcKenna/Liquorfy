"""
Thirsty Liquor scraper

Scrapes product data from Thirsty Liquor NZ using Shopify's JSON API.
Thirsty Liquor is a franchise with 130+ stores nationwide, using chain-wide pricing.
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


class ThirstyLiquorScraper(Scraper):
    """
    Scraper for Thirsty Liquor using Shopify API.

    Thirsty Liquor operates 130+ stores nationwide with chain-wide pricing.
    Uses Shopify's standard products.json API endpoint.
    """

    chain = "thirsty_liquor"
    base_url = "https://thirstyliquor.co.nz"

    # Collections to scrape (Shopify collection handles)
    collections = [
        "beer",
        "wine",
        "spirits",
        "cider",
        "rtds",
    ]

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Fetch all products from Thirsty Liquor's Shopify API.
        Returns JSON responses as strings for parsing.
        """
        pages = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for collection in self.collections:
                logger.info(f"Fetching collection: {collection}")

                page_num = 1
                while True:
                    url = f"{self.base_url}/collections/{collection}/products.json"
                    params = {"limit": 250, "page": page_num}

                    try:
                        response = await client.get(url, params=params)
                        response.raise_for_status()

                        data = response.json()
                        products = data.get("products", [])

                        if not products:
                            # No more products in this collection
                            break

                        logger.info(f"  Page {page_num}: {len(products)} products")
                        pages.append(response.text)

                        # If we got fewer than 250 products, we're on the last page
                        if len(products) < 250:
                            break

                        page_num += 1
                        await asyncio.sleep(0.5)  # Rate limiting

                    except httpx.HTTPError as e:
                        logger.error(f"Error fetching {collection} page {page_num}: {e}")
                        break

                # Delay between collections
                await asyncio.sleep(1.0)

        logger.info(f"Fetched {len(pages)} pages total")
        return pages

    async def parse_products(self, payload: str) -> List[dict]:
        """
        Parse products from Shopify JSON response.

        Args:
            payload: JSON string from Shopify API

        Returns:
            List of standardized product dictionaries
        """
        import json

        data = json.loads(payload)
        products = data.get("products", [])

        parsed_products = []

        for product in products:
            try:
                parsed = self._parse_product(product)
                if parsed:
                    parsed_products.append(parsed)
            except Exception as e:
                logger.error(f"Error parsing product {product.get('id')}: {e}")

        return parsed_products

    def _parse_product(self, product: dict) -> dict:
        """
        Parse a single Shopify product into our standard format.

        Args:
            product: Shopify product dict

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

        # Enrich promo info from product tags (comma-separated string)
        tags_raw = product.get("tags", "")
        if isinstance(tags_raw, list):
            tags = [t.strip().lower() for t in tags_raw]
        else:
            tags = [t.strip().lower() for t in str(tags_raw).split(",") if t.strip()]

        _SALE_TAGS = {"sale", "special", "on-sale", "promotion", "clearance", "reduced"}
        matched_tags = _SALE_TAGS & set(tags)
        if matched_tags and not promo_text:
            promo_text = matched_tags.pop().title()
            if not promo_price:
                promo_price = price  # Flag as promotional even without compare_at

        # Image URL
        image_url = None
        images = product.get("images", [])
        if images:
            image_url = images[0].get("src")

        # Product URL
        url = f"{self.base_url}/products/{handle}"

        # Parse volume and attributes from title
        volume = parse_volume(title)
        abv = extract_abv(title)
        inferred_brand = infer_brand(title)
        category = infer_category(title)

        return {
            "chain": self.chain,
            "source_id": product_id,
            "name": title,
            "brand": inferred_brand or vendor,
            "category": category,
            "price_nzd": price,
            "promo_price_nzd": promo_price,
            "promo_text": promo_text,
            "promo_ends_at": None,  # Shopify doesn't provide end dates
            "is_member_only": False,  # Thirsty Liquor doesn't have member pricing
            "pack_count": volume.pack_count,
            "unit_volume_ml": volume.unit_volume_ml,
            "total_volume_ml": volume.total_volume_ml,
            "abv_percent": abv,
            "url": url,
            "image_url": image_url,
        }


__all__ = ["ThirstyLiquorScraper"]
