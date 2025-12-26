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
    "countdown": CountdownAPIScraper,  # API-based scraper
    "liquorland": LiquorlandScraper,
    "liquor_centre": LiquorCentreScraper,
    "super_liquor": SuperLiquorScraper,
    "bottle_o": BottleOScraper,
    "new_world": NewWorldAPIScraper,  # API-based scraper
    "paknsave": PakNSaveAPIScraper,  # API-based scraper
    "glengarry": GlengarryScraper,
    "thirsty_liquor": ThirstyLiquorScraper,  # Shopify API-based scraper
    "black_bull": BlackBullScraper,  # Shopify API-based, limited coverage (3 stores)
}


def get_chain_scraper(chain: str) -> Scraper:
    scraper_cls = CHAINS.get(chain)
    if not scraper_cls:
        raise ValueError(f"Unknown chain: {chain}")
    return scraper_cls()


__all__ = ["get_chain_scraper", "CHAINS"]
