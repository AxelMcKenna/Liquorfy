"""
New World API-based scraper using their internal product search API.
Much faster and more reliable than HTML scraping.

Inherits from FoodstuffsAPIScraper as New World and PakNSave share the same API infrastructure.
"""
from __future__ import annotations

from app.scrapers.foodstuffs_base import FoodstuffsAPIScraper


class NewWorldAPIScraper(FoodstuffsAPIScraper):
    """API-based scraper for New World NZ using their internal product API."""

    chain = "new_world"
    site_url = "https://www.newworld.co.nz/shop/category/beer-wine-and-cider/beer"
    api_domain = "api-prod.newworld.co.nz"
    api_url = "https://api-prod.newworld.co.nz/v1/edge/search/paginated/products"
    default_store_id = "60928d93-06fa-4d8f-92a6-8c359e7e846d"  # Auckland
    store_data_file = "newworld_stores.json"


__all__ = ["NewWorldAPIScraper"]
