import pytest

from app.scrapers.countdown import CountdownScraper
from app.scrapers.liquorland import LiquorlandScraper
from app.scrapers.super_liquor import SuperLiquorScraper


@pytest.mark.asyncio
async def test_countdown_scraper_parses_products():
    scraper = CountdownScraper("countdown")
    pages = await scraper.fetch_catalog_pages()
    products = await scraper.parse_products(pages[0])
    assert any(p["total_volume_ml"] == 1000 for p in products)


@pytest.mark.asyncio
async def test_liquorland_scraper_promo_price():
    scraper = LiquorlandScraper("liquorland")
    page = (await scraper.fetch_catalog_pages())[0]
    products = await scraper.parse_products(page)
    promo_product = products[0]
    assert pytest.approx(promo_product["promo_price_nzd"], 0.01) == 30.0


@pytest.mark.asyncio
async def test_super_liquor_scraper_abv():
    scraper = SuperLiquorScraper("super_liquor")
    page = (await scraper.fetch_catalog_pages())[0]
    products = await scraper.parse_products(page)
    assert products[0]["abv_percent"] == pytest.approx(4.5)
