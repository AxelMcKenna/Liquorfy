from __future__ import annotations

import pathlib
from typing import List

from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume

FIXTURE = pathlib.Path(__file__).with_suffix(".py").with_name("fixtures/liquorland.html")


class LiquorlandScraper(Scraper):
    chain = "liquorland"

    def __init__(self, chain: str = "liquorland") -> None:
        super().__init__()
        self.chain = chain

    async def fetch_catalog_pages(self) -> List[str]:
        return [FIXTURE.read_text()]

    async def parse_products(self, payload: str) -> List[dict]:
        tree = HTMLParser(payload)
        products: List[dict] = []
        for node in tree.css("article"):
            name = node.css_first("h3").text()
            price_text = node.css_first("p.price").text()
            price = float(price_text.replace("$", ""))
            promo_node = node.css_first("p.promo")
            promo_text = promo_node.text(strip=True) if promo_node else None
            promo_price = None
            if promo_text and "for" in promo_text:
                parts = promo_text.lower().split("for")
                amount = ''.join(ch for ch in parts[1] if ch.isdigit() or ch == '.')
                count = ''.join(ch for ch in parts[0] if ch.isdigit())
                if amount and count:
                    promo_price = float(amount) / int(count)
            volume = parse_volume(name)
            abv = extract_abv(name)
            products.append(
                {
                    "chain": self.chain,
                    "source_id": node.attributes.get("data-sku", name),
                    "name": name,
                    "price_nzd": price,
                    "promo_price_nzd": promo_price,
                    "promo_text": promo_text,
                    "pack_count": volume.pack_count,
                    "unit_volume_ml": volume.unit_volume_ml,
                    "total_volume_ml": volume.total_volume_ml,
                    "abv_percent": abv,
                    "image_url": node.css_first("img").attributes.get("src") if node.css_first("img") else None,
                }
            )
        return products


__all__ = ["LiquorlandScraper"]
