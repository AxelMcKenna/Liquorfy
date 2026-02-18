"""
Glengarry scraper for liquor products using browser automation.
Glengarry is a specialist wine and spirits retailer in NZ.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import List
from urllib.parse import urljoin

from playwright.async_api import Page
from selectolax.parser import HTMLParser

from app.scrapers.browser_base import BrowserScraper
from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
)

logger = logging.getLogger(__name__)


class GlengarryScraper(BrowserScraper):
    """Browser-based scraper for Glengarry NZ website."""

    chain = "glengarry"

    # Glengarry catalog sections.
    # /beer is a landing page (4 products) - use JSP sub-category URLs instead.
    # ?page=N is ignored by Glengarry, so pagination returns same page.
    # Each JSP sub-category shows up to 75 products.
    catalog_urls = [
        # Wine
        "https://www.glengarrywines.co.nz/wine/red",
        "https://www.glengarrywines.co.nz/wine/white",
        "https://www.glengarrywines.co.nz/wine/rose",
        "https://www.glengarrywines.co.nz/champagne",
        # Beer - Mainstream
        "https://www.glengarrywines.co.nz/beercider.jsp?style=ale&variety=main stream",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=lager&variety=main stream",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=pale ale&variety=main stream",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=stout&variety=main stream",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=other&variety=main stream",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=low/ no alcohol&variety=main stream",
        # Beer - Craft
        "https://www.glengarrywines.co.nz/beercider.jsp?style=ale&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=lager&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=pale ale&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=pilsner&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=stout&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=dark&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=bitter&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=sours&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=other&variety=craft",
        "https://www.glengarrywines.co.nz/beercider.jsp?style=low/ no alcohol&variety=craft",
        # Spirits
        "https://www.glengarrywines.co.nz/spirits/whisky",
        "https://www.glengarrywines.co.nz/spirits/gin",
        "https://www.glengarrywines.co.nz/spirits/vodka",
        "https://www.glengarrywines.co.nz/spirits/rum",
        # Specials
        "https://www.glengarrywines.co.nz/specials",
    ]

    async def wait_for_content(self, page: Page) -> None:
        """Wait for product grid to load."""
        try:
            # Wait for Glengarry's specific product elements
            await page.wait_for_selector('.productDisplaySlot', timeout=10000)
            # Extra wait for dynamic content
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Timeout waiting for products: {e}")
            await asyncio.sleep(3)

    async def extract_total_pages(self, html: str) -> int:
        """
        Extract total number of pages from pagination.

        Args:
            html: Page HTML content

        Returns:
            Total number of pages (defaults to 1 if not found)
        """
        tree = HTMLParser(html)

        # Look for pagination - Glengarry might use different selectors
        pagination_selectors = [
            '.pagination',
            '.pager',
            '[class*="pagination"]',
            'nav.pagination',
        ]

        for selector in pagination_selectors:
            pagination = tree.css(selector)
            if pagination:
                page_links = pagination[0].css('a')
                max_page = 1
                for link in page_links:
                    text = link.text(strip=True)
                    # Extract numbers from text
                    if text.isdigit():
                        max_page = max(max_page, int(text))
                if max_page > 1:
                    return max_page

        return 1

    def get_page_url(self, base_url: str, page_num: int) -> str:
        """
        Construct URL for a specific page number.

        Args:
            base_url: Base category URL
            page_num: Page number

        Returns:
            URL with page parameter
        """
        # Glengarry typically uses ?page=N or /page/N format
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

    async def parse_products(self, html: str) -> List[dict]:
        """
        Parse products from Glengarry HTML.

        Args:
            html: Page HTML content

        Returns:
            List of product dictionaries
        """
        tree = HTMLParser(html)
        products: List[dict] = []

        # Glengarry uses specific class names
        product_cards = tree.css('.productDisplaySlot')

        if not product_cards:
            logger.warning("No product cards found with .productDisplaySlot selector")
            return products

        logger.info(f"Found {len(product_cards)} products using Glengarry selector")

        for card in product_cards:
            try:
                # Extract brand from .fontProductHead
                brand_elem = card.css_first('.fontProductHead a')
                brand_name = brand_elem.text(strip=True) if brand_elem else ""

                # Extract product name from .fontProductHeadSub
                name_elem = card.css_first('.fontProductHeadSub a')
                if not name_elem:
                    continue

                product_name = name_elem.text(strip=True)

                # Full name: Brand + Product Name
                name = f"{brand_name} {product_name}".strip() if brand_name else product_name

                # Extract price from .productDisplayPrice
                # Glengarry shows "WAS $X.XX" and "NOW $X.XX" for sales
                price = None
                promo_price = None
                promo_text = None

                price_container = card.css_first('.productDisplayPrice')
                if not price_container:
                    continue

                # Look for "WAS" price (original price)
                was_price_elem = price_container.css_first('.fontProductPriceSub')
                now_price_elem = price_container.css_first('.fontProductPrice')

                if was_price_elem and now_price_elem:
                    # On sale: WAS/NOW pricing
                    was_text = was_price_elem.text(strip=True)
                    now_text = now_price_elem.text(strip=True)

                    # Extract WAS price as original
                    was_match = re.search(r'[\d.]+', was_text.replace(',', ''))
                    now_match = re.search(r'[\d.]+', now_text.replace(',', ''))

                    if was_match and now_match:
                        price = float(was_match.group())
                        promo_price = float(now_match.group())
                        promo_text = f"Sale: Was ${price:.2f}, Now ${promo_price:.2f}"[:255]
                elif now_price_elem:
                    # Regular price only
                    now_text = now_price_elem.text(strip=True)
                    now_match = re.search(r'[\d.]+', now_text.replace(',', ''))
                    if now_match:
                        price = float(now_match.group())
                else:
                    # Try any price element
                    price_text = price_container.text(strip=True)
                    price_match = re.search(r'[\d.]+', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group())

                if not price:
                    continue

                # Promo date and member-only detection
                promo_ends_at = None
                is_member_only = False

                # Check for promo badges (multi-buy deals, specials)
                badge_elem = (
                    card.css_first('.productDisplayBadge')
                    or card.css_first('[class*="badge"]')
                    or card.css_first('[class*="promo"]')
                    or card.css_first('[class*="special"]')
                )
                if badge_elem:
                    badge_text = badge_elem.text(strip=True)
                    if badge_text:
                        # Check for multi-buy deals first
                        multi_buy = parse_multi_buy_deal(badge_text)
                        if multi_buy:
                            if multi_buy.get('unit_price'):
                                promo_price = multi_buy['unit_price']
                            promo_text = multi_buy['deal_text'][:255]
                        elif not promo_text:
                            # Regular badge promo
                            promo_text = badge_text[:255]
                            extracted = parse_promo_price(badge_text)
                            if extracted and extracted < price:
                                promo_price = extracted

                        promo_ends_at = parse_promo_end_date(badge_text)
                        is_member_only = detect_member_only(badge_text)

                # Check for additional promo info in productDisplayInfo
                info_elem = card.css_first('.productDisplayInfo')
                if info_elem:
                    info_text = info_elem.text(strip=True)
                    if not promo_ends_at:
                        promo_ends_at = parse_promo_end_date(info_text)
                    if not is_member_only:
                        is_member_only = detect_member_only(info_text)

                # Extract image URL using helper
                image_url = self.extract_image_url(
                    card,
                    'https://www.glengarrywines.co.nz',
                    selectors=['img.productDisplayImage', 'img']
                )

                # Extract product URL from .fontProductHeadSub a
                url = None
                if name_elem:
                    url = name_elem.attributes.get('href')
                    if url and not url.startswith('http'):
                        url = urljoin('https://www.glengarrywines.co.nz', url)

                # Extract product ID from URL (e.g., /items/91118/...)
                source_id = None
                if url:
                    id_match = re.search(r'/items/(\d+)/', url)
                    if id_match:
                        source_id = id_match.group(1)

                if not source_id:
                    # Try from image URL
                    if image_url:
                        img_match = re.search(r'/bottles/(\d+)\.png', image_url)
                        if img_match:
                            source_id = img_match.group(1)

                if not source_id:
                    source_id = name  # Fallback to name

                # Use standardized product dict builder
                product = self.build_product_dict(
                    source_id=source_id,
                    name=name,
                    price_nzd=price,
                    promo_price_nzd=promo_price,
                    promo_text=promo_text,
                    promo_ends_at=promo_ends_at,
                    is_member_only=is_member_only,
                    url=url,
                    image_url=image_url,
                )

                products.append(product)

            except Exception as e:
                logger.error(f"Error parsing product card: {e}")
                continue

        logger.info(f"Successfully parsed {len(products)} products from Glengarry")
        return products


__all__ = ["GlengarryScraper"]
