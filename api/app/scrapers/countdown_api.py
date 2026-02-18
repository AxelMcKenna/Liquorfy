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

    # Search terms for beer, cider, and wine only.
    # NZ supermarkets cannot sell spirits — only beer, cider, and wine.
    # Browse categories (dasFilter) return a tiny curated subset;
    # search returns the full catalog. Items are filtered by the
    # "Beer & Wine" department to exclude grocery noise.
    search_terms = [
        "beer", "lager", "ale", "cider",
        "sauvignon blanc", "pinot noir", "merlot", "chardonnay",
        "pinot gris", "rose wine", "sparkling wine", "champagne",
    ]

    # Woolworths department ID for alcohol
    _ALCOHOL_DEPT = "Beer & Wine"

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

    async def _fetch_search(
        self,
        term: str,
        page: int = 1,
        size: int = 120,
    ) -> dict:
        """
        Fetch products via search API.

        Args:
            term: Search query (e.g., "beer", "pinot noir")
            page: Page number (1-indexed)
            size: Results per page

        Returns:
            API response dict with products
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-NZ",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "referer": f"https://www.woolworths.co.nz/shop/search?search={quote(term)}",
            "x-requested-with": "OnlineShopping.WebApp",
            "cache-control": "no-cache",
            "pragma": "no-cache",
        }

        if self.cookies:
            cookie_string = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers["cookie"] = cookie_string

        url = (
            f"{self.api_url}?"
            f"target=search&"
            f"search={quote(term)}&"
            f"page={page}&"
            f"size={size}&"
            f"inStockProductsOnly=false"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
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
        # Extract basic info (use `or ""` to coerce None to empty string)
        sku = product_data.get("sku") or ""
        name = product_data.get("name") or ""
        brand = product_data.get("brand") or ""
        variety = product_data.get("variety") or ""

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

                # Batch upsert all products (broadcasts to all stores)
                try:
                    changed_items = await self._upsert_products_batch(
                        session, products, stores
                    )
                except Exception as e:
                    logger.error(f"Failed to persist products: {e}")
                    failed_items = total_items

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

    async def _validate_auth(self) -> bool:
        """Validate that cookies are still valid by making a lightweight API call."""
        try:
            response = await self._fetch_search("beer", page=1, size=1)
            items = response.get("products", {}).get("items", [])
            logger.info(f"Auth validation passed ({len(items)} test item(s))")
            return True
        except Exception as e:
            logger.warning(f"Auth validation failed: {e}")
            return False

    async def scrape(self) -> List[dict]:
        """
        Scrape all products from Countdown using search-based queries.

        The browse API returns a tiny subset; search returns the full catalog.
        Multiple search terms are used to cover all alcohol categories,
        with SKU-based dedup across terms.

        Returns:
            List of product dictionaries
        """
        if not self.cookies:
            self.cookies = await self._get_cookies()

        # Validate auth before full scrape
        if not await self._validate_auth():
            logger.warning("Stale cookies detected, refreshing...")
            self.cookies = await self._get_cookies()
            if not await self._validate_auth():
                logger.error("Auth validation failed after refresh")
                return []

        seen_skus: set[str] = set()
        all_products: List[dict] = []

        for term in self.search_terms:
            logger.info(f"Searching: '{term}'")
            page_num = 1

            while True:
                try:
                    response = await self._fetch_search(term, page=page_num)
                    items = response.get("products", {}).get("items", [])

                    if not items:
                        break

                    new_count = 0
                    for item_data in items:
                        try:
                            # Filter to Beer & Wine department only
                            depts = item_data.get("departments") or []
                            if not any(
                                d.get("name") == self._ALCOHOL_DEPT
                                for d in depts
                            ):
                                continue

                            sku = str(item_data.get("sku") or "")
                            if not sku or sku in seen_skus:
                                continue
                            seen_skus.add(sku)
                            product = self._parse_product(item_data)
                            all_products.append(product)
                            new_count += 1
                        except Exception as e:
                            logger.debug(f"Error parsing product: {e}")

                    logger.info(
                        f"  '{term}' page {page_num}: "
                        f"{len(items)} items, {new_count} new"
                    )

                    if len(items) < 120:
                        break

                    page_num += 1
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error searching '{term}' page {page_num}: {e}")
                    break

            await asyncio.sleep(1)

        logger.info(
            f"Scraped {len(all_products)} unique products "
            f"from {len(seen_skus)} SKUs across {len(self.search_terms)} search terms"
        )
        return all_products


__all__ = ["CountdownAPIScraper"]
