from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.scrapers.base import Scraper

FIXTURE = Path(__file__).parent / "fixtures" / "stub.json"



class StubScraper(Scraper):
    def __init__(self, chain: str) -> None:
        super().__init__()
        self.chain = chain

    async def fetch_catalog_pages(self) -> List[str]:
        return [FIXTURE.read_text()]

    async def parse_products(self, payload: str) -> List[dict]:
        items = json.loads(payload)
        for item in items:
            item["chain"] = self.chain
        return items


__all__ = ["StubScraper"]
