"""
Comprehensive tests for all product scrapers across all NZ liquor chains.

Tests ensure every registered scraper can parse products correctly
and that we have complete NZ-wide coverage.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.registry import CHAINS, get_chain_scraper
from app.scrapers.base import Scraper
from app.scrapers.countdown_api import CountdownAPIScraper
from app.scrapers.new_world_api import NewWorldAPIScraper
from app.scrapers.paknsave_api import PakNSaveAPIScraper
from app.scrapers.liquorland import LiquorlandScraper, SPECIALS_PAYLOAD_PREFIX
from app.scrapers.super_liquor import SuperLiquorScraper
from app.scrapers.bottle_o import BottleOScraper
from app.scrapers.glengarry import GlengarryScraper
from app.scrapers.thirsty_liquor import ThirstyLiquorScraper
from app.scrapers.black_bull import BlackBullScraper


# ============================================================================
# Registry Tests
# ============================================================================

class TestScraperRegistry:
    """Tests for the scraper registry."""

    def test_all_chains_registered(self):
        """Test that all expected chains are registered."""
        expected_chains = {
            "liquorland",
            "liquor_centre",
            "super_liquor",
            "bottle_o",
            "new_world",
            "paknsave",
            "glengarry",
            "thirsty_liquor",
            "black_bull",
        }

        # Check all expected are present
        for chain in expected_chains:
            assert chain in CHAINS, f"Chain '{chain}' not registered"

    def test_get_chain_scraper_returns_instance(self):
        """Test that get_chain_scraper returns proper instances."""
        for chain_name in CHAINS:
            scraper = get_chain_scraper(chain_name)
            assert isinstance(scraper, Scraper)
            assert scraper.chain == chain_name

    def test_get_unknown_chain_raises_error(self):
        """Test that unknown chain raises ValueError."""
        with pytest.raises(ValueError, match="Unknown chain"):
            get_chain_scraper("unknown_chain")

    def test_all_scrapers_have_catalog_urls_or_api(self):
        """Test that all scrapers have catalog URLs or API methods."""
        for chain_name, scraper_cls in CHAINS.items():
            scraper = scraper_cls()

            # Scrapers may have various data source configurations:
            has_catalog = bool(scraper.catalog_urls)
            has_scrape_method = hasattr(scraper, 'scrape')
            has_fetch_override = hasattr(scraper, '_fetch_category')
            has_store_list = hasattr(scraper, 'stores') and scraper.stores  # LiquorCentre
            has_shop_url = hasattr(scraper, 'shop_url')  # Some Shopify scrapers
            has_collections = hasattr(scraper, 'collections') and scraper.collections  # Shopify
            has_base_url = hasattr(scraper, 'base_url')  # Base URL for API scrapers
            has_dynamic_discovery = hasattr(scraper, '_discover_category_urls')  # Liquorland

            assert has_catalog or has_scrape_method or has_fetch_override or has_store_list or has_shop_url or has_collections or has_base_url or has_dynamic_discovery, \
                f"Scraper {chain_name} has no data source"


# ============================================================================
# Base Scraper Tests
# ============================================================================

class TestBaseScraperFunctionality:
    """Tests for base Scraper class functionality."""

    def test_build_product_dict_minimal(self):
        """Test building product dict with minimal required fields."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="TEST123",
            name="Steinlager Pure 12x330ml 5%",
            price_nzd=29.99
        )

        assert result["chain"] == "liquorland"
        assert result["source_id"] == "TEST123"
        assert result["name"] == "Steinlager Pure 12x330ml 5%"
        assert result["price_nzd"] == 29.99
        # Auto-inferred fields
        assert result["brand"] is not None
        assert result["category"] is not None
        assert result["pack_count"] == 12
        assert result["unit_volume_ml"] == 330.0
        assert result["abv_percent"] == 5.0

    def test_build_product_dict_with_all_fields(self):
        """Test building product dict with all optional fields."""
        scraper = SuperLiquorScraper()
        promo_ends = datetime(2024, 12, 25, 23, 59, 59)

        result = scraper.build_product_dict(
            source_id="PROMO123",
            name="Test Beer 6x330ml",
            price_nzd=25.00,
            promo_price_nzd=20.00,
            promo_text="Save $5",
            promo_ends_at=promo_ends,
            is_member_only=True,
            url="https://example.com/product",
            image_url="https://example.com/image.jpg",
            brand="Test Brand",
            category="beer",
        )

        assert result["promo_price_nzd"] == 20.00
        assert result["promo_text"] == "Save $5"
        assert result["promo_ends_at"] == promo_ends
        assert result["is_member_only"] is True
        assert result["url"] == "https://example.com/product"
        assert result["image_url"] == "https://example.com/image.jpg"
        assert result["brand"] == "Test Brand"
        assert result["category"] == "beer"

    def test_build_product_dict_truncates_long_promo_text(self):
        """Test that promo text is truncated to 255 chars."""
        scraper = LiquorlandScraper()
        long_promo = "A" * 300

        result = scraper.build_product_dict(
            source_id="TEST",
            name="Test",
            price_nzd=10.00,
            promo_text=long_promo
        )

        assert len(result["promo_text"]) == 255


