from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume, infer_brand, infer_category
from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
)

FIXTURE = Path(__file__).parent / "fixtures" / "super_liquor.html"

logger = logging.getLogger(__name__)

# Rate limiting configuration (respectful scraping)
DELAY_BETWEEN_REQUESTS = 0.7  # seconds between page requests
DELAY_BETWEEN_CATEGORIES = 1.5  # seconds between different categories
MAX_RETRIES = 3  # max retries for failed requests
RETRY_DELAY = 2.0  # initial retry delay (doubles each retry)


class SuperLiquorScraper(Scraper):
    chain = "super_liquor"
    catalog_urls = [
        # Specials first so category pages overwrite with correct was/now pricing
        "https://www.superliquor.co.nz/super-specials",
        # Beer & Cider
        "https://www.superliquor.co.nz/beer",
        "https://www.superliquor.co.nz/craft-beer",
        "https://www.superliquor.co.nz/cider",
        # Wine & Bubbles
        "https://www.superliquor.co.nz/wine",
        "https://www.superliquor.co.nz/white-wine",
        "https://www.superliquor.co.nz/red-wine-",
        "https://www.superliquor.co.nz/sparkling-wine",
        # Spirits
        "https://www.superliquor.co.nz/spirits",
        "https://www.superliquor.co.nz/vodka",
        "https://www.superliquor.co.nz/gin",
        "https://www.superliquor.co.nz/whisky",
        "https://www.superliquor.co.nz/rum",
        "https://www.superliquor.co.nz/bourbon",
        # RTDs
        "https://www.superliquor.co.nz/premix",
    ]

    def __init__(self, chain: str = "super_liquor", use_fixtures: bool = False) -> None:
        super().__init__(use_fixtures=use_fixtures)
        self.chain = chain
        self._page_urls: List[str] = []
        self._specials_by_source_id: Dict[str, float] = {}
        self._specials_by_name: Dict[str, float] = {}

        # Set respectful User-Agent header
        self.client.headers.update({
            "User-Agent": "Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)"
        })

    async def _fetch_with_retry(self, url: str, retry_count: int = 0) -> str:
        """Fetch URL with exponential backoff on errors."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text

        except Exception as e:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
                logger.warning(f"  Request failed, retrying in {delay}s... ({retry_count + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                return await self._fetch_with_retry(url, retry_count + 1)
            else:
                logger.error(f"  Failed after {MAX_RETRIES} retries: {e}")
                raise

    async def fetch_catalog_pages(self) -> List[str]:
        """Fetch catalog pages from fixtures or live HTTP with pagination and rate limiting."""
        self._page_urls = []
        self._specials_by_source_id = {}
        self._specials_by_name = {}

        if self.use_fixtures:
            logger.info(f"Using fixture data for {self.chain}")
            self._page_urls.append(str(FIXTURE))
            return [FIXTURE.read_text()]

        # Fetch from real URLs with pagination and rate limiting
        logger.info(f"Fetching live data from {len(self.catalog_urls)} category URLs")
        logger.info(f"Rate limiting: {DELAY_BETWEEN_REQUESTS}s between requests, {DELAY_BETWEEN_CATEGORIES}s between categories")
        pages = []

        for category_idx, base_url in enumerate(self.catalog_urls):
            try:
                # Add delay between categories (but not before the first one)
                if category_idx > 0:
                    logger.info(f"Waiting {DELAY_BETWEEN_CATEGORIES}s before next category...")
                    await asyncio.sleep(DELAY_BETWEEN_CATEGORIES)

                # Fetch first page to determine total pages
                logger.info(f"Fetching {base_url}")
                first_page = await self._fetch_with_retry(base_url)
                pages.append(first_page)
                self._page_urls.append(base_url)

                # Parse to find total number of pages
                total_pages = self._extract_total_pages(first_page)

                if total_pages > 1:
                    logger.info(f"  Found {total_pages} pages, fetching remaining pages...")

                    # Fetch remaining pages with delays
                    for page_num in range(2, total_pages + 1):
                        # Rate limiting: delay between requests
                        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

                        page_url = f"{base_url}?pagenumber={page_num}"
                        try:
                            page_html = await self._fetch_with_retry(page_url)
                            pages.append(page_html)
                            self._page_urls.append(page_url)
                            logger.info(f"  Fetched page {page_num}/{total_pages}")
                        except Exception as e:
                            logger.error(f"  Failed to fetch page {page_num} after retries: {e}")
                            # Continue fetching other pages
                            continue
                else:
                    logger.info(f"  Only 1 page found")

            except Exception as e:
                logger.error(f"Failed to fetch {base_url} after retries: {e}")
                continue

        logger.info(f"Fetched total of {len(pages)} pages across all categories")
        return pages

    @staticmethod
    def _normalized_name(name: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", name.lower())).strip()

    def _store_special_candidate(self, source_id: str, name: str, specials_price: float) -> None:
        if specials_price <= 0:
            return
        if source_id:
            existing = self._specials_by_source_id.get(source_id)
            if existing is None or specials_price < existing:
                self._specials_by_source_id[source_id] = specials_price
        normalized = self._normalized_name(name)
        if normalized:
            existing = self._specials_by_name.get(normalized)
            if existing is None or specials_price < existing:
                self._specials_by_name[normalized] = specials_price

    def _find_special_candidate(self, source_id: str, name: str) -> Optional[float]:
        if source_id and source_id in self._specials_by_source_id:
            return self._specials_by_source_id[source_id]
        return self._specials_by_name.get(self._normalized_name(name))

    def _extract_total_pages(self, html: str) -> int:
        """Extract total number of pages from pagination HTML."""
        # Look for pager div with page links
        pager_match = re.search(r'<div class="pager"[^>]*>(.*?)</div>', html, re.DOTALL)
        if pager_match:
            pager_html = pager_match.group(1)

            # Find all page numbers in pagination links
            page_nums = re.findall(r'pagenumber=(\d+)', pager_html)
            if page_nums:
                page_nums = [int(p) for p in page_nums]
                return max(page_nums)

        # If no pagination found, assume single page
        return 1

    async def parse_products(self, payload: str) -> List[dict]:
        page_url = self._page_urls.pop(0) if self._page_urls else None
        is_specials_page = bool(page_url and "/super-specials" in page_url)

        tree = HTMLParser(payload)
        products: List[dict] = []
        specials_candidates_seen = 0
        specials_candidates_applied = 0

        for node in tree.css("div.product-item"):
            # Extract title
            title_node = node.css_first("h2.product-title a")
            if not title_node:
                logger.warning("Product found without title, skipping")
                continue
            name = title_node.text().strip()

            # Extract price from span or GA4 data
            price = None
            price_node = node.css_first("span.price.actual-price")
            if price_node and price_node.text():
                price_text = price_node.text().strip()
                price = float(price_text.replace("$", "").replace(",", ""))
            else:
                # Try to extract from GA4 tracking data as fallback
                ga4_match = re.search(r'price:([\d.]+)', node.html or "")
                if ga4_match:
                    price = float(ga4_match.group(1))

            if price is None:
                logger.warning(f"Product {name} has no price, skipping")
                continue

            # Extract promotional pricing
            promo_price = None
            promo_text = None
            promo_ends_at = None
            is_member_only = False

            # Look for promo badges on product
            promo_badge = (
                node.css_first('.product-badge') or
                node.css_first('.badge-special') or
                node.css_first('.badge') or
                node.css_first('[class*="badge"]') or
                node.css_first('[class*="deal"]') or
                node.css_first('[class*="promo"]') or
                node.css_first('[class*="special"]')
            )

            if promo_badge:
                badge_text = promo_badge.text(strip=True)
                if badge_text:
                    promo_text = badge_text[:255]

                    # Extract promo price if present in badge
                    price_match = re.search(r'\$?([\d.]+)', badge_text)
                    if price_match:
                        potential_promo = float(price_match.group(1))
                        if potential_promo < price:
                            promo_price = potential_promo

                    # Check for multi-buy deals
                    multi_buy = parse_multi_buy_deal(badge_text)
                    if multi_buy:
                        if multi_buy.get('unit_price'):
                            promo_price = multi_buy['unit_price']
                        promo_text = multi_buy['deal_text'][:255]

                    # Parse dates
                    promo_ends_at = parse_promo_end_date(badge_text)
                    is_member_only = detect_member_only(badge_text)

            # Check for special price alongside regular price
            special_price_node = node.css_first('.price.special-price') or node.css_first('.special-price')
            if special_price_node:
                special_text = special_price_node.text(strip=True)
                if special_text:
                    special_match = re.search(r'\$?([\d.]+)', special_text)
                    if special_match:
                        special_price = float(special_match.group(1))
                        if special_price < price:
                            promo_price = special_price
                            if not promo_text:
                                promo_text = "Special"[:255]

            # Check was-price scenario
            was_price_node = node.css_first('.price.was-price') or node.css_first('.was-price')
            if was_price_node and not promo_price:
                was_text = was_price_node.text(strip=True)
                if was_text:
                    was_match = re.search(r'\$?([\d.]+)', was_text)
                    if was_match:
                        old_price = float(was_match.group(1))
                        if price < old_price:
                            promo_price = price
                            price = old_price
                            if not promo_text:
                                promo_text = "Special"[:255]

            # Extract product URL
            url = title_node.attributes.get("href", "")
            if url and not url.startswith("http"):
                url = f"https://www.superliquor.co.nz{url}"

            # Extract product ID
            source_id = node.attributes.get("data-productid", "")
            if not source_id:
                source_id = url.split("/")[-1] if url else name

            # Extract image URL (avoid badge images)
            image_url = None
            img_nodes = node.css("div.picture img")

            # Badge keywords to filter out
            BADGE_KEYWORDS = [
                "low-carb", "gluten", "vegan", "organic", "badge", "icon",
                "promo", "deal", "offer", "special", "2for", "3for", "buy", "save",
                "2 for", "3 for", "multi", "multipack", "_100", "_50", "label",
                "zero", "sugar", "zero-sugar", "no-sugar"
            ]

            for img_node in img_nodes:
                # Super Liquor uses lazy loading with data-src
                img_url = img_node.attributes.get("data-src") or img_node.attributes.get("src")
                if img_url:
                    # Skip badge images
                    img_url_lower = img_url.lower()
                    if any(badge in img_url_lower for badge in BADGE_KEYWORDS):
                        continue
                    # Use the first non-badge image
                    image_url = img_url
                    break

            # Parse volume and ABV from product name and description
            volume = parse_volume(name)
            abv = extract_abv(name)

            # If no ABV found in name, try description
            if abv is None:
                desc_node = node.css_first("div.description")
                if desc_node:
                    description = desc_node.text().strip()
                    abv = extract_abv(description)

            brand = infer_brand(name)
            category = infer_category(name)

            product = {
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

            if is_specials_page:
                specials_price = promo_price if promo_price is not None and promo_price < price else price
                self._store_special_candidate(source_id, name, specials_price)
                specials_candidates_seen += 1
            else:
                special_candidate = self._find_special_candidate(source_id, name)
                if special_candidate is not None and special_candidate < price:
                    existing_promo = promo_price if promo_price is not None and promo_price < price else None
                    if existing_promo is None or special_candidate < existing_promo:
                        product["promo_price_nzd"] = special_candidate
                        product["promo_text"] = (product.get("promo_text") or "Super Special")[:255]
                        specials_candidates_applied += 1

            products.append(product)

        if is_specials_page:
            logger.info(
                f"Parsed {len(products)} products from specials page; "
                f"captured {specials_candidates_seen} specials candidates"
            )
        else:
            logger.info(
                f"Parsed {len(products)} products from page; "
                f"applied {specials_candidates_applied} specials candidates"
            )
        return products


__all__ = ["SuperLiquorScraper"]
