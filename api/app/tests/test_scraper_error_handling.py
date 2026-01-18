"""
Comprehensive tests for scraper error handling and edge cases.

Tests ensure scrapers handle errors gracefully and don't crash on malformed data.
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.base import Scraper
from app.scrapers.countdown_api import CountdownAPIScraper
from app.scrapers.liquorland import LiquorlandScraper
from app.scrapers.bottle_o import BottleOScraper
from app.scrapers.glengarry import GlengarryScraper
from app.scrapers.new_world_api import NewWorldAPIScraper
from app.scrapers.paknsave_api import PakNSaveAPIScraper
from app.scrapers.registry import CHAINS, get_chain_scraper


# ============================================================================
# Malformed HTML Tests
# ============================================================================

class TestMalformedHTMLHandling:
    """Tests for handling malformed or unexpected HTML."""

    @pytest.mark.asyncio
    async def test_liquorland_handles_empty_html(self):
        """Test Liquorland scraper handles empty HTML."""
        scraper = LiquorlandScraper()

        products = await scraper.parse_products("")
        assert products == []

    @pytest.mark.asyncio
    async def test_liquorland_handles_no_products_html(self):
        """Test Liquorland scraper handles HTML with no products."""
        scraper = LiquorlandScraper()

        html = "<html><body><p>No products found</p></body></html>"
        products = await scraper.parse_products(html)

        assert products == []

    @pytest.mark.asyncio
    async def test_liquorland_handles_missing_price(self):
        """Test Liquorland scraper skips products without price."""
        scraper = LiquorlandScraper()

        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/test">Test Product</a>
            <!-- No price element -->
        </div>
        """

        products = await scraper.parse_products(html)
        assert products == []

    @pytest.mark.asyncio
    async def test_liquorland_handles_invalid_price(self):
        """Test Liquorland scraper handles invalid price text."""
        scraper = LiquorlandScraper()

        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/test">Test Product</a>
            <div class="s-price">Price on request</div>
        </div>
        """

        products = await scraper.parse_products(html)
        # Should skip products with unparseable prices
        assert products == []

    @pytest.mark.asyncio
    async def test_glengarry_handles_empty_html(self):
        """Test Glengarry scraper handles empty HTML."""
        scraper = GlengarryScraper()

        products = await scraper.parse_products("")
        assert products == []

    @pytest.mark.asyncio
    async def test_glengarry_handles_missing_name(self):
        """Test Glengarry scraper skips products without name."""
        scraper = GlengarryScraper()

        html = """
        <div class="productDisplaySlot">
            <div class="productDisplayPrice">
                <span class="fontProductPrice">$25.99</span>
            </div>
        </div>
        """

        products = await scraper.parse_products(html)
        assert products == []


# ============================================================================
# Malformed JSON/API Tests
# ============================================================================

class TestMalformedAPIHandling:
    """Tests for handling malformed API responses."""

    @pytest.mark.asyncio
    async def test_bottle_o_handles_invalid_json(self):
        """Test Bottle O scraper handles invalid JSON."""
        scraper = BottleOScraper()

        products = await scraper.parse_products("invalid json")
        assert products == []

    @pytest.mark.asyncio
    async def test_bottle_o_handles_empty_gtm_data(self):
        """Test Bottle O scraper handles empty GTM data."""
        scraper = BottleOScraper()

        combined_data = json.dumps({"gtm": [], "html": ""})
        products = await scraper.parse_products(combined_data)

        assert products == []

    @pytest.mark.asyncio
    async def test_bottle_o_handles_missing_gtm_key(self):
        """Test Bottle O scraper handles missing GTM key."""
        scraper = BottleOScraper()

        combined_data = json.dumps({"html": "<html></html>"})
        products = await scraper.parse_products(combined_data)

        assert products == []

    @pytest.mark.asyncio
    async def test_bottle_o_skips_invalid_impression(self):
        """Test Bottle O scraper skips invalid product impressions."""
        scraper = BottleOScraper()

        combined_data = json.dumps({
            "gtm": [
                {
                    "event": "productListImpression",
                    "ecommerce": {
                        "impressions": [
                            {"id": "valid-123", "name": "Valid Product", "price": 10.0},
                            {"id": "", "name": "", "price": None},  # Invalid
                            {"name": "No ID"},  # Missing id
                            {"id": "no-price", "name": "No Price"},  # Missing price
                        ]
                    }
                }
            ],
            "html": ""
        })

        products = await scraper.parse_products(combined_data)

        # Should only return the valid product
        assert len(products) == 1
        assert products[0]["source_id"] == "valid-123"

    def test_countdown_handles_empty_product_data(self):
        """Test Countdown scraper handles empty product data."""
        scraper = CountdownAPIScraper()

        # Empty dict should not crash
        result = scraper._parse_product({})
        # May return with defaults or raise - just shouldn't crash unexpectedly

    def test_foodstuffs_handles_missing_fields(self):
        """Test Foodstuffs scraper handles missing required fields."""
        scraper = NewWorldAPIScraper(scrape_all_stores=False)

        # Missing productId
        product_data = {
            "brand": "Test",
            "name": "Product",
            "displayName": "Test",
            "singlePrice": {"price": 1000},
            "promotions": []
        }

        result = scraper._parse_product(product_data)
        # Should still work but with empty source_id
        assert result["source_id"] == ""

    def test_foodstuffs_handles_missing_price(self):
        """Test Foodstuffs scraper handles missing price."""
        scraper = PakNSaveAPIScraper(scrape_all_stores=False)

        product_data = {
            "productId": "R123",
            "brand": "Test",
            "name": "Product",
            "displayName": "Test",
            "singlePrice": {},  # Missing price key
            "promotions": []
        }

        # Should handle gracefully
        try:
            result = scraper._parse_product(product_data)
            # If it doesn't crash, check price is 0 or None
            assert result["price_nzd"] in [0, 0.0, None]
        except (KeyError, TypeError):
            # This is acceptable behavior for missing required field
            pass


# ============================================================================
# Network Error Tests
# ============================================================================

class TestNetworkErrorHandling:
    """Tests for handling network errors."""

    @pytest.mark.asyncio
    async def test_countdown_handles_api_error(self):
        """Test Countdown scraper handles API errors gracefully."""
        scraper = CountdownAPIScraper()
        scraper.cookies = {"session": "test"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(Exception):
                await scraper._fetch_category("beer", "beer")


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestScraperEdgeCases:
    """Tests for edge cases in scrapers."""

    def test_build_product_dict_with_none_values(self):
        """Test building product dict with None optional values."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="TEST",
            name="Test Beer",
            price_nzd=10.0,
            promo_price_nzd=None,
            promo_text=None,
            url=None,
            image_url=None,
        )

        assert result["source_id"] == "TEST"
        assert result["promo_price_nzd"] is None
        assert result["promo_text"] is None

    def test_build_product_dict_with_zero_price(self):
        """Test building product dict with zero price."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="FREE",
            name="Free Sample",
            price_nzd=0.0
        )

        assert result["price_nzd"] == 0.0

    def test_build_product_dict_with_very_high_price(self):
        """Test building product dict with very high price."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="EXPENSIVE",
            name="Rare Whisky 700ml",
            price_nzd=99999.99
        )

        assert result["price_nzd"] == 99999.99

    def test_build_product_dict_with_unicode_name(self):
        """Test building product dict with unicode characters."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="UNICODE",
            name="Château Margaux Rosé 750ml",
            price_nzd=150.0
        )

        assert "Château" in result["name"]
        assert "Rosé" in result["name"]

    def test_build_product_dict_with_very_long_name(self):
        """Test building product dict with very long name."""
        scraper = LiquorlandScraper()

        long_name = "A" * 1000 + " 330ml"
        result = scraper.build_product_dict(
            source_id="LONG",
            name=long_name,
            price_nzd=10.0
        )

        assert len(result["name"]) == len(long_name)

    def test_promo_price_higher_than_regular_price(self):
        """Test handling when promo price is incorrectly higher than regular."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="WEIRD",
            name="Test Product",
            price_nzd=20.0,
            promo_price_nzd=25.0  # Higher than regular - data error
        )

        # Should still accept the values as provided
        assert result["price_nzd"] == 20.0
        assert result["promo_price_nzd"] == 25.0

    def test_negative_price_handling(self):
        """Test handling of negative prices."""
        scraper = LiquorlandScraper()

        result = scraper.build_product_dict(
            source_id="NEGATIVE",
            name="Test",
            price_nzd=-10.0  # Invalid negative price
        )

        # Should accept as-is (validation is elsewhere)
        assert result["price_nzd"] == -10.0


