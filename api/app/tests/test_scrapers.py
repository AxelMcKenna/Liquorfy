import os
import pytest

from app.scrapers.countdown_api import CountdownAPIScraper
from app.scrapers.liquorland import LiquorlandScraper
from app.scrapers.super_liquor import SuperLiquorScraper

# Skip tests if Playwright browsers aren't installed
# These are live integration tests that hit real websites
def _check_playwright_browsers():
    """Check if Playwright browsers are actually installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # executable_path returns where browser SHOULD be, check if it exists
            path = p.chromium.executable_path
            return os.path.exists(path)
    except Exception:
        return False

PLAYWRIGHT_AVAILABLE = _check_playwright_browsers()

requires_playwright = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright browsers not installed (run: playwright install)"
)


@requires_playwright
@pytest.mark.asyncio
async def test_countdown_scraper_parses_products():
    """Test that Countdown API scraper can fetch and parse products."""
    scraper = CountdownAPIScraper()
    # API-based scrapers use scrape() method directly, not fetch_catalog_pages/parse_products
    products = await scraper.scrape()
    # Verify we got some products
    assert len(products) > 0
    # Verify products have required fields
    assert all("name" in p for p in products)
    assert all("price_nzd" in p for p in products)


@requires_playwright
@pytest.mark.asyncio
async def test_liquorland_scraper_promo_price():
    """Test that Liquorland scraper can parse products and prices."""
    scraper = LiquorlandScraper()
    page = (await scraper.fetch_catalog_pages())[0]
    products = await scraper.parse_products(page)

    # Verify we got some products
    assert len(products) > 0, "Expected at least one product"

    # Verify all products have required price fields
    for product in products:
        assert "price_nzd" in product
        assert product["price_nzd"] > 0

    # If there are promo products, verify promo price is less than regular price
    promo_products = [p for p in products if p.get("promo_price_nzd") is not None]
    if promo_products:
        assert promo_products[0]["promo_price_nzd"] < promo_products[0]["price_nzd"]


@requires_playwright
@pytest.mark.asyncio
async def test_super_liquor_scraper_abv():
    """Test that Super Liquor scraper can parse ABV when present in product names."""
    scraper = SuperLiquorScraper()
    page = (await scraper.fetch_catalog_pages())[0]
    products = await scraper.parse_products(page)

    # Verify we got some products
    assert len(products) > 0, "Expected at least one product"

    # First product in fixture is "Asahi Super Dry 0.0% Alcohol Free" (0.0% ABV)
    # This verifies that ABV extraction works when explicitly stated in the name
    assert products[0]["name"].lower().count("0.0%") > 0
    assert products[0]["abv_percent"] == pytest.approx(0.0)

    # Note: ABV may be None for products where it's not in the name/description
    # This is expected behavior - ABV is extracted when available in the text
