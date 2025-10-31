from __future__ import annotations

import pathlib
from datetime import datetime
from typing import List

from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume

FIXTURE = pathlib.Path(__file__).with_suffix(".py").with_name("fixtures/countdown.html")


class CountdownScraper(Scraper):
    chain = "countdown"

    def __init__(self, chain: str = "countdown") -> None:
        super().__init__()
        self.chain = chain

    async def fetch_catalog_pages(self) -> List[str]:
        return [FIXTURE.read_text()]  # In production would fetch via HTTP

    async def parse_products(self, payload: str) -> List[dict]:
        tree = HTMLParser(payload)
        products: List[dict] = []
        for node in tree.css("div.product"):
            name = node.css_first("h2").text().strip()
            price_text = node.css_first("span.price").text()
            price = float(price_text.replace("$", ""))
            promo_node = node.css_first("span.promo")
            promo_price = None
            promo_text = None
            promo_ends_at = None
            if promo_node:
                promo_text = promo_node.text(strip=True)
                extracted_price = ''.join(ch for ch in promo_text if ch.isdigit() or ch == '.')
                if extracted_price:
                    promo_price = float(extracted_price)
                if promo_node.attributes.get("data-ends"):
                    promo_ends_at = datetime.fromisoformat(promo_node.attributes["data-ends"])
            volume = parse_volume(name)
            products.append(
                {
                    "chain": self.chain,
                    "source_id": node.attributes.get("data-id", name),
                    "name": name,
                    "price_nzd": price,
                    "promo_price_nzd": promo_price,
                    "promo_text": promo_text,
                    "promo_ends_at": promo_ends_at,
                    "pack_count": volume.pack_count,
                    "unit_volume_ml": volume.unit_volume_ml,
                    "total_volume_ml": volume.total_volume_ml,
                    "abv_percent": extract_abv(name),
                    "url": node.css_first("a.link").attributes.get("href"),
                }
            )
        return products


__all__ = ["CountdownScraper"]
