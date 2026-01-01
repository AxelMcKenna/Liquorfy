"""
The Bottle O scraper extracting products from GTM dataLayer.
Uses Playwright for browser automation with database integration.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import List

from playwright.async_api import async_playwright, Browser, BrowserContext
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
DELAY_BETWEEN_CATEGORIES = 2.5  # seconds between different categories


class BottleOScraper(Scraper):
    """Scraper for The Bottle O NZ website using GTM dataLayer extraction."""

    chain = "bottle_o"

    # Use search URLs which load all products for a category
    catalog_urls = [
        "https://thebottleo.co.nz/search?q[]=category:beer&sort_by=top_products",
        "https://thebottleo.co.nz/search?q[]=category:wine&sort_by=top_products",
        "https://thebottleo.co.nz/search?q[]=category:spirits&sort_by=top_products",
        "https://thebottleo.co.nz/search?q[]=category:rtd&sort_by=top_products",
        "https://thebottleo.co.nz/search?q[]=category:cider&sort_by=top_products",
    ]

    def __init__(self, use_fixtures: bool = False) -> None:
        """
        Initialize Bottle O scraper.

        Args:
            use_fixtures: Not used for browser-based scraping (always False)
        """
        super().__init__(use_fixtures=False)
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.playwright = None

    async def fetch_catalog_pages(self) -> List[str]:
        """
        Fetch catalog pages using Playwright and extract GTM dataLayer.

        Returns:
            List of JSON strings containing GTM dataLayer data
        """
        logger.info(f"Starting browser-based scraping for {self.chain}")
        logger.info(f"Fetching data from {len(self.catalog_urls)} category URLs")
        logger.info(f"Rate limiting: {DELAY_BETWEEN_CATEGORIES}s between categories")

        # Start Playwright browser
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

        # Create context with respectful user agent (compliant with robots.txt)
        self.context = await self.browser.new_context(
            user_agent="Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)",
            viewport={"width": 1920, "height": 1080},
        )

        pages_data = []

        try:
            for category_idx, url in enumerate(self.catalog_urls):
                try:
                    # Add delay between categories (but not before the first one)
                    if category_idx > 0:
                        logger.info(f"Waiting {DELAY_BETWEEN_CATEGORIES}s before next category...")
                        await asyncio.sleep(DELAY_BETWEEN_CATEGORIES)

                    logger.info(f"Fetching {url}")

                    # Create new page for this category
                    page = await self.context.new_page()
                    try:
                        # Navigate to page
                        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                        # Wait for body and GTM dataLayer to load
                        await page.wait_for_selector('body', timeout=10000)
                        await page.wait_for_timeout(5000)  # Give JS time to populate gtmDataLayer

                        # Check if gtmDataLayer exists
                        has_data = await page.evaluate("() => window.gtmDataLayer && window.gtmDataLayer.length > 0")
                        if has_data:
                            logger.info("  GTM dataLayer loaded successfully")
                        else:
                            logger.warning("  GTM dataLayer not found or empty")

                        # Extract both gtmDataLayer and HTML for image extraction
                        gtm_data = await page.evaluate("() => JSON.stringify(window.gtmDataLayer || [])")
                        html = await page.content()

                        # Combine GTM data and HTML in a dict for parsing
                        combined_data = json.dumps({
                            "gtm": json.loads(gtm_data),
                            "html": html
                        })
                        pages_data.append(combined_data)

                        logger.info(f"  Fetched GTM data and HTML ({len(combined_data)} chars)")

                    finally:
                        await page.close()

                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    continue

        finally:
            # Cleanup browser resources
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info(f"Browser closed for {self.chain}")

        logger.info(f"Fetched data from {len(pages_data)} categories")
        return pages_data

    async def parse_products(self, payload: str) -> List[dict]:
        """
        Parse products from combined GTM dataLayer and HTML.

        Args:
            payload: JSON string containing both GTM data and HTML

        Returns:
            List of product dictionaries
        """
        products = []

        try:
            # Parse combined data
            data = json.loads(payload)
            gtm_data = data.get('gtm', [])
            html = data.get('html', '')

            if not isinstance(gtm_data, list):
                logger.warning("GTM dataLayer is not a list")
                return products

            # Extract images from HTML (keyed by product ID)
            images_by_id = self._extract_images_from_html(html)

            # Find product impression events
            for event in gtm_data:
                if not isinstance(event, dict):
                    continue

                if event.get('event') == 'productListImpression':
                    ecommerce = event.get('ecommerce', {})
                    impressions = ecommerce.get('impressions', [])

                    for item in impressions:
                        product = self._parse_gtm_product(item, images_by_id)
                        if product:
                            products.append(product)

            logger.info(f"Parsed {len(products)} products from GTM dataLayer")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse combined data JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing products: {e}")

        return products

    def _normalize_name(self, name: str) -> str:
        """
        Normalize product name for matching between HTML and GTM data.

        Args:
            name: Raw product name

        Returns:
            Normalized name (lowercase, no extra whitespace, standardized volume format)
        """
        import re

        # Remove newlines, extra spaces, convert to lowercase
        normalized = ' '.join(name.replace('\n', ' ').split()).lower()

        # Normalize volume format: "12 x 330ml" -> "12x330ml"
        normalized = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1x\2', normalized)

        return normalized

    def _normalize_name_without_volume(self, name: str) -> str:
        """
        Normalize name and remove volume information for fuzzy matching.

        Args:
            name: Raw product name

        Returns:
            Normalized name without volume info
        """
        import re

        normalized = self._normalize_name(name)

        # Remove volume patterns (12x330ml, 330ml, 6pk, etc.)
        normalized = re.sub(r'\b\d+x\d+ml\b', '', normalized)
        normalized = re.sub(r'\b\d+ml\b', '', normalized)
        normalized = re.sub(r'\b\d+l\b', '', normalized)
        normalized = re.sub(r'\b\d+pk\b', '', normalized)

        # Clean up extra spaces
        normalized = ' '.join(normalized.split())

        return normalized

    def _extract_images_from_html(self, html: str) -> dict:
        """
        Extract product images from HTML, keyed by normalized product name.

        Args:
            html: Page HTML content

        Returns:
            Dictionary mapping normalized product names (with and without volume) to image URLs
        """
        images = {}
        tree = HTMLParser(html)

        # Bottle O uses .talker elements for product cards
        for talker in tree.css('.talker'):
            # Find the image
            img = talker.css_first('img[src], img[data-src]')
            if not img:
                continue

            src = img.attributes.get('src') or img.attributes.get('data-src')
            if not src or 'placeholder' in src.lower():
                continue

            # Ensure absolute URL
            if not src.startswith('http'):
                if src.startswith('//'):
                    src = f"https:{src}"
                else:
                    src = f"https://thebottleo.co.nz{src}"

            # Extract product name and store under multiple normalized keys
            name_elem = talker.css_first('.talker__name')
            if name_elem:
                product_name = name_elem.text().strip()
                if product_name:
                    # Store with full normalized name
                    normalized_full = self._normalize_name(product_name)
                    images[normalized_full] = src

                    # Also store without volume for fuzzy matching
                    normalized_no_volume = self._normalize_name_without_volume(product_name)
                    if normalized_no_volume and normalized_no_volume not in images:
                        images[normalized_no_volume] = src

        logger.debug(f"Extracted {len(images)} image URLs from HTML")
        return images

    def _parse_gtm_product(self, item: dict, images_by_id: dict) -> dict | None:
        """
        Parse a single product from GTM dataLayer impression.

        Args:
            item: Product impression data from GTM
            images_by_id: Dictionary mapping product IDs to image URLs

        Returns:
            Product dictionary or None if invalid
        """
        try:
            # Extract basic fields from GTM data
            source_id = item.get('id', '')
            name = item.get('name', '')
            price = item.get('price')
            brand = item.get('brand', '')
            category = item.get('category', '')

            if not name or not source_id or price is None:
                logger.debug(f"Skipping product with missing required fields: {item}")
                return None

            # Convert price to float
            if isinstance(price, str):
                price = float(price.replace('$', '').replace(',', ''))
            else:
                price = float(price)

            # Use GTM brand/category if available, otherwise infer
            if not brand:
                brand = infer_brand(name)
            if not category:
                category = infer_category(name)

            # Parse volume and ABV from product name
            volume = parse_volume(name)
            abv = extract_abv(name)

            # Extract promotional pricing from GTM data
            promo_price = None
            promo_text = None
            promo_ends_at = None
            is_member_only = False

            # Check GTM for promo fields (Bottle O may include these in dataLayer)
            if item.get('discount'):
                discount_text = str(item['discount'])
                promo_text = discount_text[:255]

                # Try to extract promo price from discount text
                extracted_price = parse_promo_price(discount_text)
                if extracted_price and extracted_price < price:
                    promo_price = extracted_price

            if item.get('promotion'):
                promo_text_raw = str(item['promotion'])
                promo_text = promo_text_raw[:255]

                # Parse for multi-buy deals
                multi_buy = parse_multi_buy_deal(promo_text_raw)
                if multi_buy:
                    if multi_buy.get('unit_price'):
                        promo_price = multi_buy['unit_price']
                    promo_text = multi_buy['deal_text'][:255]

                # Parse promo end date
                promo_ends_at = parse_promo_end_date(promo_text_raw)

            if item.get('coupon'):
                coupon_text = str(item['coupon'])
                is_member_only = detect_member_only(coupon_text)
                if not promo_text:
                    promo_text = coupon_text[:255]

            # Check for price vs original_price (was price scenario)
            if item.get('original_price') or item.get('was_price'):
                old_price_val = item.get('original_price') or item.get('was_price')
                if isinstance(old_price_val, str):
                    old_price = float(old_price_val.replace('$', '').replace(',', ''))
                else:
                    old_price = float(old_price_val)

                if price < old_price and not promo_price:
                    promo_price = price
                    price = old_price
                    if not promo_text:
                        promo_text = "Special"[:255]

            # Construct product URL
            url = f"https://thebottleo.co.nz/products/{source_id}"

            # Get image URL from HTML extraction - try multiple matching strategies
            # 1. Try exact normalized match
            normalized_name = self._normalize_name(name)
            image_url = images_by_id.get(normalized_name)

            # 2. If no match, try without volume information
            if not image_url:
                normalized_no_volume = self._normalize_name_without_volume(name)
                image_url = images_by_id.get(normalized_no_volume)

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


__all__ = ["BottleOScraper"]
