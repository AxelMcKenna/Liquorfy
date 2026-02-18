"""
Liquorland scraper using Playwright for JavaScript-rendered content.
Includes database integration and robots.txt compliance.
"""
from __future__ import annotations

import asyncio
import logging
import math
import re
from typing import List

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume, infer_brand, infer_category
from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
)

logger = logging.getLogger(__name__)

# Rate limiting configuration (respectful scraping per robots.txt)
DELAY_BETWEEN_REQUESTS = 1.0  # seconds between page requests
DELAY_BETWEEN_CATEGORIES = 2.5  # seconds between different categories


class LiquorlandScraper(Scraper):
    """Scraper for Liquorland NZ website using Playwright."""

    chain = "liquorland"

    # Top-level nav entries that are not product categories
    _SKIP_NAV_LABELS = {"recipes", "drinks guide", "specials"}

    BASE_URL = "https://www.liquorland.co.nz"

    # Fallback URLs used when dynamic discovery fails
    _FALLBACK_CATALOG_URLS = [
        "/beer/all-beer",
        "/craft-beer/all-craft-beer",
        "/cider",
        "/wine/all-wine",
        "/spirits/all-spirits",
        "/liqueurs/all-liqueurs",
        "/rtd/all-rtd",
    ]

    def __init__(self, use_fixtures: bool = False) -> None:
        super().__init__(use_fixtures=False)
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.playwright = None

    # ------------------------------------------------------------------
    # Category discovery
    # ------------------------------------------------------------------

    async def _discover_category_urls(self, page: Page) -> List[str]:
        """Read window.navigation and return non-overlapping category URLs.

        Strategy per top-level node:
        - Skip non-product sections (recipes, drinks guide, specials).
        - If the node has an "All X" child, use that (it contains the
          complete set for the category with zero overlap).
        - If the node is a leaf (no children), use it directly.
        - Otherwise DFS to collect leaf URLs.
        """
        nav = await page.evaluate(
            "() => { try { return window.navigation; } catch(e) { return null; } }"
        )
        if not nav:
            logger.warning("window.navigation not found, using fallback URLs")
            return [f"{self.BASE_URL}{path}" for path in self._FALLBACK_CATALOG_URLS]

        urls: List[str] = []
        for node in nav:
            label = (node.get("label") or "").strip()
            if label.lower() in self._SKIP_NAV_LABELS:
                continue

            children = node.get("children") or []
            if not children:
                # Leaf node (e.g. /cider)
                url = node.get("url", "")
                if url:
                    urls.append(self._abs(url))
                continue

            # Look for an "All X" child — it covers the entire category
            all_child = self._find_all_child(children)
            if all_child:
                urls.append(self._abs(all_child))
            else:
                # No "All X" child — DFS to leaves
                urls.extend(self._collect_leaf_urls(children))

        logger.info(f"Discovered {len(urls)} category URLs from navigation")
        for u in urls:
            logger.info(f"  {u}")
        return urls

    @staticmethod
    def _find_all_child(children: List[dict]) -> str | None:
        """Find the 'All X' child URL (e.g. 'All Wine' → /wine/all-wine)."""
        for child in children:
            label = (child.get("label") or "").lower()
            if label.startswith("all "):
                return child.get("url", "")
        return None

    def _collect_leaf_urls(self, nodes: List[dict]) -> List[str]:
        """DFS to collect leaf category URLs, skipping 'Shop All' entries."""
        leaves: List[str] = []
        for node in nodes:
            label = (node.get("label") or "").lower()
            if label.startswith("shop all") or label.startswith("all "):
                continue
            children = node.get("children") or []
            if not children:
                url = node.get("url", "")
                if url:
                    leaves.append(self._abs(url))
            else:
                # Prefer "All X" child within this sub-tree too
                all_child = self._find_all_child(children)
                if all_child:
                    leaves.append(self._abs(all_child))
                else:
                    leaves.extend(self._collect_leaf_urls(children))
        return leaves

    def _abs(self, path: str) -> str:
        """Convert a relative path to absolute URL."""
        if path.startswith("http"):
            return path
        return f"{self.BASE_URL}{path}"

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    async def fetch_catalog_pages(self) -> List[str]:
        """Fetch all catalog pages using Playwright.

        1. Loads any page to read window.navigation and discover category URLs.
        2. For each category, reads window.category.pagination to determine
           total pages, then fetches each page via ?p=N.
        """
        logger.info(f"Starting browser-based scraping for {self.chain}")
        logger.info(
            f"Rate limiting: {DELAY_BETWEEN_REQUESTS}s between pages, "
            f"{DELAY_BETWEEN_CATEGORIES}s between categories"
        )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)",
            viewport={"width": 1920, "height": 1080},
        )

        # Block resources we don't need — cuts page load time significantly
        _BLOCK_TYPES = {"image", "media", "font", "stylesheet"}
        await self.context.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type in _BLOCK_TYPES
                else route.continue_()
            ),
        )

        pages_html: List[str] = []

        try:
            # Discover categories from live navigation
            discovery_page = await self.context.new_page()
            await discovery_page.goto(
                f"{self.BASE_URL}/beer", wait_until="domcontentloaded", timeout=60000
            )
            await self._wait_for_content(discovery_page)
            catalog_urls = await self._discover_category_urls(discovery_page)
            await discovery_page.close()

            for category_idx, base_url in enumerate(catalog_urls):
                try:
                    if category_idx > 0:
                        logger.info(f"Waiting {DELAY_BETWEEN_CATEGORIES}s before next category...")
                        await asyncio.sleep(DELAY_BETWEEN_CATEGORIES)

                    logger.info(f"Fetching {base_url}")

                    page = await self.context.new_page()
                    try:
                        await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
                        await self._wait_for_content(page)

                        first_page_html = await page.content()
                        pages_html.append(first_page_html)

                        total_pages = await self._extract_total_pages_js(page)

                        if total_pages > 1:
                            logger.info(f"  Found {total_pages} pages, fetching remaining...")
                            for page_num in range(2, total_pages + 1):
                                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
                                page_url = self._get_page_url(base_url, page_num)
                                try:
                                    await page.goto(
                                        page_url, wait_until="domcontentloaded", timeout=60000
                                    )
                                    await self._wait_for_content(page)
                                    pages_html.append(await page.content())
                                    logger.info(f"  Fetched page {page_num}/{total_pages}")
                                except Exception as e:
                                    logger.error(f"  Failed to fetch page {page_num}: {e}")
                                    continue
                        else:
                            logger.info(f"  Only 1 page found")
                    finally:
                        await page.close()

                except Exception as e:
                    logger.error(f"Failed to fetch {base_url}: {e}")
                    continue

        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info(f"Browser closed for {self.chain}")

        logger.info(f"Fetched {len(pages_html)} total pages across all categories")
        return pages_html

    async def _wait_for_content(self, page: Page) -> None:
        """Wait for Liquorland products to load."""
        try:
            # Wait until products are attached to the DOM (not visible — avoids
            # false timeouts when elements render off-screen before scrolling).
            # networkidle is intentionally omitted: it waits for analytics/ads
            # which adds 10-15s per page with no benefit for data extraction.
            await page.wait_for_selector('.s-product', state='attached', timeout=10000)
        except Exception as e:
            logger.warning(f"Timeout waiting for products: {e}")
            # Continue anyway, we might still get some data

    async def _extract_total_pages_js(self, page: Page) -> int:
        """Extract total pages from window.category.pagination JS object."""
        try:
            pagination = await page.evaluate(
                "() => { try { return window.category.pagination; } catch(e) { return null; } }"
            )
            if pagination:
                total_items = pagination.get("totalItems", 0)
                items_per_page = pagination.get("itemsPerPage", 24)
                if total_items and items_per_page:
                    total_pages = math.ceil(total_items / items_per_page)
                    logger.info(f"  Pagination: {total_items} items, {items_per_page}/page, {total_pages} pages")
                    return total_pages
        except Exception as e:
            logger.warning(f"  Could not extract pagination from JS: {e}")

        # Fallback: check for Load More link in DOM
        try:
            load_more = page.locator("a.ps-category-pagination__button")
            if await load_more.count() > 0:
                return 2  # At least 2 pages
        except Exception:
            pass

        return 1

    def _get_page_url(self, base_url: str, page_num: int) -> str:
        """Construct Liquorland page URL."""
        # Liquorland uses ?p=N format
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}p={page_num}"

    async def parse_products(self, payload: str) -> List[dict]:
        """Parse products from Liquorland HTML."""
        tree = HTMLParser(payload)
        products: List[dict] = []

        for node in tree.css('.s-product'):
            try:
                # Extract title from s-product__name
                title_node = node.css_first('a.s-product__name')
                if not title_node:
                    continue

                name = title_node.text().strip()

                # Extract URL
                url = title_node.attributes.get('href', '')
                if url and not url.startswith('http'):
                    url = f"https://www.liquorland.co.nz{url}"

                # Extract price - skip if "Choose a store" pricing
                pricing_section = node.css_first('.s-site-pricing')
                if pricing_section and 'no-cta' in (pricing_section.attributes.get('class') or ''):
                    # This product requires store selection for pricing
                    continue

                price_node = node.css_first('.s-price') or node.css_first('.s-site-price')
                if not price_node or not price_node.text():
                    continue

                price_text = price_node.text().strip()
                # Remove currency symbols and extract number
                price_clean = re.sub(r'[^\d.]', '', price_text)
                if not price_clean:
                    continue
                price = float(price_clean)

                # Extract promotional pricing
                promo_price = None
                promo_text = None
                promo_ends_at = None
                is_member_only = False

                # Try multiple promo selectors
                promo_node = (
                    node.css_first('.s-product__badge') or
                    node.css_first('.s-product__label') or
                    node.css_first('.s-product__special') or
                    node.css_first('.s-product__promo') or
                    node.css_first('[class*="promo"]') or
                    node.css_first('[class*="special"]') or
                    node.css_first('[class*="deal"]') or
                    node.css_first('[class*="save"]')
                )

                if promo_node:
                    promo_raw_text = promo_node.text(strip=True)

                    if promo_raw_text:
                        # Extract promo price from badge
                        extracted_price = parse_promo_price(promo_raw_text)
                        if extracted_price and extracted_price < price:
                            promo_price = extracted_price
                            promo_text = promo_raw_text[:255]

                        # Check for multi-buy deals
                        multi_buy = parse_multi_buy_deal(promo_raw_text)
                        if multi_buy:
                            if multi_buy.get('unit_price'):
                                promo_price = multi_buy['unit_price']
                            promo_text = multi_buy['deal_text'][:255]

                        # Parse end date
                        promo_ends_at = parse_promo_end_date(promo_raw_text)

                        # Check member-only
                        is_member_only = detect_member_only(promo_raw_text)

                # Check for "was price" / crossed-out price scenario
                was_price_node = (
                    node.css_first('.s-product__was-price') or
                    node.css_first('.s-price--was') or
                    node.css_first('[class*="was-price"]') or
                    node.css_first('[class*="old-price"]')
                )

                if was_price_node and not promo_price:
                    was_text = was_price_node.text(strip=True)
                    if was_text:
                        was_match = re.search(r'\$?([\d.]+)', was_text)
                        if was_match:
                            old_price = float(was_match.group(1))
                            if price < old_price:
                                # Current price IS the promo, was_price is the original
                                promo_price = price
                                price = old_price
                                if not promo_text:
                                    promo_text = "Special"[:255]

                # Extract image (avoid badge images)
                image_url = None
                img_nodes = node.css('img')

                # Badge keywords to filter out
                BADGE_KEYWORDS = [
                    "low-carb", "gluten", "vegan", "organic", "badge", "icon",
                    "promo", "deal", "offer", "special", "2for", "3for", "buy", "save",
                    "2 for", "3 for", "multi", "multipack", "_100", "_50", "label",
                    "zero", "sugar", "zero-sugar", "no-sugar"
                ]

                for img_node in img_nodes:
                    img_url = (
                        img_node.attributes.get('src') or
                        img_node.attributes.get('data-src') or
                        img_node.attributes.get('data-lazy-src')
                    )
                    if img_url:
                        # Skip badge images
                        img_url_lower = img_url.lower()
                        if any(badge in img_url_lower for badge in BADGE_KEYWORDS):
                            continue
                        # Use the first non-badge image
                        if not img_url.startswith('http'):
                            image_url = f"https://www.liquorland.co.nz{img_url}"
                        else:
                            image_url = img_url
                        break

                # Extract product ID from URL
                source_id = url.split('/')[-1] if url else name

                # Parse volume and ABV from name
                volume = parse_volume(name)
                abv = extract_abv(name)
                brand = infer_brand(name)
                category = infer_category(name)

                products.append({
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
                })

            except Exception as e:
                logger.error(f"Error parsing product: {e}", exc_info=True)
                continue

        logger.info(f"Parsed {len(products)} products from page")
        return products


__all__ = ["LiquorlandScraper"]
