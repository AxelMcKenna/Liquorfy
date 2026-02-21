"""
Liquor Centre scraper

Scrapes product data from Liquor Centre stores across New Zealand.
Liquor Centre uses store-specific subdomains (e.g., beerescourt.shop.liquor-centre.co.nz)
with per-store pricing.
"""
import asyncio
import json
import logging
import re
from contextlib import suppress
from pathlib import Path
from typing import AsyncIterator, List, Optional
from selectolax.parser import HTMLParser
from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from datetime import datetime
from sqlalchemy import select

from app.scrapers.base import Scraper
from app.db.models import Price, Product, Store
from app.db.session import get_async_session
from app.services.parser_utils import (
    parse_volume,
    extract_abv,
    infer_brand,
    infer_category,
)
from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
)
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)
STORE_SLUG_PATTERN = re.compile(r"https?://([a-z0-9-]+)\.shop\.liquor-centre\.co\.nz", re.IGNORECASE)


# Representative stores from different regions (subset of 90 total stores)
# Only stores with online shopping enabled are included
# Use for testing - for production, use scrape_all_stores=True to load all 90 stores
DEFAULT_STORES = [
    "beerescourt",  # Hamilton
    "greenhithe",  # Auckland North
    "milford",  # Auckland North Shore
    "st-lukes",  # Auckland Central
    "pakuranga",  # Auckland East
    "royal-oak",  # Auckland South
    "opawa",  # Christchurch
]


def load_all_stores() -> List[str]:
    """Load all Liquor Centre store slugs from JSON file."""
    try:
        current_dir = Path(__file__).parent
        data_file = current_dir.parent / "data" / "liquor_centre_stores.json"

        if not data_file.exists():
            logger.warning(f"Store list file not found: {data_file}")
            return DEFAULT_STORES

        with open(data_file, 'r') as f:
            stores = json.load(f)

        logger.info(f"Loaded {len(stores)} Liquor Centre stores from {data_file}")
        return stores
    except Exception as e:
        logger.error(f"Failed to load store list: {e}")
        return DEFAULT_STORES


