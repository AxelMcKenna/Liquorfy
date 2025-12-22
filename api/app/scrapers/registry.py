from __future__ import annotations

from typing import Dict, Type

from app.scrapers.base import Scraper
from app.scrapers.countdown import CountdownScraper
from app.scrapers.liquorland import LiquorlandScraper
from app.scrapers.liquor_centre import LiquorCentreScraper
from app.scrapers.super_liquor import SuperLiquorScraper
from app.scrapers.stub import StubScraper

CHAINS: Dict[str, Type[Scraper]] = {
    "countdown": CountdownScraper,
    "liquorland": LiquorlandScraper,
    "liquor_centre": LiquorCentreScraper,
    "super_liquor": SuperLiquorScraper,
    "new_world": StubScraper,
    "paknsave": StubScraper,
    "bottle_o": StubScraper,
    "glengarry": StubScraper,
}


def get_chain_scraper(chain: str) -> Scraper:
    scraper_cls = CHAINS.get(chain)
    if not scraper_cls:
        raise ValueError(f"Unknown chain: {chain}")
    return scraper_cls(chain)


__all__ = ["get_chain_scraper", "CHAINS"]
