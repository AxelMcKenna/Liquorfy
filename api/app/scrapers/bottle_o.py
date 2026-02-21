"""
The Bottle O scraper — per-store CityHive scraping with franchise fallback.

Individual Bottle O stores run on the CityHive platform (same as Liquor Centre)
at {slug}.shop.thebottleo.co.nz with per-store pricing.  Stores without an
online shop fall back to the franchise catalog at thebottleo.co.nz (GTM
dataLayer extraction).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from contextlib import suppress
from datetime import datetime
from typing import List, Optional

from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)
from selectolax.parser import HTMLParser
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

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

logger = logging.getLogger(__name__)

STORE_SLUG_PATTERN = re.compile(
    r"https?://([a-z0-9-]+)\.shop\.thebottleo\.co\.nz", re.IGNORECASE
)

# Rate limiting
DELAY_BETWEEN_CATEGORIES = 2.5
DELAY_BETWEEN_REQUESTS = 1.5

# Categories available on CityHive store sites
CATEGORIES = ["beer", "wine", "spirits", "cider", "rtds", "specials"]

# Franchise catalog URLs (for stores without online shops)
FRANCHISE_CATALOG_URLS = [
    "https://thebottleo.co.nz/search?q[]=category:beer&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:wine&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:spirits&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:rtd&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:cider&sort_by=top_products",
]

# Hardcoded fallback store slugs (representative subset)
DEFAULT_STORES = [
    "albany",
    "botany",
    "napier",
    "nelson",
    "tauranga",
]


class BottleOScraper(Scraper):
    """
    Scraper for The Bottle O NZ — CityHive per-store + franchise fallback.

    Per-store scraping mirrors the LiquorCentreScraper approach: navigate each
    store's CityHive subdomain, paginate categories, tag HTML with metadata,
    and parse .talker elements.

    Stores without an online shop receive prices from the franchise catalog
    (GTM dataLayer extraction on thebottleo.co.nz).
    """

    chain = "bottle_o"
    _sweep_per_store = True

    # Keep catalog_urls populated so registry tests pass
    catalog_urls = FRANCHISE_CATALOG_URLS

    def __init__(
        self,
        use_fixtures: bool = False,
        stores: Optional[List[str]] = None,
        scrape_all_stores: bool = True,
    ) -> None:
        super().__init__(use_fixtures=use_fixtures)
        self.use_fixtures = use_fixtures
        self._stores_explicit = bool(stores)
        self._scrape_all_stores = scrape_all_stores

        if stores:
            self.stores = stores
        else:
            self.stores = DEFAULT_STORES

        logger.info(f"BottleOScraper initialised with {len(self.stores)} stores")

    # ------------------------------------------------------------------
    # Store slug discovery
    # ------------------------------------------------------------------

    async def _load_store_slugs_from_db(self) -> List[str]:
        """Load Bottle O store slugs from DB Store.url field."""
        slugs: set[str] = set()
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Store.url).where(Store.chain == self.chain)
                )
                for (url,) in result.all():
                    if url:
                        match = STORE_SLUG_PATTERN.search(url)
                        if match:
                            slugs.add(match.group(1).lower())
        except Exception as e:
            logger.warning(f"Failed loading {self.chain} stores from DB: {e}")
            return []

        return sorted(slugs)

    # ------------------------------------------------------------------
    # Fetching — per-store CityHive pages + franchise fallback
    # ------------------------------------------------------------------

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Fetch product pages from per-store CityHive sites and (optionally)
        the franchise catalog for non-shoppable stores.

        Returns tagged HTML strings (per-store) and JSON strings (franchise).
        """
        if self.use_fixtures:
            return await self._fetch_from_fixtures()

        # Resolve store list from DB when not explicitly provided
        if not self._stores_explicit and self._scrape_all_stores:
            db_stores = await self._load_store_slugs_from_db()
            if db_stores:
                self.stores = db_stores
                logger.info(f"Loaded {len(self.stores)} Bottle O stores from database")
            else:
                logger.info(f"Using fallback Bottle O store list ({len(self.stores)} stores)")

        pages: List[str] = []

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

            # --- Per-store scraping ---
            shoppable_slugs: set[str] = set()
            try:
                for store_slug in self.stores:
                    logger.info(f"Scraping store: {store_slug}")
                    consecutive_failures = 0
                    max_failures = 3
                    store_had_products = False

                    for category in CATEGORIES:
                        if consecutive_failures >= max_failures:
                            logger.warning(f"  Skipping remaining categories for {store_slug}")
                            break

                        logger.info(f"  Category: {category}")
                        category_success = False
                        page_num = 1

                        while True:
                            url = self._build_url(store_slug, category, page_num)

                            try:
                                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                                try:
                                    await page.wait_for_selector(".talker", state="attached", timeout=8000)
                                except Exception:
                                    pass  # Page may be empty (no products in category)
                                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

                                html = await page.content()
                                tagged_html = self._tag_html(html, store_slug, category, page_num)
                                pages.append(tagged_html)
                                category_success = True
                                store_had_products = True

                                has_next = await self._has_next_page(page)
                                if not has_next:
                                    logger.info(f"    Scraped {page_num} page(s)")
                                    break

                                page_num += 1
                                if page_num > 50:
                                    logger.warning(f"    Hit page limit at page {page_num}")
                                    break

                            except PlaywrightTimeout:
                                logger.error(f"    Timeout loading {url}")
                                break
                            except Exception as e:
                                logger.error(f"    Error loading {url}: {e}")
                                break

                        if category_success:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1

                        await asyncio.sleep(DELAY_BETWEEN_CATEGORIES)

                    if store_had_products:
                        shoppable_slugs.add(store_slug)

                # --- Franchise fallback for non-shoppable stores ---
                franchise_pages = await self._fetch_franchise_pages(page)
                if franchise_pages:
                    pages.extend(franchise_pages)
            finally:
                with suppress(Exception):
                    await context.unroute_all(behavior="ignoreErrors")
                with suppress(Exception):
                    await page.close()
                with suppress(Exception):
                    await context.close()
                with suppress(Exception):
                    await browser.close()

        logger.info(
            f"Fetched {len(pages)} total pages "
            f"({len(shoppable_slugs)} shoppable stores)"
        )
        return pages

    async def _fetch_franchise_pages(self, page) -> List[str]:
        """Fetch franchise catalog pages via GTM dataLayer extraction."""
        franchise_pages: List[str] = []

        for cat_url in FRANCHISE_CATALOG_URLS:
            try:
                logger.info(f"Franchise catalog: {cat_url}")
                page_num = 1

                while True:
                    url = cat_url if page_num == 1 else f"{cat_url}&page={page_num}"

                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_selector("body", timeout=10000)
                    await page.wait_for_timeout(5000)

                    product_count = await page.evaluate("""() => {
                        if (!window.gtmDataLayer) return 0;
                        let count = 0;
                        for (const event of window.gtmDataLayer) {
                            if (event.event === 'productListImpression') {
                                count += (event.ecommerce && event.ecommerce.impressions)
                                    ? event.ecommerce.impressions.length : 0;
                            }
                        }
                        return count;
                    }""")

                    if product_count == 0:
                        if page_num == 1:
                            logger.warning(f"  No products on franchise page 1")
                        break

                    gtm_data = await page.evaluate(
                        "() => JSON.stringify(window.gtmDataLayer || [])"
                    )
                    html = await page.content()

                    combined = json.dumps({
                        "gtm": json.loads(gtm_data),
                        "html": html,
                        "_franchise": True,
                    })
                    franchise_pages.append(combined)
                    logger.info(f"  Page {page_num}: {product_count} products")

                    if product_count < 48:
                        break

                    page_num += 1
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

            except Exception as e:
                logger.error(f"Failed to fetch franchise page {cat_url}: {e}")
                continue

        return franchise_pages

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    async def parse_products(self, payload: str) -> List[dict]:
        """
        Parse products from either:
        - Tagged CityHive HTML (per-store)
        - JSON blob with GTM dataLayer (franchise fallback)
        """
        # Franchise pages are JSON, per-store pages start with <!--METADATA:
        if payload.startswith("<!--METADATA:"):
            return self._parse_cityhive_products(payload)
        else:
            return self._parse_franchise_products(payload)

    def _parse_cityhive_products(self, tagged_html: str) -> List[dict]:
        """Parse products from CityHive .talker HTML (per-store pages)."""
        metadata, html = self._untag_html(tagged_html)
        store_slug = metadata.get("store", "unknown")

        tree = HTMLParser(html)
        products = []

        for talker in tree.css(".talker"):
            try:
                product = self._parse_talker_element(talker, store_slug)
                if product:
                    products.append(product)
            except Exception as e:
                logger.error(f"Error parsing talker element: {e}", exc_info=True)

        logger.info(f"Parsed {len(products)} products from store {store_slug}")
        return products

    def _parse_talker_element(self, talker, store_slug: str) -> Optional[dict]:
        """Parse a single product from a CityHive .talker element."""

        # Product ID
        product_id_attr = talker.attributes.get("id", "")
        source_id_match = re.search(r"line_([a-f0-9]+)", product_id_attr)
        if not source_id_match:
            return None
        source_id = source_id_match.group(1)

        # Product name
        name_elem = talker.css_first(".talker__name")
        if not name_elem:
            return None

        name_spans = name_elem.css("span")
        if not name_spans:
            return None

        product_name = name_spans[0].text(strip=True)
        if not product_name:
            return None

        # Size from .talker__name__size
        size_text = ""
        size_elem = name_elem.css_first(".talker__name__size")
        if size_elem:
            size_text = size_elem.text(strip=True)
            full_name = f"{product_name} {size_text}".strip()
        else:
            full_name = product_name

        # Price
        price_elem = talker.css_first(".price__sell")
        if not price_elem:
            return None

        price_text = price_elem.text(strip=True).replace("$", "").replace(",", "")
        try:
            price_nzd = float(price_text)
        except (ValueError, TypeError):
            return None

        # Product URL
        url = None
        link_elem = talker.css_first("a[href]")
        if link_elem:
            href = link_elem.attributes.get("href", "")
            if href and not href.startswith("http"):
                url = f"https://{store_slug}.shop.thebottleo.co.nz{href}"
            elif href:
                url = href

        # Image URL
        image_url = None
        source_elem = talker.css_first("source[type='image/webp']")
        if source_elem:
            srcset = source_elem.attributes.get("srcset")
            if srcset:
                image_url = srcset.split()[0]
        if not image_url:
            img_elem = talker.css_first("img")
            if img_elem:
                image_url = img_elem.attributes.get("src") or img_elem.attributes.get("data-src")

        if image_url and "no_image" in image_url:
            image_url = None

        # Volume / ABV / brand / category
        volume_info = parse_volume(size_text) or parse_volume(full_name)
        pack_count = volume_info.pack_count if volume_info else None
        unit_volume_ml = volume_info.unit_volume_ml if volume_info else None
        total_volume_ml = volume_info.total_volume_ml if volume_info else None

        abv_percent = extract_abv(full_name) or extract_abv(size_text)
        brand = infer_brand(full_name)
        category = infer_category(full_name)

        # Promotions
        promo_price = None
        promo_text = None
        promo_ends_at = None
        is_member_only = False

        talker_classes = talker.attributes.get("class", "")
        is_special = "talker--Special" in talker_classes or "talker--Discount" in talker_classes

        if is_special:
            sticker_label = talker.css_first(".talker__sticker__label")
            if sticker_label:
                badge_text = sticker_label.text(strip=True)
                if badge_text:
                    promo_text = badge_text[:255]

                    multi_buy = parse_multi_buy_deal(badge_text)
                    if multi_buy:
                        if multi_buy.get("unit_price"):
                            promo_price = multi_buy["unit_price"]
                        promo_text = multi_buy["deal_text"][:255]
                    else:
                        promo_price = price_nzd

                    promo_ends_at = parse_promo_end_date(badge_text)
                    is_member_only = detect_member_only(badge_text)
            else:
                promo_price = price_nzd
                promo_text = "Special"

        # Secondary promo badge check
        if not promo_text:
            promo_badge = (
                talker.css_first('[class*="promo"]')
                or talker.css_first('[class*="deal"]')
                or talker.css_first('[class*="save"]')
                or talker.css_first('[class*="offer"]')
            )
            if promo_badge:
                badge_text = promo_badge.text(strip=True)
                if badge_text:
                    promo_text = badge_text[:255]

                    extracted_price = parse_promo_price(badge_text)
                    if extracted_price and extracted_price < price_nzd:
                        promo_price = extracted_price

                    multi_buy = parse_multi_buy_deal(badge_text)
                    if multi_buy:
                        if multi_buy.get("unit_price"):
                            promo_price = multi_buy["unit_price"]
                        promo_text = multi_buy["deal_text"][:255]

                    promo_ends_at = parse_promo_end_date(badge_text)
                    is_member_only = detect_member_only(badge_text)

        return {
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
            "store_identifier": store_slug,
        }

    # ------------------------------------------------------------------
    # Franchise (GTM) parsing — fallback for non-shoppable stores
    # ------------------------------------------------------------------

    def _parse_franchise_products(self, payload: str) -> List[dict]:
        """Parse products from franchise GTM dataLayer JSON."""
        products = []
        try:
            data = json.loads(payload)
            gtm_data = data.get("gtm", [])
            html = data.get("html", "")

            if not isinstance(gtm_data, list):
                return products

            images_by_name = self._extract_images_from_html(html)

            for event in gtm_data:
                if not isinstance(event, dict):
                    continue
                if event.get("event") == "productListImpression":
                    impressions = event.get("ecommerce", {}).get("impressions", [])
                    for item in impressions:
                        product = self._parse_gtm_product(item, images_by_name)
                        if product:
                            # Mark as franchise (no store_identifier)
                            product["_franchise"] = True
                            products.append(product)

            logger.info(f"Parsed {len(products)} products from franchise catalog")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse franchise JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing franchise products: {e}")

        return products

    def _parse_gtm_product(self, item: dict, images_by_name: dict) -> Optional[dict]:
        """Parse a single product from GTM dataLayer impression."""
        try:
            source_id = item.get("id", "")
            name = item.get("name", "")
            price = item.get("price")
            brand = item.get("brand", "")
            category = item.get("category", "")

            if not name or not source_id or price is None:
                return None

            if isinstance(price, str):
                price = float(price.replace("$", "").replace(",", ""))
            else:
                price = float(price)

            if not brand:
                brand = infer_brand(name)
            if not category:
                category = infer_category(name)

            volume = parse_volume(name)
            abv = extract_abv(name)

            promo_price = None
            promo_text = None
            promo_ends_at = None
            is_member_only = False

            if item.get("discount"):
                discount_text = str(item["discount"])
                promo_text = discount_text[:255]
                extracted = parse_promo_price(discount_text)
                if extracted and extracted < price:
                    promo_price = extracted

            if item.get("promotion"):
                raw = str(item["promotion"])
                promo_text = raw[:255]
                multi_buy = parse_multi_buy_deal(raw)
                if multi_buy:
                    if multi_buy.get("unit_price"):
                        promo_price = multi_buy["unit_price"]
                    promo_text = multi_buy["deal_text"][:255]
                promo_ends_at = parse_promo_end_date(raw)

            if item.get("coupon"):
                coupon_text = str(item["coupon"])
                is_member_only = detect_member_only(coupon_text)
                if not promo_text:
                    promo_text = coupon_text[:255]

            if item.get("original_price") or item.get("was_price"):
                old_val = item.get("original_price") or item.get("was_price")
                if isinstance(old_val, str):
                    old_price = float(old_val.replace("$", "").replace(",", ""))
                else:
                    old_price = float(old_val)
                if price < old_price and not promo_price:
                    promo_price = price
                    price = old_price
                    if not promo_text:
                        promo_text = "Special"

            url = f"https://thebottleo.co.nz/products/{source_id}"

            normalized_name = self._normalize_name(name)
            image_url = images_by_name.get(normalized_name)
            if not image_url:
                image_url = images_by_name.get(self._normalize_name_without_volume(name))

            return {
                "chain": self.chain,
                "source_id": source_id,
                "name": name,
                "brand": brand,
                "category": category,
                "price_nzd": price,
                "promo_price_nzd": promo_price,
                "promo_text": promo_text,
                "promo_ends_at": promo_ends_at,
                "is_member_only": is_member_only,
                "pack_count": volume.pack_count,
                "unit_volume_ml": volume.unit_volume_ml,
                "total_volume_ml": volume.total_volume_ml,
                "abv_percent": abv,
                "url": url,
                "image_url": image_url,
            }
        except Exception as e:
            logger.debug(f"Failed to parse GTM product: {e}")
            return None

    # ------------------------------------------------------------------
    # HTML helpers (shared with franchise GTM image extraction)
    # ------------------------------------------------------------------

    def _normalize_name(self, name: str) -> str:
        normalized = " ".join(name.replace("\n", " ").split()).lower()
        normalized = re.sub(r"(\d+)\s*x\s*(\d+)", r"\1x\2", normalized)
        return normalized

    def _normalize_name_without_volume(self, name: str) -> str:
        normalized = self._normalize_name(name)
        normalized = re.sub(r"\b\d+x\d+ml\b", "", normalized)
        normalized = re.sub(r"\b\d+ml\b", "", normalized)
        normalized = re.sub(r"\b\d+l\b", "", normalized)
        normalized = re.sub(r"\b\d+pk\b", "", normalized)
        return " ".join(normalized.split())

    def _extract_images_from_html(self, html: str) -> dict:
        """Extract product images from HTML, keyed by normalised product name."""
        images: dict[str, str] = {}
        tree = HTMLParser(html)

        for talker in tree.css(".talker"):
            img = talker.css_first("img[src], img[data-src]")
            if not img:
                continue
            src = img.attributes.get("src") or img.attributes.get("data-src")
            if not src or "placeholder" in src.lower():
                continue
            if not src.startswith("http"):
                src = f"https:{src}" if src.startswith("//") else f"https://thebottleo.co.nz{src}"

            name_elem = talker.css_first(".talker__name")
            if name_elem:
                product_name = name_elem.text().strip()
                if product_name:
                    images[self._normalize_name(product_name)] = src
                    no_vol = self._normalize_name_without_volume(product_name)
                    if no_vol and no_vol not in images:
                        images[no_vol] = src

        return images

    # ------------------------------------------------------------------
    # CityHive HTML metadata tagging (mirroring LiquorCentreScraper)
    # ------------------------------------------------------------------

    def _build_url(self, store_slug: str, category: str, page: int = 1) -> str:
        base = f"https://{store_slug}.shop.thebottleo.co.nz/category/{category}"
        if page > 1:
            return f"{base}?page={page}"
        return base

    async def _has_next_page(self, page) -> bool:
        try:
            next_link = await page.locator('a[rel="next"]').count()
            return next_link > 0
        except Exception:
            return False

    def _tag_html(self, html: str, store: str, category: str, page: int) -> str:
        return f"<!--METADATA:store={store},category={category},page={page}-->{html}"

    def _untag_html(self, tagged_html: str) -> tuple:
        metadata: dict[str, str] = {}
        html = tagged_html

        if tagged_html.startswith("<!--METADATA:"):
            end_idx = tagged_html.find("-->")
            if end_idx != -1:
                metadata_str = tagged_html[13:end_idx]
                html = tagged_html[end_idx + 3:]
                for pair in metadata_str.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        metadata[key] = value

        return metadata, html

    # ------------------------------------------------------------------
    # Fixture support
    # ------------------------------------------------------------------

    async def _fetch_from_fixtures(self) -> List[str]:
        import os

        fixture_path = "app/scrapers/fixtures/bottle_o.html"
        if not os.path.exists(fixture_path):
            logger.warning(f"Fixture not found: {fixture_path}")
            return []

        with open(fixture_path, "r", encoding="utf-8") as f:
            html = f.read()

        # If the fixture already starts with a METADATA tag, return as-is
        if html.startswith("<!--METADATA:"):
            return [html]

        tagged = self._tag_html(html, "test-store", "beer", 1)
        return [tagged]

    # ------------------------------------------------------------------
    # DB persistence — per-store pricing override
    # ------------------------------------------------------------------

    async def _upsert_products_batch(
        self, session, products_data: list, stores: list
    ) -> int:
        """
        Batch upsert with per-store pricing for CityHive products and
        broadcast pricing for franchise products.
        """
        if not products_data:
            return 0

        # Split into per-store and franchise products
        store_products: dict[str, list] = {}
        franchise_products: list[dict] = []

        for p in products_data:
            if p.get("_franchise"):
                franchise_products.append(p)
            else:
                sid = p.get("store_identifier", "unknown")
                store_products.setdefault(sid, []).append(p)

        changed_count = 0

        # Per-store upserts (CityHive)
        for store_identifier, prods in store_products.items():
            changed_count += await self._upsert_for_store(
                session, prods, stores, store_identifier
            )

        # Franchise broadcast: assign to all stores that were NOT scraped per-store
        if franchise_products:
            scraped_slugs = set(store_products.keys())
            fallback_stores = [
                s for s in stores
                if not self._store_matches_slug(s, scraped_slugs)
            ]
            if fallback_stores:
                changed_count += await self._upsert_franchise_broadcast(
                    session, franchise_products, fallback_stores
                )

        return changed_count

    async def _upsert_for_store(
        self,
        session,
        products_data: list,
        stores: list,
        store_identifier: str,
    ) -> int:
        """Upsert products and prices for a single store."""
        now = datetime.utcnow()
        changed_count = 0

        # Find matching store
        target_store = None
        for store in stores:
            if store.url and store_identifier in store.url:
                target_store = store
                break
            name_slug = (
                store.name.lower()
                .replace(" ", "-")
                .replace("the-bottle-o-", "")
                .replace("bottle-o-", "")
            )
            if store_identifier in name_slug or name_slug in store_identifier:
                target_store = store
                break

        if not target_store:
            store_url = f"https://{store_identifier}.shop.thebottleo.co.nz"
            existing = await session.execute(
                select(Store).where(
                    Store.chain == self.chain, Store.url == store_url
                )
            )
            target_store = existing.scalar_one_or_none()

            if not target_store:
                logger.info(f"Creating new store for: {store_identifier}")
                target_store = Store(
                    name=f"The Bottle O {store_identifier.title().replace('-', ' ')}",
                    chain=self.chain,
                    lat=0.0,
                    lon=0.0,
                    url=store_url,
                )
                session.add(target_store)
                await session.flush()

        # Bulk upsert products
        product_values = [self._product_values(p) for p in products_data]
        stmt = insert(Product).values(product_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["chain", "source_product_id"],
            set_=self._product_update_set(stmt, now),
        )
        await session.execute(stmt)
        await session.flush()

        # Get product IDs
        source_ids = [p["source_id"] for p in products_data]
        result = await session.execute(
            select(Product.id, Product.source_product_id).where(
                Product.chain == self.chain,
                Product.source_product_id.in_(source_ids),
            )
        )
        product_id_map = {row.source_product_id: row.id for row in result}

        # Existing prices for THIS store
        product_ids = list(product_id_map.values())
        existing_result = await session.execute(
            select(Price).where(
                Price.product_id.in_(product_ids),
                Price.store_id == target_store.id,
            )
        )
        existing_map = {
            price.product_id: price
            for price in existing_result.scalars().all()
        }

        # Bulk upsert prices
        price_values = []
        for p in products_data:
            pid = product_id_map.get(p["source_id"])
            if not pid:
                continue

            existing = existing_map.get(pid)
            price_changed = False
            if existing:
                if (
                    existing.price_nzd != p["price_nzd"]
                    or existing.promo_price_nzd != p.get("promo_price_nzd")
                ):
                    price_changed = True
                    changed_count += 1

            price_values.append({
                "product_id": pid,
                "store_id": target_store.id,
                "price_nzd": p["price_nzd"],
                "promo_price_nzd": p.get("promo_price_nzd"),
                "promo_text": p.get("promo_text"),
                "promo_ends_at": p.get("promo_ends_at"),
                "is_member_only": p.get("is_member_only", False),
                "last_seen_at": now,
                "price_last_changed_at": now
                if (price_changed or not existing)
                else (existing.price_last_changed_at if existing else now),
            })

            if not existing:
                changed_count += 1

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

    async def _upsert_franchise_broadcast(
        self, session, products_data: list, stores: list
    ) -> int:
        """Broadcast franchise prices to all non-shoppable stores (base behaviour)."""
        return await super()._upsert_products_batch(session, products_data, stores)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _store_matches_slug(store: Store, slugs: set[str]) -> bool:
        """Check if a Store object matches any of the given slugs."""
        if store.url:
            match = STORE_SLUG_PATTERN.search(store.url)
            if match and match.group(1).lower() in slugs:
                return True
        return False

    @staticmethod
    def _product_values(p: dict) -> dict:
        return {
            "chain": p["chain"],
            "source_product_id": p["source_id"],
            "name": p["name"],
            "brand": p.get("brand"),
            "category": p.get("category"),
            "abv_percent": p.get("abv_percent"),
            "pack_count": p.get("pack_count"),
            "unit_volume_ml": p.get("unit_volume_ml"),
            "total_volume_ml": p.get("total_volume_ml"),
            "image_url": p.get("image_url"),
            "product_url": p.get("url"),
        }

    @staticmethod
    def _product_update_set(stmt, now: datetime) -> dict:
        return {
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
        }


__all__ = ["BottleOScraper"]