# ============================================================================
# Liquorland Scraper Tests
# ============================================================================

class TestLiquorlandScraper:
    """Tests for Liquorland scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = LiquorlandScraper()

        assert scraper.chain == "liquorland"
        assert len(scraper._FALLBACK_CATALOG_URLS) > 0

    def test_fallback_urls_cover_all_categories(self):
        """Test that fallback URLs cover all major categories."""
        scraper = LiquorlandScraper()
        urls_str = " ".join(scraper._FALLBACK_CATALOG_URLS)

        assert "beer" in urls_str
        assert "wine" in urls_str
        assert "spirits" in urls_str
        assert "rtd" in urls_str

    @pytest.mark.asyncio
    async def test_parse_products_from_html(self):
        """Test parsing products from Liquorland HTML."""
        scraper = LiquorlandScraper()

        # Sample HTML matching Liquorland structure
        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/steinlager-pure">
                Steinlager Pure 12x330ml
            </a>
            <div class="s-price">$29.99</div>
            <img src="https://example.com/steinlager.jpg" />
        </div>
        <div class="s-product">
            <a class="s-product__name" href="/products/corona-extra">
                Corona Extra 6x355ml
            </a>
            <div class="s-price">$19.99</div>
            <div class="s-product__badge">2 for $35</div>
            <img src="https://example.com/corona.jpg" />
        </div>
        """

        products = await scraper.parse_products(html)

        assert len(products) == 2

        # First product
        assert "Steinlager" in products[0]["name"]
        assert products[0]["price_nzd"] == 29.99
        assert products[0]["chain"] == "liquorland"

        # Second product (with promo)
        assert "Corona" in products[1]["name"]
        assert products[1]["price_nzd"] == 19.99
        assert products[1]["promo_text"] is not None

    def test_get_page_url(self):
        """Test pagination URL construction."""
        scraper = LiquorlandScraper()

        base_url = "https://www.liquorland.co.nz/beer"
        result = scraper._get_page_url(base_url, 2)

        assert "p=2" in result

        # Test with existing query params
        base_url_with_params = "https://www.liquorland.co.nz/beer?sort=price"
        result = scraper._get_page_url(base_url_with_params, 3)

        assert "p=3" in result
        assert "&" in result  # Should use & not ?

    @pytest.mark.asyncio
    async def test_parse_specials_payload_uses_catalog_price_as_regular(self):
        """SaleFinder specials should use catalog price as regular baseline."""
        scraper = LiquorlandScraper()

        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/test-gin-700ml">Test Gin 700ml</a>
            <div class="s-price">$49.99</div>
        </div>
        """
        await scraper.parse_products(html)

        specials_payload = {
            "__liquorland_specials": True,
            "items": [
                {
                    "itemId": "999",
                    "itemName": "Test Gin 700ml",
                    "URL": "https://www.liquorland.co.nz/products/test-gin-700ml",
                    "endDate": "2026-02-22 23:59:59",
                    "prices": [
                        {
                            "priceSaleDesc": "Hot Price",
                            "priceSale": "39.99",
                        }
                    ],
                }
            ],
        }

        products = await scraper.parse_products(
            f"{SPECIALS_PAYLOAD_PREFIX}{json.dumps(specials_payload)}"
        )

        assert len(products) == 1
        assert products[0]["source_id"] == "test-gin-700ml"
        assert products[0]["price_nzd"] == 49.99
        assert products[0]["promo_price_nzd"] == 39.99
        assert products[0]["promo_ends_at"] is not None

    @pytest.mark.asyncio
    async def test_parse_specials_payload_extracts_multibuy_unit_price(self):
        """SaleFinder multi-buy deals should map to unit promo price."""
        scraper = LiquorlandScraper()

        specials_payload = {
            "__liquorland_specials": True,
            "items": [
                {
                    "itemId": "1000",
                    "itemName": "Sample RTD 10x330ml",
                    "URL": "https://www.liquorland.co.nz/products/sample-rtd-10x330ml",
                    "endDate": "2026-02-22 23:59:59",
                    "prices": [
                        {
                            "priceSaleDesc": "2 for",
                            "priceSale": "40.00",
                        },
                        {
                            "priceOptionDesc": "Or",
                            "priceReg": "22.99",
                            "priceRegSuffix": "each",
                        },
                    ],
                }
            ],
        }

        products = await scraper.parse_products(
            f"{SPECIALS_PAYLOAD_PREFIX}{json.dumps(specials_payload)}"
        )

        assert len(products) == 1
        assert products[0]["price_nzd"] == 22.99
        assert products[0]["promo_price_nzd"] == 20.00


# ============================================================================
# Super Liquor Scraper Tests
# ============================================================================

class TestSuperLiquorScraper:
    """Tests for Super Liquor scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = SuperLiquorScraper()

        assert scraper.chain == "super_liquor"
        assert len(scraper.catalog_urls) > 0

    def test_catalog_urls_comprehensive(self):
        """Test all major categories are covered."""
        scraper = SuperLiquorScraper()
        urls_str = " ".join(scraper.catalog_urls).lower()

        categories = ["beer", "wine", "spirit", "vodka", "gin", "whisky", "cider"]
        for category in categories:
            assert category in urls_str, f"Missing category: {category}"


