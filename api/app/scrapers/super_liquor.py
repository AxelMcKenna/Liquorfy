from __future__ import annotations

import pathlib
from typing import List

from selectolax.parser import HTMLParser

from app.scrapers.base import Scraper
from app.services.parser_utils import extract_abv, parse_volume

FIXTURE = pathlib.Path(__file__).with_suffix(".py").with_name("fixtures/super_liquor.html")


class SuperLiquorScraper(Scraper):
    chain = "super_liquor"

    def __init__(self, chain: str = "super_liquor") -> None:
        super().__init__()
        self.chain = chain

    async def fetch_catalog_pages(self) -> List[str]:
        return [FIXTURE.read_text()]

    async def parse_products(self, payload: str) -> List[dict]:
        tree = HTMLParser(payload)
        products: List[dict] = []
        for node in tree.css("div.item"):
            name = node.css_first("span.title").text()
            price_text = node.css_first("span.price").text()
            price = float(price_text.replace("$", ""))
            abv_text = node.css_first("span.abv").text() if node.css_first("span.abv") else ""
            volume = parse_volume(name)
            abv = extract_abv(name) or extract_abv(abv_text)
            products.append(
                {
                    "chain": self.chain,
                    "source_id": node.attributes.get("data-sku", name),
                    "name": name,
                    "price_nzd": price,
                    "promo_price_nzd": None,
                    "promo_text": None,
                    "pack_count": volume.pack_count,
                    "unit_volume_ml": volume.unit_volume_ml,
                    "total_volume_ml": volume.total_volume_ml,
                    "abv_percent": abv,
                }
            )
        return products


__all__ = ["SuperLiquorScraper"]