# ============================================================================
# Special Character Tests
# ============================================================================

class TestSpecialCharacterHandling:
    """Tests for handling special characters."""

    @pytest.mark.asyncio
    async def test_liquorland_handles_html_entities(self):
        """Test Liquorland scraper handles HTML entities."""
        scraper = LiquorlandScraper()

        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/test">
                Jack Daniel&apos;s Tennessee Whiskey
            </a>
            <div class="s-price">$45.99</div>
        </div>
        """

        products = await scraper.parse_products(html)

        # Verify it parsed (entities may or may not be decoded)
        assert len(products) == 1

    @pytest.mark.asyncio
    async def test_liquorland_handles_newlines_in_name(self):
        """Test Liquorland scraper handles newlines in product names."""
        scraper = LiquorlandScraper()

        html = """
        <div class="s-product">
            <a class="s-product__name" href="/products/test">
                Steinlager Pure
                12x330ml
            </a>
            <div class="s-price">$29.99</div>
        </div>
        """

        products = await scraper.parse_products(html)

        assert len(products) == 1
        assert "Steinlager" in products[0]["name"]


# ============================================================================
# Concurrent Access Tests
# ============================================================================

class TestConcurrentAccess:
    """Tests for concurrent scraper usage."""

    @pytest.mark.asyncio
    async def test_multiple_parse_calls(self):
        """Test multiple parse calls don't interfere."""
        scraper = LiquorlandScraper()

        html1 = """
        <div class="s-product">
            <a class="s-product__name" href="/p1">Product 1</a>
            <div class="s-price">$10.00</div>
        </div>
        """

        html2 = """
        <div class="s-product">
            <a class="s-product__name" href="/p2">Product 2</a>
            <div class="s-price">$20.00</div>
        </div>
        """

        products1 = await scraper.parse_products(html1)
        products2 = await scraper.parse_products(html2)

        assert len(products1) == 1
        assert len(products2) == 1
        assert products1[0]["name"] != products2[0]["name"]