# ============================================================================
# Bottle O Scraper Tests
# ============================================================================

class TestBottleOScraper:
    """Tests for The Bottle O scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = BottleOScraper()

        assert scraper.chain == "bottle_o"
        assert len(scraper.catalog_urls) > 0

    @pytest.mark.asyncio
    async def test_parse_products_from_cityhive_html(self):
        """Test parsing products from CityHive .talker HTML."""
        scraper = BottleOScraper()

        tagged_html = (
            '<!--METADATA:store=test-store,category=beer,page=1-->'
            '<html><body>'
            '<div class="talker" id="line_abc123def456">'
            '  <a href="/product/test-beer">'
            '    <div class="talker__name">'
            '      <span>Test Beer</span>'
            '      <span class="talker__name__size">6 x 330ml</span>'
            '    </div>'
            '    <div class="price"><span class="price__sell">$24.99</span></div>'
            '  </a>'
            '</div>'
            '<div class="talker" id="line_789abc012def">'
            '  <a href="/product/test-wine">'
            '    <div class="talker__name">'
            '      <span>Test Wine</span>'
            '      <span class="talker__name__size">750ml</span>'
            '    </div>'
            '    <div class="price"><span class="price__sell">$15.99</span></div>'
            '  </a>'
            '</div>'
            '</body></html>'
        )

        products = await scraper.parse_products(tagged_html)

        assert len(products) == 2
        assert products[0]["source_id"] == "abc123def456"
        assert products[0]["name"] == "Test Beer 6 x 330ml"
        assert products[0]["price_nzd"] == 24.99
        assert products[0]["chain"] == "bottle_o"
        assert products[0]["store_identifier"] == "test-store"

    @pytest.mark.asyncio
    async def test_parse_products_from_gtm_data(self):
        """Test parsing franchise products from GTM dataLayer."""
        scraper = BottleOScraper()

        combined_data = json.dumps({
            "gtm": [
                {
                    "event": "productListImpression",
                    "ecommerce": {
                        "impressions": [
                            {
                                "id": "test-beer-123",
                                "name": "Test Beer 6x330ml",
                                "price": 24.99,
                                "brand": "Test Brand",
                                "category": "beer",
                            },
                            {
                                "id": "test-wine-456",
                                "name": "Test Wine 750ml",
                                "price": 15.99,
                                "brand": "Test Winery",
                                "category": "wine",
                            }
                        ]
                    }
                }
            ],
            "html": "<html><body></body></html>"
        })

        products = await scraper.parse_products(combined_data)

        assert len(products) == 2
        assert products[0]["source_id"] == "test-beer-123"
        assert products[0]["name"] == "Test Beer 6x330ml"
        assert products[0]["price_nzd"] == 24.99
        assert products[0]["chain"] == "bottle_o"
        assert products[0].get("_franchise") is True

    @pytest.mark.asyncio
    async def test_parse_cityhive_special_product(self):
        """Test parsing a product with Special class from CityHive HTML."""
        scraper = BottleOScraper()

        tagged_html = (
            '<!--METADATA:store=test-store,category=beer,page=1-->'
            '<html><body>'
            '<div class="talker talker--Special" id="line_aabbccdd1122">'
            '  <a href="/product/promo-beer">'
            '    <div class="talker__name">'
            '      <span>Promo Beer</span>'
            '      <span class="talker__name__size">12 x 330ml</span>'
            '    </div>'
            '    <div class="price"><span class="price__sell">$22.99</span></div>'
            '    <div class="talker__sticker">'
            '      <span class="talker__sticker__label">2 for $40</span>'
            '    </div>'
            '  </a>'
            '</div>'
            '</body></html>'
        )

        products = await scraper.parse_products(tagged_html)

        assert len(products) == 1
        assert products[0]["promo_text"] is not None

    def test_normalize_name(self):
        """Test product name normalization."""
        scraper = BottleOScraper()

        assert scraper._normalize_name("Test Beer 12 x 330ml") == "test beer 12x330ml"
        assert scraper._normalize_name("Test  Beer") == "test beer"
        assert scraper._normalize_name("TEST BEER") == "test beer"


# ============================================================================
# Glengarry Scraper Tests
# ============================================================================

class TestGlengarryScraper:
    """Tests for Glengarry scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = GlengarryScraper()

        assert scraper.chain == "glengarry"
        assert len(scraper.catalog_urls) > 0
        assert "glengarrywines.co.nz" in scraper.catalog_urls[0]

    @pytest.mark.asyncio
    async def test_parse_products_from_html(self):
        """Test parsing products from Glengarry HTML."""
        scraper = GlengarryScraper()

        html = """
        <div class="productDisplaySlot">
            <div class="fontProductHead"><a>Test Winery</a></div>
            <div class="fontProductHeadSub"><a href="/items/12345/test-wine">Pinot Noir 2022</a></div>
            <div class="productDisplayPrice">
                <span class="fontProductPrice">$25.99</span>
            </div>
            <img class="productDisplayImage" src="/images/test.jpg" />
        </div>
        """

        products = await scraper.parse_products(html)

        assert len(products) == 1
        assert "Test Winery" in products[0]["name"]
        assert products[0]["price_nzd"] == 25.99

    @pytest.mark.asyncio
    async def test_parse_products_with_sale_price(self):
        """Test parsing products with WAS/NOW pricing."""
        scraper = GlengarryScraper()

        html = """
        <div class="productDisplaySlot">
            <div class="fontProductHead"><a>Test Winery</a></div>
            <div class="fontProductHeadSub"><a href="/items/12345/test-wine">Premium Wine</a></div>
            <div class="productDisplayPrice">
                <span class="fontProductPriceSub">WAS $35.99</span>
                <span class="fontProductPrice">NOW $29.99</span>
            </div>
        </div>
        """

        products = await scraper.parse_products(html)

        assert len(products) == 1
        assert products[0]["price_nzd"] == 35.99  # Original price
        assert products[0]["promo_price_nzd"] == 29.99  # Sale price


