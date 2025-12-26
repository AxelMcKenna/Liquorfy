from __future__ import annotations

import logging
import pathlib
from datetime import datetime
from pathlib import Path
from typing import List

from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume, infer_brand, infer_category
from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
)

FIXTURE = Path(__file__).parent / "fixtures" / "countdown.html"

logger = logging.getLogger(__name__)


class CountdownScraper(Scraper):
    chain = "countdown"
    # Example catalog URLs - in production these would be real Countdown URLs
    catalog_urls = [
        "https://www.countdown.co.nz/shop/browse/beer-cider-wine",
    ]

    def __init__(self, chain: str = "countdown", use_fixtures: bool = True) -> None:
        super().__init__(use_fixtures=use_fixtures)
        self.chain = chain

    async def fetch_catalog_pages(self) -> List[str]:
        """Fetch catalog pages from fixtures or live HTTP."""
        if self.use_fixtures:
            logger.info(f"Using fixture data for {self.chain}")
            return [FIXTURE.read_text()]

        # Fetch from real URLs
        logger.info(f"Fetching live data from {len(self.catalog_urls)} URLs")
        pages = []
        for url in self.catalog_urls:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                pages.append(response.text)
                logger.info(f"Fetched {url}")
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
        return pages

    async def parse_products(self, payload: str) -> List[dict]:
        tree = HTMLParser(payload)
        products: List[dict] = []
        for node in tree.css("div.product"):
            name = node.css_first("h2").text().strip()
            price_text = node.css_first("span.price").text()
            price = float(price_text.replace("$", ""))

            # Extract promotional pricing
            promo_price = None
            promo_text = None
            promo_ends_at = None
            is_member_only = False

            # Look for promo elements
            promo_node = (
                node.css_first("span.promo") or
                node.css_first(".badge-promo") or
                node.css_first(".special-price") or
                node.css_first("[class*='promo']") or
                node.css_first("[class*='special']") or
                node.css_first("[class*='deal']")
            )

            if promo_node:
                promo_raw_text = promo_node.text(strip=True)
                if promo_raw_text:
                    promo_text = promo_raw_text[:255]

                    # Use promo_utils to extract price
                    extracted_price = parse_promo_price(promo_raw_text)
                    if extracted_price and extracted_price < price:
                        promo_price = extracted_price

                    # Check for multi-buy deals
                    multi_buy = parse_multi_buy_deal(promo_raw_text)
                    if multi_buy:
                        if multi_buy.get('unit_price'):
                            promo_price = multi_buy['unit_price']
                        promo_text = multi_buy['deal_text'][:255]

                    # Parse end date from text or attribute
                    if promo_node.attributes.get("data-ends"):
                        promo_ends_at = datetime.fromisoformat(promo_node.attributes["data-ends"])
                    else:
                        promo_ends_at = parse_promo_end_date(promo_raw_text)

                    # Check if member-only
                    is_member_only = detect_member_only(promo_raw_text)

            # Check for was-price scenario
            was_price_node = (
                node.css_first(".was-price") or
                node.css_first(".old-price") or
                node.css_first("[class*='was']")
            )

            if was_price_node and not promo_price:
                import re
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

            # Extract image URL (avoid badge images)
            image_url = None
            img_nodes = node.css("img")

            # Badge keywords to filter out
            BADGE_KEYWORDS = [
                "low-carb", "gluten", "vegan", "organic", "badge", "icon",
                "promo", "deal", "offer", "special", "2for", "3for", "buy", "save",
                "2 for", "3 for", "multi", "multipack", "_100", "_50", "label",
                "zero", "sugar", "zero-sugar", "no-sugar"
            ]

            for img_node in img_nodes:
                # Check for lazy-loaded images (data-src) or regular src
                img_url = img_node.attributes.get("data-src") or img_node.attributes.get("src")
                if img_url:
                    # Skip badge images
                    img_url_lower = img_url.lower()
                    if any(badge in img_url_lower for badge in BADGE_KEYWORDS):
                        continue
                    # Use the first non-badge image
                    image_url = img_url
                    break

            volume = parse_volume(name)
            brand = infer_brand(name)
            category = infer_category(name)

            products.append(
                {
                    "chain": self.chain,
                    "source_id": node.attributes.get("data-id", name),
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
                    "abv_percent": extract_abv(name),
                    "url": node.css_first("a.link").attributes.get("href"),
                    "image_url": image_url,
                }
            )
        return products


__all__ = ["CountdownScraper"]