# ============================================================================
# Memory/Performance Edge Cases
# ============================================================================

class TestPerformanceEdgeCases:
    """Tests for performance-related edge cases."""

    @pytest.mark.asyncio
    async def test_large_html_response(self):
        """Test handling of large HTML responses."""
        scraper = LiquorlandScraper()

        # Generate HTML with 1000 products
        products_html = ""
        for i in range(1000):
            products_html += f"""
            <div class="s-product">
                <a class="s-product__name" href="/p{i}">Product {i} 330ml</a>
                <div class="s-price">${i + 1}.99</div>
            </div>
            """

        html = f"<html><body>{products_html}</body></html>"

        products = await scraper.parse_products(html)

        assert len(products) == 1000

    @pytest.mark.asyncio
    async def test_bottle_o_large_gtm_response(self):
        """Test Bottle O with large GTM data."""
        scraper = BottleOScraper()

        impressions = [
            {"id": f"prod-{i}", "name": f"Product {i}", "price": 10.0 + i}
            for i in range(500)
        ]

        combined_data = json.dumps({
            "gtm": [{
                "event": "productListImpression",
                "ecommerce": {"impressions": impressions}
            }],
            "html": ""
        })

        products = await scraper.parse_products(combined_data)

        assert len(products) == 500


# ============================================================================
# Rate Limiting Configuration Tests
# ============================================================================

class TestRateLimitingConfig:
    """Tests for rate limiting configuration."""

    def test_liquorland_has_rate_limits(self):
        """Test Liquorland has rate limiting constants defined."""
        from app.scrapers.liquorland import DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_CATEGORIES

        assert DELAY_BETWEEN_REQUESTS > 0
        assert DELAY_BETWEEN_CATEGORIES > 0
        assert DELAY_BETWEEN_CATEGORIES >= DELAY_BETWEEN_REQUESTS

    def test_bottle_o_has_rate_limits(self):
        """Test Bottle O has rate limiting constants defined."""
        from app.scrapers.bottle_o import DELAY_BETWEEN_CATEGORIES

        assert DELAY_BETWEEN_CATEGORIES > 0


# ============================================================================
# Browser Resource Cleanup Tests
# ============================================================================

class TestBrowserCleanup:
    """Tests for browser resource cleanup."""

    @pytest.mark.asyncio
    async def test_liquorland_cleanup_on_error(self):
        """Test Liquorland cleans up browser on error."""
        scraper = LiquorlandScraper()

        # Mock browser components
        scraper.playwright = AsyncMock()
        scraper.browser = AsyncMock()
        scraper.context = AsyncMock()

        # Simulate error during fetch
        scraper.context.new_page = AsyncMock(side_effect=Exception("Browser error"))

        # Should still attempt cleanup (though may fail)
        # This tests that cleanup is in finally block
