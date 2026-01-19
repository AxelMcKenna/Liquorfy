"""
Comprehensive test suite for all Liquorfy scrapers.

Tests cover:
- Product parsing accuracy
- Price extraction
- Volume/ABV parsing
- Error handling
- Store-specific pricing
- Rate limiting
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from app.scrapers.countdown_api import CountdownAPIScraper
from app.scrapers.new_world_api import NewWorldAPIScraper
from app.scrapers.paknsave_api import PakNSaveAPIScraper
from app.scrapers.super_liquor import SuperLiquorScraper
from app.scrapers.black_bull import BlackBullScraper
from app.scrapers.thirsty_liquor import ThirstyLiquorScraper


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def countdown_api_response():
    """Sample Countdown API response."""
    return {
        "products": {
            "items": [
                {
                    "sku": "1234567",
                    "name": "Pale Ale 330ml",
                    "brand": "Garage Project",
                    "variety": "Day of the Dead",
                    "price": {
                        "originalPrice": 6.50,
                        "salePrice": 5.00,
                        "isSpecial": True,
                        "savePrice": 1.50,
                        "isClubPrice": False
                    },
                    "size": {
                        "volumeSize": "1 x 330ml"
                    },
                    "images": {
                        "big": "https://example.com/image.jpg"
                    },
                    "slug": "garage-project-day-of-the-dead-pale-ale"
                },
                {
                    "sku": "7654321",
                    "name": "Lager 6x330ml",
                    "brand": "Steinlager",
                    "variety": "Pure",
                    "price": {
                        "originalPrice": 18.99,
                        "isSpecial": False,
                        "isClubPrice": False
                    },
                    "images": {
                        "big": "https://example.com/lager.jpg"
                    },
                    "slug": "steinlager-pure-lager"
                }
            ],
            "totalCount": 2
        }
    }


@pytest.fixture
def foodstuffs_api_response():
    """Sample New World/PAK'nSAVE API response."""
    return {
        "products": [
            {
                "productId": "R1234567",
                "brand": "Speight's",
                "name": "Summit",
                "displayName": "Lager 12x330ml Bottles",
                "singlePrice": {
                    "price": 2499  # $24.99 in cents
                },
                "promotions": [
                    {
                        "bestPromotion": True,
                        "rewardValue": 1999,  # $19.99
                        "rewardType": "NEW_PRICE",
                        "decal": "Now $19.99",
                        "cardDependencyFlag": True
                    }
                ]
            },
            {
                "productId": "R7654321",
                "brand": "Corona",
                "name": "Extra",
                "displayName": "Bottle 330ml",
                "singlePrice": {
                    "price": 599  # $5.99
                },
                "promotions": []
            }
        ],
        "totalProducts": 2
    }


# ============================================================================
# Countdown Tests
# ============================================================================

class TestCountdownScraper:
    """Test Countdown API scraper."""

    def test_parse_product_with_promo(self, countdown_api_response):
        """Test parsing product with promotional pricing."""
        scraper = CountdownAPIScraper()
        product_data = countdown_api_response["products"]["items"][0]

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "1234567"
        assert "Garage Project" in result["name"]
        assert "Day of the Dead" in result["name"]
        assert result["price_nzd"] == 6.50
        assert result["promo_price_nzd"] == 5.00
        assert result["promo_text"] == "Save $1.50"
        assert result["is_member_only"] is False
        assert result["image_url"] is not None
        assert result["url"] is not None

    def test_parse_product_no_promo(self, countdown_api_response):
        """Test parsing product without promotion."""
        scraper = CountdownAPIScraper()
        product_data = countdown_api_response["products"]["items"][1]

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "7654321"
        assert result["price_nzd"] == 18.99
        assert result["promo_price_nzd"] is None
        assert result["promo_text"] is None

    def test_volume_parsing(self, countdown_api_response):
        """Test volume information is parsed correctly."""
        scraper = CountdownAPIScraper()
        product_data = countdown_api_response["products"]["items"][0]

        result = scraper._parse_product(product_data)

        # Volume should be parsed from product name
        assert result["unit_volume_ml"] is not None or result["total_volume_ml"] is not None

    @pytest.mark.asyncio
    async def test_fetch_category(self):
        """Test category fetching with mocked HTTP client."""
        scraper = CountdownAPIScraper()
        scraper.cookies = {"session": "test"}

        mock_response_data = {"products": {"items": []}}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            # Use MagicMock for the response since .json() is synchronous
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_get = AsyncMock(return_value=mock_response)
            mock_instance.get = mock_get
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await scraper._fetch_category("beer-cider-wine", "beer")

            assert "products" in result
            assert result == mock_response_data


# ============================================================================
# Foodstuffs (New World / PAK'nSAVE) Tests
# ============================================================================

