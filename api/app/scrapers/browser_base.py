"""
Base browser scraper using Playwright for JavaScript-heavy sites.
Includes respectful rate limiting and error handling.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import IngestionRun, Price, Product, Store
from app.db.session import async_transaction
from app.scrapers.base import Scraper

try:
    from undetected_playwright.tarnished import Malenia
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Rate limiting configuration (respectful scraping)
DELAY_BETWEEN_REQUESTS = 1.0  # seconds between page requests
DELAY_BETWEEN_CATEGORIES = 2.5  # seconds between different categories
MAX_RETRIES = 3  # max retries for failed requests
RETRY_DELAY = 2.0  # initial retry delay (doubles each retry)
PAGE_TIMEOUT = 30000  # page load timeout in ms


class BrowserScraper(Scraper):
    """Base class for browser-based scrapers using Playwright."""

    chain: str = "unknown"
    catalog_urls: List[str] = []

    def __init__(self, headless: bool = True, use_fixtures: bool = False) -> None:
        """
        Initialize browser scraper.

        Args:
            headless: Run browser in headless mode (no UI)
            use_fixtures: Use fixtures instead of live scraping (from parent Scraper)
        """
        super().__init__(use_fixtures=use_fixtures)
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()

    async def start_browser(self) -> None:
        """Start the browser and create a context."""
        logger.info(f"Starting browser for {self.chain} scraper (headless={self.headless})")
        self.playwright = await async_playwright().start()

        # Launch with anti-detection args
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process"
        ]

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )

        # Create context with realistic user agent
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-NZ",
            timezone_id="Pacific/Auckland",
        )

        # Apply stealth if available
        if STEALTH_AVAILABLE:
            try:
                await Malenia.apply_stealth(self.context)
                logger.info("✓ Stealth mode enabled")
            except Exception as e:
                logger.warning(f"Failed to apply stealth: {e}")

        # Set default timeout
        self.context.set_default_timeout(PAGE_TIMEOUT)

    async def close_browser(self) -> None:
        """Close the browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"Browser closed for {self.chain}")

    async def _fetch_page_with_retry(
        self, url: str, retry_count: int = 0
    ) -> str:
        """
        Fetch page HTML with exponential backoff on errors.

        Args:
            url: URL to fetch
            retry_count: Current retry attempt

        Returns:
            Page HTML content
        """
        try:
            page = await self.context.new_page()
            try:
                logger.debug(f"Navigating to {url}")
                # Use 'domcontentloaded' - faster than 'load' and avoids timeouts from
                # slow analytics/tracking scripts. Subclass wait_for_content() handles
                # waiting for actual product elements.
                await page.goto(url, wait_until="domcontentloaded")

                # Wait for content to load (can be overridden by subclasses)
                await self.wait_for_content(page)

                html = await page.content()
                return html
            finally:
                await page.close()

        except Exception as e:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
                logger.warning(
                    f"  Request failed, retrying in {delay}s... "
                    f"({retry_count + 1}/{MAX_RETRIES}): {e}"
                )
                await asyncio.sleep(delay)
                return await self._fetch_page_with_retry(url, retry_count + 1)
            else:
                logger.error(f"  Failed after {MAX_RETRIES} retries: {e}")
                raise

    async def wait_for_content(self, page: Page) -> None:
        """
        Wait for dynamic content to load.
        Override this in subclasses to wait for specific selectors.

        Args:
            page: Playwright page instance
        """
        # Default: wait a moment for JS to execute
        await asyncio.sleep(1)

    @staticmethod
    def extract_image_url(
        node,
        base_url: str,
        selectors: Optional[List[str]] = None,
        attributes: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Extract and normalize image URL from HTML node.

        Args:
            node: HTML node (from selectolax)
            base_url: Base URL for resolving relative URLs
            selectors: CSS selectors to try (default: ['img'])
            attributes: Image attributes to check (default: ['src', 'data-src', 'data-lazy-src'])

        Returns:
            Absolute image URL or None
        """
        from urllib.parse import urljoin

        if selectors is None:
            selectors = ['img']
        if attributes is None:
            attributes = ['src', 'data-src', 'data-lazy-src']

        for selector in selectors:
            img_elem = node.css_first(selector)
            if img_elem:
                for attr in attributes:
                    image_url = img_elem.attributes.get(attr)
                    if image_url:
                        # Convert relative URLs to absolute
                        if not image_url.startswith('http'):
                            image_url = urljoin(base_url, image_url)
                        return image_url

        return None

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Fetch catalog pages with pagination and rate limiting.

        Returns:
            List of HTML strings
        """
        if not self.browser:
            await self.start_browser()

        logger.info(
            f"Fetching live data from {len(self.catalog_urls)} category URLs"
        )
        logger.info(
            f"Rate limiting: {DELAY_BETWEEN_REQUESTS}s between requests, "
            f"{DELAY_BETWEEN_CATEGORIES}s between categories"
        )
        pages = []

        for category_idx, base_url in enumerate(self.catalog_urls):
            try:
                # Add delay between categories (but not before the first one)
                if category_idx > 0:
                    logger.info(
                        f"Waiting {DELAY_BETWEEN_CATEGORIES}s before next category..."
                    )
                    await asyncio.sleep(DELAY_BETWEEN_CATEGORIES)

                # Fetch first page to determine total pages
                logger.info(f"Fetching {base_url}")
                first_page = await self._fetch_page_with_retry(base_url)
                pages.append(first_page)

                # Check for pagination
                total_pages = await self.extract_total_pages(first_page)

                if total_pages > 1:
                    logger.info(
                        f"  Found {total_pages} pages, fetching remaining pages..."
                    )

                    # Fetch remaining pages with delays
                    for page_num in range(2, total_pages + 1):
                        # Rate limiting: delay between requests
                        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

                        page_url = self.get_page_url(base_url, page_num)
                        try:
                            page_html = await self._fetch_page_with_retry(page_url)
                            pages.append(page_html)
                            logger.info(f"  Fetched page {page_num}/{total_pages}")
                        except Exception as e:
                            logger.error(
                                f"  Failed to fetch page {page_num} after retries: {e}"
                            )
                            continue
                else:
                    logger.info(f"  Only 1 page found")

            except Exception as e:
                logger.error(f"Failed to fetch {base_url} after retries: {e}")
                continue

        logger.info(f"Fetched total of {len(pages)} pages across all categories")
        return pages

    @abstractmethod
    async def extract_total_pages(self, html: str) -> int:
        """
        Extract total number of pages from HTML.
        Must be implemented by subclasses.

        Args:
            html: Page HTML content

        Returns:
            Total number of pages
        """
        pass

    @abstractmethod
    def get_page_url(self, base_url: str, page_num: int) -> str:
        """
        Construct URL for a specific page number.
        Must be implemented by subclasses.

        Args:
            base_url: Base category URL
            page_num: Page number

        Returns:
            URL for the specific page
        """
        pass

    @abstractmethod
    async def parse_products(self, payload: str) -> List[dict]:
        """
        Parse products from HTML.
        Must be implemented by subclasses.

        Args:
            payload: Page HTML content

        Returns:
            List of product dictionaries
        """
        pass

    async def run(self) -> IngestionRun:
        """Run the scraper and persist data to database."""
        # Create ingestion run record
        run = IngestionRun(
            chain=self.chain,
            status="running",
            started_at=datetime.utcnow(),
        )

        async with async_transaction() as session:
            session.add(run)
            await session.flush()

        try:
            # Fetch and process catalog pages
            pages = await self.fetch_catalog_pages()
            total_items = 0
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

                for page in pages:
                    try:
                        products = await self.parse_products(page)
                        total_items += len(products)

                        # Batch process products for better performance
                        changed_count = await self._upsert_products_batch(
                            session, products, stores
                        )
                        changed_items += changed_count
                        # changed_count is DB row-level (product/store upserts),
                        # while total_items is product-level; do not derive failures
                        # from changed_count or it can go negative.

                    except Exception as e:
                        logger.error(f"Failed to parse page: {e}")
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
        finally:
            # Always close the browser
            await self.close_browser()

    async def _upsert_product_and_prices(
        self, session, product_data: dict, stores: List[Store]
    ) -> bool:
        """
        Upsert product and its prices.
        Returns True if any changes were made, False otherwise.
        """
        now = datetime.utcnow()
        changed = False

        # Upsert product
        stmt = insert(Product).values(
            chain=product_data["chain"],
            source_product_id=product_data["source_id"],
            name=product_data["name"],
            brand=product_data.get("brand"),
            category=product_data.get("category"),
            abv_percent=product_data.get("abv_percent"),
            pack_count=product_data.get("pack_count"),
            unit_volume_ml=product_data.get("unit_volume_ml"),
            total_volume_ml=product_data.get("total_volume_ml"),
            image_url=product_data.get("image_url"),
            product_url=product_data.get("url"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["chain", "source_product_id"],
            set_={
                "name": stmt.excluded.name,
                "brand": stmt.excluded.brand,
                "category": stmt.excluded.category,
                "abv_percent": stmt.excluded.abv_percent,
                "pack_count": stmt.excluded.pack_count,
                "unit_volume_ml": stmt.excluded.unit_volume_ml,
                "total_volume_ml": stmt.excluded.total_volume_ml,
                "image_url": stmt.excluded.image_url,
                "product_url": stmt.excluded.product_url,
                "updated_at": now,
            },
        )
        stmt = stmt.returning(Product.id)
        result = await session.execute(stmt)
        product_id = result.scalar_one()

        # Upsert prices for all stores
        price_data = {
            "currency": product_data.get("currency", "NZD"),
            "price_nzd": product_data["price_nzd"],
            "promo_price_nzd": product_data.get("promo_price_nzd"),
            "promo_text": product_data.get("promo_text"),
            "promo_ends_at": product_data.get("promo_ends_at"),
            "is_member_only": product_data.get("is_member_only", False),
            "last_seen_at": now,
        }

        for store in stores:
            # Check if price changed
            existing = await session.execute(
                select(Price).where(
                    Price.product_id == product_id, Price.store_id == store.id
                )
            )
            existing_price = existing.scalar_one_or_none()

            if existing_price:
                # Check if price actually changed
                if existing_price.price_nzd != price_data["price_nzd"]:
                    price_data["price_last_changed_at"] = now
                    changed = True
                else:
                    price_data["price_last_changed_at"] = existing_price.price_last_changed_at

            # Upsert price
            price_stmt = insert(Price).values(
                product_id=product_id,
                store_id=store.id,
                **price_data,
            )
            price_stmt = price_stmt.on_conflict_do_update(
                index_elements=["product_id", "store_id"],
                set_={
                    "currency": price_stmt.excluded.currency,
                    "price_nzd": price_stmt.excluded.price_nzd,
                    "promo_price_nzd": price_stmt.excluded.promo_price_nzd,
                    "promo_text": price_stmt.excluded.promo_text,
                    "promo_ends_at": price_stmt.excluded.promo_ends_at,
                    "is_member_only": price_stmt.excluded.is_member_only,
                    "last_seen_at": price_stmt.excluded.last_seen_at,
                    "price_last_changed_at": price_data.get("price_last_changed_at"),
                    "updated_at": now,
                },
            )
            await session.execute(price_stmt)

        return changed


__all__ = ["BrowserScraper"]