class LiquorCentreScraper(Scraper):
    """
    Scraper for Liquor Centre stores.

    Uses Playwright for browser automation as the site is JavaScript-rendered.
    Scrapes multiple store locations with store-specific pricing.
    """

    chain = "liquor_centre"
    _sweep_per_store = True

    # Category URLs (relative to store subdomain)
    CATEGORIES = ["beer", "wine", "spirits", "cider", "rtds", "specials"]

    def __init__(self, chain: str = None, use_fixtures: bool = False, stores: List[str] = None, scrape_all_stores: bool = True):
        super().__init__(use_fixtures=use_fixtures)
        if chain:
            self.chain = chain
        self.use_fixtures = use_fixtures
        self._stores_explicit = bool(stores)
        self._scrape_all_stores = scrape_all_stores

        # Determine which stores to scrape
        if stores:
            # Custom store list provided
            self.stores = stores
        elif scrape_all_stores:
            # Load all stores from JSON file
            self.stores = load_all_stores()
        else:
            # Use default subset
            self.stores = DEFAULT_STORES

        logger.info(f"LiquorCentreScraper initialized with {len(self.stores)} stores")

    async def _load_store_slugs_from_db(self) -> List[str]:
        """Load Liquor Centre store slugs from DB store URLs/api_ids."""
        slugs: set[str] = set()

        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Store.url, Store.api_id).where(Store.chain == self.chain)
                )
                for url, api_id in result.all():
                    if url:
                        match = STORE_SLUG_PATTERN.search(url)
                        if match:
                            slugs.add(match.group(1).lower())
                            continue

                    # Fallback: some rows may have only api_id populated.
                    if api_id:
                        candidate = str(api_id).strip().lower()
                        if re.fullmatch(r"[a-z0-9-]+", candidate):
                            slugs.add(candidate)

        except Exception as e:
            logger.warning(f"Failed loading {self.chain} stores from DB, using fallback list: {e}")
            return []

        return sorted(slugs)

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Materialize streamed Liquor Centre pages into a list.

        Returns HTML pages as strings, each tagged with metadata for parsing.
        """
        pages: List[str] = []
        async for payload in self.stream_catalog_pages():
            pages.append(payload)
        logger.info(f"Fetched {len(pages)} total pages")
        return pages

    async def stream_catalog_pages(self) -> AsyncIterator[str]:
        """
        Yield Liquor Centre pages incrementally for page-level persistence.
        """
        if self.use_fixtures:
            fixture_pages = await self._fetch_from_fixtures()
            for payload in fixture_pages:
                yield payload
            return

        # For production runs, treat DB as source of truth and fallback to JSON/bootstrap list.
        if not self._stores_explicit and self._scrape_all_stores:
            db_stores = await self._load_store_slugs_from_db()
            if db_stores:
                self.stores = db_stores
                logger.info(f"Loaded {len(self.stores)} Liquor Centre stores from database")
            else:
                logger.info(f"Using fallback Liquor Centre store list ({len(self.stores)} stores)")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # Block resources we don't need — significantly reduces page load time.
            _BLOCK_TYPES = {"image", "media", "font", "stylesheet"}
            async def _route_handler(route):
                """Ignore route errors that happen during shutdown/cancellation."""
                try:
                    if route.request.resource_type in _BLOCK_TYPES:
                        await route.abort()
                    else:
                        await route.continue_()
                except PlaywrightError as e:
                    if "Target page, context or browser has been closed" not in str(e):
                        raise
            await context.route(
                "**/*",
                _route_handler,
            )

            page = await context.new_page()

            try:
                for store_slug in self.stores:
                    logger.info(f"Scraping store: {store_slug}")
                    consecutive_failures = 0
                    max_failures = 3  # Skip store if 3 consecutive categories fail

                    for category in self.CATEGORIES:
                        # Skip remaining categories if store is unresponsive
                        if consecutive_failures >= max_failures:
                            logger.warning(
                                f"  Skipping remaining categories for {store_slug} (too many failures)"
                            )
                            break

                        logger.info(f"  Category: {category}")
                        category_success = False

                        # Start with page 1
                        page_num = 1
                        while True:
                            url = self._build_url(store_slug, category, page_num)

                            try:
                                # domcontentloaded is enough — we wait for .talker
                                # elements below, which is more precise than networkidle
                                # (networkidle waits for analytics/ads to settle, ~5-15s extra)
                                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                                try:
                                    await page.wait_for_selector(".talker", state="attached", timeout=8000)
                                except Exception:
                                    pass  # Page may be empty (no products in category)

                                html = await page.content()
                                tagged_html = self._tag_html(html, store_slug, category, page_num)
                                yield tagged_html
                                category_success = True

                                # Check for pagination
                                has_next = await self._has_next_page(page)
                                if not has_next:
                                    logger.info(f"    Scraped {page_num} page(s)")
                                    break

                                page_num += 1

                                # Safety limit
                                if page_num > 50:
                                    logger.warning(f"    Hit page limit at page {page_num}")
                                    break

                            except PlaywrightTimeout:
                                logger.error(f"    Timeout loading {url}")
                                break
                            except Exception as e:
                                logger.error(f"    Error loading {url}: {e}")
                                break

                        # Track consecutive failures
                        if category_success:
                            consecutive_failures = 0  # Reset on success
                        else:
                            consecutive_failures += 1

                        # Delay between categories
                        await asyncio.sleep(1.0)
            finally:
                # Route callbacks can still be in-flight when a scraper is cancelled.
                # Unroute first and ignore residual route errors during shutdown.
                with suppress(Exception):
                    await context.unroute_all(behavior="ignoreErrors")
                with suppress(Exception):
                    await page.close()
                with suppress(Exception):
                    await context.close()
                with suppress(Exception):
                    await browser.close()

    async def parse_products(self, payload: str) -> List[dict]:
        """
        Parse products from a single HTML page.

        Args:
            payload: HTML string tagged with metadata (store, category, page)

        Returns:
            List of product dictionaries
        """
        # Extract metadata from tagged HTML
        metadata, html = self._untag_html(payload)
        store_slug = metadata.get("store", "unknown")

        tree = HTMLParser(html)
        products = []

        # Find all product elements (.talker)
        talker_elements = tree.css(".talker")
        logger.info(f"Found {len(talker_elements)} products on page")

        for talker in talker_elements:
            try:
                product = self._parse_talker_element(talker, store_slug)
                if product:
                    products.append(product)
            except Exception as e:
                logger.error(f"Error parsing talker element: {e}", exc_info=True)
                continue

        return products

    def _parse_talker_element(self, talker, store_slug: str) -> Optional[dict]:
        """Parse a single product from a .talker element"""

        # Extract product ID from parent element
        product_id_attr = talker.attributes.get("id", "")
        source_id_match = re.search(r"line_([a-f0-9]+)", product_id_attr)
        if not source_id_match:
            logger.debug(f"Could not extract product ID from: {product_id_attr}")
            return None
        source_id = source_id_match.group(1)

        # Product name (contains name + size)
        name_elem = talker.css_first(".talker__name")
        if not name_elem:
            logger.debug("Missing product name")
            return None

        # Get main name (first span)
        name_spans = name_elem.css("span")
        if not name_spans:
            logger.debug("No name spans found")
            return None

        product_name = name_spans[0].text(strip=True)
        if not product_name:
            logger.debug("Empty product name")
            return None

        # Get size from second span (.talker__name__size)
        size_text = ""
        size_elem = name_elem.css_first(".talker__name__size")
        if size_elem:
            size_text = size_elem.text(strip=True)
            # Combine name with size for full product name
            full_name = f"{product_name} {size_text}".strip()
        else:
            full_name = product_name

        # Price
        price_elem = talker.css_first(".price__sell")
        if not price_elem:
            logger.debug(f"Missing price for {full_name}")
            return None

        price_text = price_elem.text(strip=True).replace("$", "").replace(",", "")
        try:
            price_nzd = float(price_text)
        except (ValueError, TypeError):
            logger.debug(f"Invalid price: {price_text}")
            return None

        # Product URL
        url = None
        link_elem = talker.css_first("a[href]")
        if link_elem:
            href = link_elem.attributes.get("href", "")
            if href and not href.startswith("http"):
                url = f"https://{store_slug}.shop.liquor-centre.co.nz{href}"
            elif href:
                url = href

        # Image URL
        image_url = None
        img_elem = talker.css_first("img")
        if img_elem:
            image_url = img_elem.attributes.get("src") or img_elem.attributes.get("data-src")

        # Use srcset from <source> if available (higher quality WebP)
        source_elem = talker.css_first("source[type='image/webp']")
        if source_elem:
            srcset = source_elem.attributes.get("srcset")
            if srcset:
                image_url = srcset.split()[0]  # Take first URL from srcset

        # Filter out placeholder images - set to NULL if it's a placeholder
        if image_url and "no_image" in image_url:
            image_url = None

        # Parse volume information from size text and name
        volume_info = parse_volume(size_text) or parse_volume(full_name)
        pack_count = volume_info.pack_count if volume_info else None
        unit_volume_ml = volume_info.unit_volume_ml if volume_info else None
        total_volume_ml = volume_info.total_volume_ml if volume_info else None

        # Extract ABV
        abv_percent = extract_abv(full_name) or extract_abv(size_text)

        # Infer brand and category
        brand = infer_brand(full_name)
        category = infer_category(full_name)

        # Extract promotional pricing
        promo_price = None
        promo_text = None
        promo_ends_at = None
        is_member_only = False

        # Check if product is on special by examining talker classes
        talker_classes = talker.attributes.get("class", "")
        is_special = "talker--Special" in talker_classes or "talker--Discount" in talker_classes

        if is_special:
            # Look for promotional sticker/badge
            sticker_label = talker.css_first(".talker__sticker__label")
            if sticker_label:
                badge_text = sticker_label.text(strip=True)
                if badge_text:
                    promo_text = badge_text[:255]

                    # Check for multi-buy deals in badge text
                    multi_buy = parse_multi_buy_deal(badge_text)
                    if multi_buy:
                        if multi_buy.get('unit_price'):
                            # Multi-buy with unit price calculation
                            promo_price = multi_buy['unit_price']
                        promo_text = multi_buy['deal_text'][:255]
                    else:
                        # Regular special - price shown is the promo price
                        # Since Liquor Centre doesn't show "was" price, we set promo_price
                        # to indicate it's on special
                        promo_price = price_nzd

                    # Parse promotional end date if present
                    promo_ends_at = parse_promo_end_date(badge_text)

                    # Check if member-only
                    is_member_only = detect_member_only(badge_text)
            else:
                # Has special class but no sticker text - still mark as special
                promo_price = price_nzd
                promo_text = "Special"[:255]

        # Look for additional promotional badges/text in other locations
        if not promo_text:
            # Check for any other promo elements
            promo_badge = (
                talker.css_first('[class*="promo"]') or
                talker.css_first('[class*="deal"]') or
                talker.css_first('[class*="save"]') or
                talker.css_first('[class*="offer"]')
            )
            if promo_badge:
                badge_text = promo_badge.text(strip=True)
                if badge_text:
                    promo_text = badge_text[:255]

                    # Try to extract promo price
                    extracted_price = parse_promo_price(badge_text)
                    if extracted_price and extracted_price < price_nzd:
                        promo_price = extracted_price

                    # Check for multi-buy deals
                    multi_buy = parse_multi_buy_deal(badge_text)
                    if multi_buy:
                        if multi_buy.get('unit_price'):
                            promo_price = multi_buy['unit_price']
                        promo_text = multi_buy['deal_text'][:255]

                    # Parse dates and member-only
                    promo_ends_at = parse_promo_end_date(badge_text)
                    is_member_only = detect_member_only(badge_text)

        product = {
            "chain": self.chain,
            "source_id": source_id,
            "name": full_name,
            "brand": brand,
            "category": category,
            "price_nzd": price_nzd,
            "promo_price_nzd": promo_price,
            "promo_text": promo_text,
            "promo_ends_at": promo_ends_at,
            "is_member_only": is_member_only,
            "pack_count": pack_count,
            "unit_volume_ml": unit_volume_ml,
            "total_volume_ml": total_volume_ml,
            "abv_percent": abv_percent,
            "url": url,
            "image_url": image_url,
            "store_identifier": store_slug,  # Store this for multi-store support
        }

        return product

    def _build_url(self, store_slug: str, category: str, page: int = 1) -> str:
        """Build category URL for a specific store"""
        base_url = f"https://{store_slug}.shop.liquor-centre.co.nz/category/{category}"
        if page > 1:
            return f"{base_url}?page={page}"
        return base_url

    async def _has_next_page(self, page) -> bool:
        """Check if there's a next page available"""
        try:
            # Look for "Next" link with rel="next"
            next_link = await page.locator('a[rel="next"]').count()
            return next_link > 0
        except Exception as e:
            logger.debug(f"Error checking pagination: {e}")
            return False

    def _tag_html(self, html: str, store: str, category: str, page: int) -> str:
        """Tag HTML with metadata for parsing"""
        metadata = f"<!--METADATA:store={store},category={category},page={page}-->"
        return metadata + html

    def _untag_html(self, tagged_html: str) -> tuple:
        """Extract metadata and HTML from tagged content"""
        metadata = {}
        html = tagged_html

        if tagged_html.startswith("<!--METADATA:"):
            end_idx = tagged_html.find("-->")
            if end_idx != -1:
                metadata_str = tagged_html[13:end_idx]  # Skip "<!--METADATA:"
                html = tagged_html[end_idx + 3:]  # Skip "-->"

                # Parse metadata
                for pair in metadata_str.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        metadata[key] = value

        return metadata, html

    async def _fetch_from_fixtures(self) -> List[str]:
        """Load HTML from fixture files for testing"""
        import os

        fixture_path = "app/scrapers/fixtures/liquor_centre.html"
        if not os.path.exists(fixture_path):
            logger.warning(f"Fixture not found: {fixture_path}")
            return []

        with open(fixture_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Tag as a single test page
        tagged = self._tag_html(html, "test-store", "beer", 1)
        return [tagged]

    async def _upsert_products_batch(
        self, session, products_data: list, stores: list
    ) -> int:
        """
        Batch upsert optimized for Liquor Centre's store-specific pricing.
        Only creates/updates prices for the specific stores that were scraped.
        """
        if not products_data:
            return 0

        now = datetime.utcnow()
        changed_count = 0

        # Group products by store_identifier
        products_by_store = {}
        for product_data in products_data:
            store_id = product_data.get("store_identifier", "unknown")
            if store_id not in products_by_store:
                products_by_store[store_id] = []
            products_by_store[store_id].append(product_data)

        # Process each store's products
        for store_identifier, store_products in products_by_store.items():
            # Find or create the store
            target_store = None
            for store in stores:
                if store.url and store_identifier in store.url:
                    target_store = store
                    break
                store_name_slug = store.name.lower().replace(" ", "-").replace("liquor-centre-", "").replace("liquorcentre", "")
                if store_identifier in store_name_slug or store_name_slug in store_identifier:
                    target_store = store
                    break

            if not target_store:
                # Check database
                store_url = f"https://{store_identifier}.shop.liquor-centre.co.nz"
                existing_store = await session.execute(
                    select(Store).where(
                        Store.chain == self.chain,
                        Store.url == store_url
                    )
                )
                target_store = existing_store.scalar_one_or_none()

                if not target_store:
                    # Create new store
                    logger.info(f"Creating new store for identifier: {store_identifier}")
                    target_store = Store(
                        name=f"Liquor Centre {store_identifier.title().replace('-', ' ')}",
                        chain=self.chain,
                        lat=0.0,
                        lon=0.0,
                        url=store_url,
                    )
                    session.add(target_store)
                    await session.flush()

            # Bulk upsert products
            product_values = []
            for product_data in store_products:
                product_values.append({
                    "chain": product_data["chain"],
                    "source_product_id": product_data["source_id"],
                    "name": product_data["name"],
                    "brand": product_data.get("brand"),
                    "category": product_data.get("category"),
                    "abv_percent": product_data.get("abv_percent"),
                    "pack_count": product_data.get("pack_count"),
                    "unit_volume_ml": product_data.get("unit_volume_ml"),
                    "total_volume_ml": product_data.get("total_volume_ml"),
                    "image_url": product_data.get("image_url"),
                    "product_url": product_data.get("url"),
                })

            stmt = insert(Product).values(product_values)
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
            await session.execute(stmt)
            await session.flush()

            # Get product IDs
            source_ids = [p["source_id"] for p in store_products]
            result = await session.execute(
                select(Product.id, Product.source_product_id).where(
                    Product.chain == self.chain,
                    Product.source_product_id.in_(source_ids)
                )
            )
            product_id_map = {row.source_product_id: row.id for row in result}

            # Get existing prices for THIS STORE ONLY
            product_ids = list(product_id_map.values())
            existing_prices_result = await session.execute(
                select(Price).where(
                    Price.product_id.in_(product_ids),
                    Price.store_id == target_store.id
                )
            )
            existing_prices = existing_prices_result.scalars().all()
            existing_prices_map = {price.product_id: price for price in existing_prices}

            # Bulk upsert prices for this store
            price_values = []
            for product_data in store_products:
                product_id = product_id_map.get(product_data["source_id"])
                if not product_id:
                    continue

                existing_price = existing_prices_map.get(product_id)

                # Check if price changed
                price_changed = False
                if existing_price:
                    if (
                        existing_price.price_nzd != product_data["price_nzd"]
                        or existing_price.promo_price_nzd != product_data.get("promo_price_nzd")
                    ):
                        price_changed = True
                        changed_count += 1

                price_values.append({
                    "product_id": product_id,
                    "store_id": target_store.id,
                    "price_nzd": product_data["price_nzd"],
                    "promo_price_nzd": product_data.get("promo_price_nzd"),
                    "promo_text": product_data.get("promo_text"),
                    "promo_ends_at": product_data.get("promo_ends_at"),
                    "is_member_only": product_data.get("is_member_only", False),
                    "last_seen_at": now,
                    "price_last_changed_at": now if (price_changed or not existing_price) else (existing_price.price_last_changed_at if existing_price else now),
                })

                if not existing_price:
                    changed_count += 1

            # Bulk insert prices
            if price_values:
                stmt = insert(Price).values(price_values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["product_id", "store_id"],
                    set_={
                        "price_nzd": stmt.excluded.price_nzd,
                        "promo_price_nzd": stmt.excluded.promo_price_nzd,
                        "promo_text": stmt.excluded.promo_text,
                        "promo_ends_at": stmt.excluded.promo_ends_at,
                        "is_member_only": stmt.excluded.is_member_only,
                        "last_seen_at": stmt.excluded.last_seen_at,
                        "price_last_changed_at": stmt.excluded.price_last_changed_at,
                    },
                )
                await session.execute(stmt)

            # Sweep stale promos for this specific store
            if self._run_started_at and target_store:
                try:
                    from app.services.freshness import sweep_store_promos

                    await sweep_store_promos(session, target_store.id, self._run_started_at)
                except Exception as e:
                    logger.warning(f"Per-store promo sweep failed for store={store_identifier}: {e}")

        return changed_count

    async def _upsert_product_and_prices(
        self, session, product_data: dict, stores: list
    ) -> bool:
        """
        Override base method to handle store-specific pricing.

        Liquor Centre has different prices at different stores, so we only
        create/update the price for the specific store that was scraped.
        """
        now = datetime.utcnow()
        changed = False

        # Find the specific store for this product
        store_identifier = product_data.get("store_identifier")
        if not store_identifier:
            logger.warning(f"Product {product_data.get('name')} missing store_identifier")
            # Fall back to base implementation
            return await super()._upsert_product_and_prices(session, product_data, stores)

        # Find matching store by URL or name
        target_store = None
        for store in stores:
            # Match by URL containing the store slug
            if store.url and store_identifier in store.url:
                target_store = store
                break
            # Match by name (fallback)
            store_name_slug = store.name.lower().replace(" ", "-").replace("liquor-centre-", "").replace("liquorcentre", "")
            if store_identifier in store_name_slug or store_name_slug in store_identifier:
                target_store = store
                break

        if not target_store:
            # If no matching store found in the stores list, check database first
            store_url = f"https://{store_identifier}.shop.liquor-centre.co.nz"

            # Check if store already exists in database
            existing_store = await session.execute(
                select(Store).where(
                    Store.chain == self.chain,
                    Store.url == store_url
                )
            )
            target_store = existing_store.scalar_one_or_none()

            if not target_store:
                # Truly doesn't exist - create it
                logger.info(f"Creating new store for identifier: {store_identifier}")
                target_store = Store(
                    name=f"Liquor Centre {store_identifier.title().replace('-', ' ')}",
                    chain=self.chain,
                    lat=0.0,  # TODO: Could fetch coordinates if needed
                    lon=0.0,
                    url=store_url,
                )
                session.add(target_store)
                await session.flush()
            else:
                logger.debug(f"Found existing store in database: {target_store.name}")

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

        # Create/update price for THIS SPECIFIC STORE ONLY
        existing_price = await session.execute(
            select(Price).where(
                Price.product_id == product_id,
                Price.store_id == target_store.id
            )
        )
        existing = existing_price.scalar_one_or_none()

        price_changed = False
        if existing:
            # Check if price has changed
            if (
                existing.price_nzd != product_data["price_nzd"]
                or existing.promo_price_nzd != product_data.get("promo_price_nzd")
            ):
                price_changed = True
                changed = True

            # Update existing price
            existing.price_nzd = product_data["price_nzd"]
            existing.promo_price_nzd = product_data.get("promo_price_nzd")
            existing.promo_text = product_data.get("promo_text")
            existing.promo_ends_at = product_data.get("promo_ends_at")
            existing.last_seen_at = now
            if price_changed:
                existing.price_last_changed_at = now
        else:
            # Create new price for this store
            changed = True
            price = Price(
                product_id=product_id,
                store_id=target_store.id,
                price_nzd=product_data["price_nzd"],
                promo_price_nzd=product_data.get("promo_price_nzd"),
                promo_text=product_data.get("promo_text"),
                promo_ends_at=product_data.get("promo_ends_at"),
                last_seen_at=now,
                price_last_changed_at=now,
            )
            session.add(price)

        return changed
