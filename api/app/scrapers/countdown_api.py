"""
Countdown API-based scraper using Woolworths NZ API.
Much faster and more reliable than HTML scraping.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List
from urllib.parse import quote

import httpx
from sqlalchemy import select

from app.db.models import IngestionRun, Store
from app.db.session import async_transaction
from app.scrapers.base import Scraper
from app.scrapers.api_auth_base import APIAuthBase
from app.services.parser_utils import infer_brand

logger = logging.getLogger(__name__)


class CountdownAPIScraper(Scraper, APIAuthBase):
    """API-based scraper for Countdown NZ using Woolworths API."""

    chain = "countdown"
    site_url = "https://www.countdown.co.nz"
    api_domain = ""  # Countdown doesn't need token, just cookies

    # API endpoint
    api_url = "https://www.woolworths.co.nz/api/v1/products"

    # Category definitions (Department, Aisle pairs)
    categories = [
        ("beer-cider-wine", "beer"),
        ("beer-cider-wine", "cider"),
        ("beer-cider-wine", "red-wine"),
        ("beer-cider-wine", "white-wine"),
        ("beer-cider-wine", "rose-wine"),
        ("beer-cider-wine", "sparkling-wine"),
        ("beer-cider-wine", "premix-rtd"),
    ]

    def __init__(self):
        Scraper.__init__(self)
        APIAuthBase.__init__(self)

    async def _get_cookies(self) -> dict:
        """Get session cookies via browser authentication."""
        await self._get_auth_via_browser(
            capture_token=False,
            capture_cookies=True,
            headless=False,
            wait_time=5.0
        )
        return self.cookies

    async def _fetch_category(
        self,
        department: str,
        aisle: str,
        size: int = 48  # Match browser default
    ) -> dict:
        """
        Fetch products for a specific category using the API.

        Args:
            department: Department filter (e.g., "beer-cider-wine")
            aisle: Aisle filter (e.g., "beer")
            size: Number of products to fetch

        Returns:
            API response dict with products
        """
        # Build dasFilter parameters
        filters = [
            f"Department;;{department};false",
            f"Aisle;;{aisle};false",
        ]

        params = {
            "target": "browse",
            "inStockProductsOnly": "false",
            "size": str(size),
        }

        # Add dasFilter params
        for f in filters:
            params.setdefault("dasFilter", []).append(f) if isinstance(params.get("dasFilter"), list) else None

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-NZ",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "referer": f"https://www.woolworths.co.nz/shop/browse/{department}/{aisle}",
            "x-requested-with": "OnlineShopping.WebApp",
            "cache-control": "no-cache",
            "pragma": "no-cache",
        }

        # Add cookies if we have them
        if self.cookies:
            cookie_string = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers["cookie"] = cookie_string

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Manually build URL with multiple dasFilter params (order matters!)
            # Put dasFilter params first, then other params
            url = self.api_url + "?"

            # Add dasFilter params first
            for f in filters:
                url += f"dasFilter={quote(f)}&"

            # Then add other params
            for key, value in params.items():
                url += f"{key}={quote(str(value))}&"

            url = url.rstrip("&")

            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _parse_product(self, product_data: dict) -> dict:
        """
        Parse a product from API response into our standard format.

        Args:
            product_data: Product dict from API

        Returns:
            Standardized product dict
        """
        # Extract basic info
        sku = product_data.get("sku", "")
        name = product_data.get("name", "")
        brand = product_data.get("brand", "")
        variety = product_data.get("variety", "")

        # Full product name
        full_name = f"{brand} {variety} {name}".strip()

        # Price info
        price_info = product_data.get("price", {})
        price = price_info.get("originalPrice", 0)
        sale_price = price_info.get("salePrice")
        is_special = price_info.get("isSpecial", False)

        promo_price = None
        promo_text = None
        if is_special and sale_price and sale_price < price:
            promo_price = sale_price
            save_price = price_info.get("savePrice", 0)
            if save_price:
                promo_text = f"Save ${save_price:.2f}"[:255]

        # Check for club/member pricing
        is_member_only = price_info.get("isClubPrice", False)

        # Image URL
        images = product_data.get("images", {})
        image_url = images.get("big") or images.get("small")

        # Product URL
        slug = product_data.get("slug", "")
        url = f"https://www.countdown.co.nz/shop/productdetails?stockcode={sku}&name={slug}" if slug else None

        # Parse volume from size info
        size_info = product_data.get("size", {})
        volume_size = size_info.get("volumeSize", "")  # e.g., "24 x 330mL"

        # Use standardized product dict builder
        inferred_brand = infer_brand(full_name)

        return self.build_product_dict(
            source_id=sku,
            name=full_name,
            price_nzd=price,
            promo_price_nzd=promo_price,
            promo_text=promo_text,
            promo_ends_at=None,
            is_member_only=is_member_only,
            url=url,
            image_url=image_url,
            brand=inferred_brand or brand,
        )

    async def fetch_catalog_pages(self) -> List[str]:
        """Not used for API-based scraper."""
        return []

    async def parse_products(self, payload: str) -> List[dict]:
        """Not used for API-based scraper."""
        return []

    async def run(self) -> IngestionRun:
        """Run the scraper and persist data to database."""
        run = IngestionRun(
            chain=self.chain,
            status="running",
            started_at=datetime.utcnow(),
        )

        async with async_transaction() as session:
            session.add(run)
            await session.flush()

        try:
            # Scrape products via API
            products = await self.scrape()
            total_items = len(products)
            changed_items = 0
            failed_items = 0

            async with async_transaction() as session:
                # Get all stores for this chain
                result = await session.execute(
                    select(Store).where(Store.chain == self.chain)
                )
                stores = result.scalars().all()

                if not stores:
                    logger.warning(f"No stores found for chain {self.chain}")
                    stores = []

                # Upsert all products
                for product_data in products:
                    try:
                        changed = await self._upsert_product_and_prices(
                            session, product_data, stores
                        )
                        if changed:
                            changed_items += 1
                    except Exception as e:
                        logger.error(f"Failed to persist product {product_data.get('name')}: {e}")
                        failed_items += 1

            # Update ingestion run with results
            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = "completed"
                run.finished_at = datetime.utcnow()
                run.items_total = total_items
                run.items_changed = changed_items
                run.items_failed = failed_items

            logger.info(
                f"Scraper completed: {total_items} items, "
                f"{changed_items} changed, {failed_items} failed"
            )
            return run

        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            # Update run status to failed
            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.finished_at = datetime.utcnow()
            raise

    async def scrape(self) -> List[dict]:
        """
        Scrape all products from Countdown using Woolworths API.

        Returns:
            List of product dictionaries
        """
        # Get cookies first
        if not self.cookies:
            self.cookies = await self._get_cookies()

        all_products: List[dict] = []

        # Scrape each category
        for department, aisle in self.categories:
            logger.info(f"Scraping category: {department} > {aisle}")

            try:
                # Fetch products (API returns all with size parameter)
                response = await self._fetch_category(department, aisle)

                products_data = response.get("products", {}).get("items", [])
                total_count = response.get("products", {}).get("totalCount", len(products_data))

                logger.info(f"Found {len(products_data)}/{total_count} products in {aisle}")

                # Parse products
                for product_data in products_data:
                    try:
                        product = self._parse_product(product_data)
                        all_products.append(product)
                    except Exception as e:
                        logger.error(f"Error parsing product: {e}")

                # Small delay between categories
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error scraping category {aisle}: {e}")
                continue

        logger.info(f"Successfully scraped {len(all_products)} products from Countdown")
        return all_products


__all__ = ["CountdownAPIScraper"]
