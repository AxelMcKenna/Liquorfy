"""
PakNSave API-based scraper using their internal product search API.
Much faster and more reliable than HTML scraping.

Inherits from FoodstuffsAPIScraper as New World and PakNSave share the same API infrastructure.
"""
from __future__ import annotations

from app.scrapers.foodstuffs_base import FoodstuffsAPIScraper


class PakNSaveAPIScraper(FoodstuffsAPIScraper):
    """API-based scraper for PakNSave NZ using their internal product API."""

    chain = "paknsave"
    site_url = "https://www.paknsave.co.nz/shop/category/beer-wine-and-cider/beer"
    api_domain = "api-prod.paknsave.co.nz"
    api_url = "https://api-prod.paknsave.co.nz/v1/edge/search/paginated/products"
    default_store_id = "e1925ea7-01bc-4358-ae7c-c6502da5ab12"  # Royal Oak Auckland
    store_data_file = "paknsave_stores.json"


__all__ = ["PakNSaveAPIScraper"]