class TestFoodstuffsScraper:
    """Test New World and PAK'nSAVE scrapers (shared API)."""

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_parse_product_with_member_promo(self, scraper_class, foodstuffs_api_response):
        """Test parsing product with member-only promotion."""
        scraper = scraper_class(scrape_all_stores=False)
        product_data = foodstuffs_api_response["products"][0]

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "R1234567"
        assert "Speight's" in result["name"]
        assert result["price_nzd"] == 24.99
        assert result["promo_price_nzd"] == 19.99
        assert result["promo_text"] == "Now $19.99"
        assert result["is_member_only"] is True  # Member-only deal

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_parse_product_no_promo(self, scraper_class, foodstuffs_api_response):
        """Test parsing product without promotion."""
        scraper = scraper_class(scrape_all_stores=False)
        product_data = foodstuffs_api_response["products"][1]

        result = scraper._parse_product(product_data)

        assert result["source_id"] == "R7654321"
        assert result["price_nzd"] == 5.99
        assert result["promo_price_nzd"] is None
        assert result["is_member_only"] is False

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_image_url_construction(self, scraper_class, foodstuffs_api_response):
        """Test product image URL is properly constructed."""
        scraper = scraper_class(scrape_all_stores=False)
        product_data = foodstuffs_api_response["products"][0]

        result = scraper._parse_product(product_data)

        assert result["image_url"] is not None
        assert "fsimg.co.nz" in result["image_url"]
        assert "400x400" in result["image_url"]

    @pytest.mark.parametrize("scraper_class", [NewWorldAPIScraper, PakNSaveAPIScraper])
    def test_product_url_construction(self, scraper_class, foodstuffs_api_response):
        """Test product URL is properly constructed."""
        scraper = scraper_class(scrape_all_stores=False)
        product_data = foodstuffs_api_response["products"][0]

        result = scraper._parse_product(product_data)

        assert result["url"] is not None
        assert "/shop/product/" in result["url"]
        assert "r1234567" in result["url"].lower()


# ============================================================================
# Super Liquor Tests
# ============================================================================

