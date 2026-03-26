from __future__ import annotations

from typing import Dict, Type

from app.scrapers.base import Scraper
from app.scrapers.black_bull import BlackBullScraper
from app.scrapers.bottle_o import BottleOScraper
from app.scrapers.countdown_api import CountdownAPIScraper  # Using API-based scraper
from app.scrapers.glengarry import GlengarryScraper
from app.scrapers.liquorland import LiquorlandScraper
from app.scrapers.liquor_centre import LiquorCentreScraper
from app.scrapers.new_world_api import NewWorldAPIScraper  # Using API-based scraper
from app.scrapers.paknsave_api import PakNSaveAPIScraper  # Using API-based scraper
from app.scrapers.super_liquor import SuperLiquorScraper
from app.scrapers.thirsty_liquor import ThirstyLiquorScraper

CHAINS: Dict[str, Type[Scraper]] = {
    # Fast API-based scrapers first (~3-18 min each)
    "black_bull": BlackBullScraper,
    "thirsty_liquor": ThirstyLiquorScraper,
    "countdown": CountdownAPIScraper,
    "glengarry": GlengarryScraper,
    "paknsave": PakNSaveAPIScraper,
    "new_world": NewWorldAPIScraper,
    # Slower browser-based scrapers last (~40-160 min each)
    "super_liquor": SuperLiquorScraper,
    "liquor_centre": LiquorCentreScraper,
    "liquorland": LiquorlandScraper,
    "bottle_o": BottleOScraper,
}


def get_chain_scraper(chain: str) -> Scraper:
    scraper_cls = CHAINS.get(chain)
    if not scraper_cls:
        raise ValueError(f"Unknown chain: {chain}")
    return scraper_cls()


__all__ = ["get_chain_scraper", "CHAINS"]
