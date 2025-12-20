"""
Liquorland scraper using Playwright for JavaScript-rendered content.
"""
from __future__ import annotations

import logging
import re
from typing import List

from playwright.async_api import Page
from selectolax.parser import HTMLParser

from app.scrapers.browser_base import BrowserScraper
from app.services.parser_utils import extract_abv, parse_volume

logger = logging.getLogger(__name__)


class LiquorlandScraper(BrowserScraper):
    chain = "liquorland"
    catalog_urls = [
        # Beer & Cider
        "https://www.liquorland.co.nz/beer",
        "https://www.liquorland.co.nz/craft-beer",
        "https://www.liquorland.co.nz/cider",
        # Wine
        "https://www.liquorland.co.nz/wine",
        "https://www.liquorland.co.nz/wine/red",
        "https://www.liquorland.co.nz/wine/white",
        "https://www.liquorland.co.nz/wine/rose",
        "https://www.liquorland.co.nz/wine/sparkling",
        # Spirits
        "https://www.liquorland.co.nz/spirits",
        "https://www.liquorland.co.nz/spirits/whisky",
        "https://www.liquorland.co.nz/spirits/gin",
        "https://www.liquorland.co.nz/spirits/vodka",
        "https://www.liquorland.co.nz/spirits/rum",
        # RTDs
        "https://www.liquorland.co.nz/rtd",
    ]

    async def wait_for_content(self, page: Page) -> None:
        """Wait for Liquorland products to load."""
        try:
            # Wait for product grid to appear
            await page.wait_for_selector('.s-product', timeout=10000)
            # Wait a moment for all products to render
            await page.wait_for_load_state('networkidle', timeout=15000)
        except Exception as e:
            logger.warning(f"Timeout waiting for products: {e}")
            # Continue anyway, we might still get some data

    async def extract_total_pages(self, html: str) -> int:
        """Extract total pages from Liquorland pagination."""
        tree = HTMLParser(html)

        # Look for pagination elements
        # Liquorland typically uses numbered page links
        page_links = tree.css('a.s-pagination__link')
        if page_links:
            page_numbers = []
            for link in page_links:
                text = link.text().strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                return max(page_numbers)

        # Fallback: check for "next" button existence
        next_button = tree.css_first('a.s-pagination__link--next')
        if next_button:
            return 2  # At least 2 pages

        return 1

    def get_page_url(self, base_url: str, page_num: int) -> str:
        """Construct Liquorland page URL."""
        # Liquorland uses ?page=N format
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

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
                if pricing_section and 'no-cta' in pricing_section.attributes.get('class', ''):
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

                # Extract image
                img_node = node.css_first('img')
                image_url = None
                if img_node:
                    image_url = (
                        img_node.attributes.get('src') or
                        img_node.attributes.get('data-src') or
                        img_node.attributes.get('data-lazy-src')
                    )
                    if image_url and not image_url.startswith('http'):
                        image_url = f"https://www.liquorland.co.nz{image_url}"

                # Extract product ID from URL
                source_id = url.split('/')[-1] if url else name

                # Parse volume and ABV from name
                volume = parse_volume(name)
                abv = extract_abv(name)

                products.append({
                    "chain": self.chain,
                    "source_id": source_id,
                    "name": name,
                    "price_nzd": price,
                    "promo_price_nzd": None,  # TODO: Extract promo pricing
                    "promo_text": None,
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