class TestSuperLiquorScraper:
    """Test Super Liquor scraper."""

    def test_initialization(self):
        """Test scraper initializes with correct settings."""
        scraper = SuperLiquorScraper()

        assert scraper.chain == "super_liquor"
        assert len(scraper.catalog_urls) > 0
        assert scraper.use_fixtures is True  # Default to fixtures for testing

    def test_catalog_urls_comprehensive(self):
        """Test that all major categories are covered."""
        scraper = SuperLiquorScraper()

        categories = ["beer", "wine", "spirits", "vodka", "gin", "whisky", "cider"]
        for category in categories:
            assert any(category in url for url in scraper.catalog_urls), \
                f"Missing category: {category}"

    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test exponential backoff retry mechanism."""
        scraper = SuperLiquorScraper(use_fixtures=False)

        with patch.object(scraper.client, 'get') as mock_get:
            # Fail twice, then succeed
            mock_get.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                MagicMock(text="<html></html>", raise_for_status=MagicMock())
            ]

            result = await scraper._fetch_with_retry("https://example.com")

            assert result == "<html></html>"
            assert mock_get.call_count == 3


# ============================================================================
# Browser-based Scraper Tests
# ============================================================================

class TestBrowserScrapers:
    """Test scrapers that use browser automation."""

    @pytest.mark.parametrize("scraper_class,chain_name", [
        (BlackBullScraper, "black_bull"),
        (ThirstyLiquorScraper, "thirsty_liquor"),
    ])
    def test_initialization(self, scraper_class, chain_name):
        """Test browser-based scrapers initialize correctly."""
        scraper = scraper_class()

        assert scraper.chain == chain_name
        assert hasattr(scraper, 'client')


# ============================================================================
# Base Scraper Tests
# ============================================================================

class TestBaseScraper:
    """Test base scraper functionality shared across all scrapers."""

    def test_build_product_dict_minimal(self):
        """Test building product dict with minimal data."""
        scraper = CountdownAPIScraper()

        result = scraper.build_product_dict(
            source_id="TEST123",
            name="Test Beer 330ml 4.5%",
            price_nzd=10.00
        )

        assert result["source_id"] == "TEST123"
        assert result["name"] == "Test Beer 330ml 4.5%"
        assert result["price_nzd"] == 10.00
        assert result["chain"] == "countdown"

        # Should auto-infer these
        assert result["brand"] is not None
        assert result["category"] is not None
        assert result["abv_percent"] == 4.5
        assert result["unit_volume_ml"] == 330.0

    def test_build_product_dict_with_promo(self):
        """Test building product dict with promotional pricing."""
        scraper = CountdownAPIScraper()

        result = scraper.build_product_dict(
            source_id="PROMO123",
            name="Promo Beer 6x330ml",
            price_nzd=25.00,
            promo_price_nzd=20.00,
            promo_text="Save $5",
            is_member_only=True
        )

        assert result["promo_price_nzd"] == 20.00
        assert result["promo_text"] == "Save $5"
        assert result["is_member_only"] is True

    def test_volume_parsing_various_formats(self):
        """Test volume parsing handles various formats."""
        scraper = CountdownAPIScraper()

        test_cases = [
            ("Pack 6x330ml", 330.0, 6),
            ("Box 12x440ml", 440.0, 12),
            ("Case 24x375ml Cans", 375.0, 24),
        ]

        for name, expected_unit_ml, expected_pack in test_cases:
            result = scraper.build_product_dict(
                source_id=f"TEST_{name}",
                name=name,
                price_nzd=10.00
            )

            assert result["unit_volume_ml"] == expected_unit_ml, \
                f"Failed for: {name}, got {result['unit_volume_ml']}"
            assert result["pack_count"] == expected_pack, \
                f"Failed for: {name}, got {result['pack_count']}"

        # Test single items
        single_item_cases = [
            ("Beer 330ml", 330.0),
            ("Wine 750ml", 750.0),
            ("Bottle 1L", 1000.0),
        ]

        for name, expected_unit_ml in single_item_cases:
            result = scraper.build_product_dict(
                source_id=f"TEST_{name}",
                name=name,
                price_nzd=10.00
            )

            assert result["unit_volume_ml"] == expected_unit_ml, \
                f"Failed for: {name}, got {result['unit_volume_ml']}"
            # Single items may have pack_count=None or 1, both are valid
            assert result["pack_count"] in [None, 1], \
                f"Failed for: {name}, got {result['pack_count']}"

    def test_abv_extraction(self):
        """Test ABV extraction from product names."""
        scraper = CountdownAPIScraper()

        test_cases = [
            ("Beer 4.5%", 4.5),
            ("Wine 12.5% ABV", 12.5),
            ("Vodka 40%", 40.0),
            ("Cider 5.0%", 5.0),
        ]

        for name, expected_abv in test_cases:
            result = scraper.build_product_dict(
                source_id=f"TEST_{name}",
                name=name,
                price_nzd=10.00
            )

            assert result["abv_percent"] == expected_abv, \
                f"Failed for: {name}, got {result['abv_percent']}"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in scrapers."""

    @pytest.mark.asyncio
    async def test_countdown_handles_invalid_response(self):
        """Test Countdown scraper handles invalid API responses."""
        scraper = CountdownAPIScraper()

        # Test with empty response
        products = scraper._parse_product({})
        # Should not crash, but may have defaults

    @pytest.mark.asyncio
    async def test_super_liquor_handles_network_failure(self):
        """Test Super Liquor handles network failures gracefully."""
        scraper = SuperLiquorScraper(use_fixtures=False)

        with patch.object(scraper.client, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                await scraper._fetch_with_retry("https://example.com", retry_count=3)


# ============================================================================
# Integration Tests
# ============================================================================

class TestScraperIntegration:
    """Integration tests for complete scraper pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_countdown_scrape_single_category(self):
        """Test scraping a single category returns valid products."""
        scraper = CountdownAPIScraper()

        # Mock cookies and HTTP client to avoid browser launch
        with patch.object(scraper, '_get_cookies', new_callable=AsyncMock) as mock_cookies:
            mock_cookies.return_value = {"session": "test"}
            with patch.object(scraper, '_fetch_category') as mock_fetch:
                mock_fetch.return_value = {
                    "products": {
                        "items": [
                            {
                                "sku": "TEST123",
                                "name": "Test Beer",
                                "brand": "Test Brand",
                                "variety": "Lager",
                                "price": {"originalPrice": 10.00},
                                "images": {},
                                "slug": "test-beer"
                            }
                        ]
                    }
                }

                products = await scraper.scrape()

                assert len(products) > 0
                assert all("source_id" in p for p in products)
                assert all("price_nzd" in p for p in products)


# ============================================================================
# Performance Tests
# ============================================================================

class TestScraperPerformance:
    """Test scraper performance and rate limiting."""

    @pytest.mark.asyncio
    async def test_super_liquor_respects_rate_limits(self):
        """Test that Super Liquor scraper respects rate limiting."""
        scraper = SuperLiquorScraper(use_fixtures=False)

        # Check rate limit constants are set
        from app.scrapers.super_liquor import DELAY_BETWEEN_REQUESTS

        assert DELAY_BETWEEN_REQUESTS > 0, "Rate limiting should be configured"


# ============================================================================
# Fixtures and Helpers
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session