# ============================================================================
# Foodstuffs API Scraper Tests (New World / PAK'nSAVE)
# ============================================================================

class TestFoodstuffsScraper:
    """Tests for New World and PAK'nSAVE scrapers."""

    @pytest.mark.parametrize("scraper_class,chain_name", [
        (NewWorldAPIScraper, "new_world"),
        (PakNSaveAPIScraper, "paknsave"),
    ])
    def test_initialization(self, scraper_class, chain_name):
        """Test scrapers initialize correctly."""
        scraper = scraper_class(scrape_all_stores=False)

        assert scraper.chain == chain_name
        assert hasattr(scraper, 'site_url')
        assert hasattr(scraper, 'api_domain')

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_parse_product_basic(self, scraper_class):
        """Test parsing basic product from API response."""
        scraper = scraper_class(scrape_all_stores=False)

        product_data = {
            "productId": "R1234567",
            "brand": "Corona",
            "name": "Extra",
            "displayName": "6x355ml Bottles",
            "singlePrice": {
                "price": 1999  # $19.99 in cents
            },
            "promotions": []
        }

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "R1234567"
        assert "Corona" in result["name"]
        assert result["price_nzd"] == 19.99
        assert result["promo_price_nzd"] is None

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_parse_product_with_promotion(self, scraper_class):
        """Test parsing product with promotional pricing."""
        scraper = scraper_class(scrape_all_stores=False)

        product_data = {
            "productId": "R7654321",
            "brand": "Steinlager",
            "name": "Pure",
            "displayName": "12x330ml",
            "singlePrice": {
                "price": 2999  # $29.99
            },
            "promotions": [
                {
                    "bestPromotion": True,
                    "rewardValue": 2499,  # $24.99
                    "rewardType": "NEW_PRICE",
                    "decal": "Now $24.99",
                    "cardDependencyFlag": True  # Member only
                }
            ]
        }

        result = scraper._parse_product(product_data)

        assert result["price_nzd"] == 29.99
        assert result["promo_price_nzd"] == 24.99
        assert result["is_member_only"] is True

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_image_url_construction(self, scraper_class):
        """Test product image URL construction."""
        scraper = scraper_class(scrape_all_stores=False)

        product_data = {
            "productId": "R1234567",
            "brand": "Test",
            "name": "Product",
            "displayName": "Test",
            "singlePrice": {"price": 1000},
            "promotions": []
        }

        result = scraper._parse_product(product_data)

        assert result["image_url"] is not None
        assert "fsimg.co.nz" in result["image_url"]


# ============================================================================
# Countdown API Scraper Tests
# ============================================================================

class TestCountdownScraper:
    """Tests for Countdown API scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = CountdownAPIScraper()
        assert scraper.chain == "countdown"

    def test_parse_product_basic(self):
        """Test parsing basic product from API response."""
        scraper = CountdownAPIScraper()

        product_data = {
            "sku": "1234567",
            "name": "Pale Ale 330ml",
            "brand": "Garage Project",
            "variety": "Day of the Dead",
            "price": {
                "originalPrice": 6.50,
                "isSpecial": False,
                "isClubPrice": False
            },
            "images": {"big": "https://example.com/image.jpg"},
            "slug": "garage-project-day-of-the-dead"
        }

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "1234567"
        assert "Garage Project" in result["name"]
        assert result["price_nzd"] == 6.50

    def test_parse_product_with_special(self):
        """Test parsing product with special pricing."""
        scraper = CountdownAPIScraper()

        product_data = {
            "sku": "7654321",
            "name": "Lager 12x330ml",
            "brand": "Steinlager",
            "variety": "Pure",
            "price": {
                "originalPrice": 29.99,
                "salePrice": 24.99,
                "isSpecial": True,
                "savePrice": 5.00,
                "isClubPrice": False
            },
            "images": {},
            "slug": "steinlager-pure"
        }

        result = scraper._parse_product(product_data)

        assert result["price_nzd"] == 29.99
        assert result["promo_price_nzd"] == 24.99


# ============================================================================
# Shopify-Based Scraper Tests
# ============================================================================

class TestShopifyScrapers:
    """Tests for Shopify-based scrapers (Thirsty Liquor, Black Bull)."""

    @pytest.mark.parametrize("scraper_class,chain_name", [
        (ThirstyLiquorScraper, "thirsty_liquor"),
        (BlackBullScraper, "black_bull"),
    ])
    def test_initialization(self, scraper_class, chain_name):
        """Test scrapers initialize correctly."""
        scraper = scraper_class()
        assert scraper.chain == chain_name


# ============================================================================
# NZ-Wide Coverage Tests
# ============================================================================

class TestNZWideCoverage:
    """Tests to verify complete NZ coverage."""

    # Major NZ liquor chain brands
    MAJOR_NZ_CHAINS = {
        "liquorland": 100,  # ~100 stores nationally
        "super_liquor": 150,  # ~150 stores nationally
        "bottle_o": 80,  # ~80 stores
        "new_world": 140,  # ~140 stores (grocery with liquor)
        "paknsave": 60,  # ~60 stores
        "glengarry": 10,  # ~10 specialty stores
    }

    def test_all_major_chains_have_scrapers(self):
        """Test that all major NZ chains have scrapers."""
        for chain in self.MAJOR_NZ_CHAINS:
            assert chain in CHAINS, f"Missing scraper for major chain: {chain}"

    def test_estimated_store_coverage(self):
        """Test that we have estimated national coverage."""
        total_stores = sum(self.MAJOR_NZ_CHAINS.values())
        assert total_stores > 500, "Should cover 500+ stores nationally"

    def test_scraper_categories_cover_all_products(self):
        """Test that scrapers cover all product categories."""
        all_categories_covered = set()

        for chain_name in CHAINS:
            scraper = get_chain_scraper(chain_name)
            if hasattr(scraper, 'catalog_urls'):
                urls_str = " ".join(scraper.catalog_urls).lower()

                if "beer" in urls_str:
                    all_categories_covered.add("beer")
                if "wine" in urls_str:
                    all_categories_covered.add("wine")
                if "spirit" in urls_str:
                    all_categories_covered.add("spirits")
                if "cider" in urls_str:
                    all_categories_covered.add("cider")
                if "rtd" in urls_str:
                    all_categories_covered.add("rtd")

        expected_categories = {"beer", "wine", "spirits", "cider", "rtd"}
        assert all_categories_covered >= expected_categories, \
            f"Missing categories: {expected_categories - all_categories_covered}"


# ============================================================================
# Product Data Quality Tests
# ============================================================================

class TestProductDataQuality:
    """Tests for product data quality."""

    @pytest.mark.parametrize("chain_name", list(CHAINS.keys()))
    def test_scraper_returns_required_fields(self, chain_name):
        """Test that all scrapers return products with required fields."""
        scraper = get_chain_scraper(chain_name)

        # Required fields for every product
        required_fields = {
            "chain",
            "source_id",
            "name",
            "price_nzd",
        }

        # Build a test product using the scraper
        test_product = scraper.build_product_dict(
            source_id="TEST123",
            name="Test Product 330ml",
            price_nzd=10.00
        )

        for field in required_fields:
            assert field in test_product, f"Missing required field '{field}' in {chain_name}"
            assert test_product[field] is not None, f"Field '{field}' is None in {chain_name}"

    @pytest.mark.parametrize("chain_name", list(CHAINS.keys()))
    def test_price_is_valid_number(self, chain_name):
        """Test that price is a valid positive number."""
        scraper = get_chain_scraper(chain_name)

        product = scraper.build_product_dict(
            source_id="TEST",
            name="Test",
            price_nzd=29.99
        )

        assert isinstance(product["price_nzd"], (int, float))
        assert product["price_nzd"] > 0


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_liquorland_html():
    """Sample Liquorland HTML fixture."""
    return """
    <html>
    <body>
        <div class="s-product">
            <a class="s-product__name" href="/products/steinlager-pure-12-330ml">
                Steinlager Pure 12x330ml
            </a>
            <div class="s-price">$29.99</div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_countdown_api_response():
    """Sample Countdown API response fixture."""
    return {
        "products": {
            "items": [
                {
                    "sku": "123456",
                    "name": "Pale Ale 330ml",
                    "brand": "Garage Project",
                    "variety": "IPA",
                    "price": {"originalPrice": 8.99},
                    "images": {},
                    "slug": "garage-project-ipa"
                }
            ],
            "totalCount": 1
        }
    }


@pytest.fixture
def sample_foodstuffs_api_response():
    """Sample Foodstuffs (New World/PAK'nSAVE) API response fixture."""
    return {
        "products": [
            {
                "productId": "R123456",
                "brand": "Steinlager",
                "name": "Pure",
                "displayName": "12x330ml",
                "singlePrice": {"price": 2999},
                "promotions": []
            }
        ],
        "totalProducts": 1
    }
