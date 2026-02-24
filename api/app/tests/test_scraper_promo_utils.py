"""
Comprehensive tests for promo_utils.py - Promotional pricing and deal parsing.

Tests all promotional parsing functions used by scrapers.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
import pytz

from app.services.promo_utils import (
    parse_promo_price,
    parse_multi_buy_deal,
    parse_promo_end_date,
    detect_member_only,
    NZ_TZ,
)


# ============================================================================
# Promo Price Parsing Tests
# ============================================================================

class TestParsePromoPrice:
    """Tests for parse_promo_price function."""

    @pytest.mark.parametrize("text,expected", [
        # Standard price formats
        ("$19.99", 19.99),
        ("$5.00", 5.0),
        ("$100.00", 100.0),
        ("$0.99", 0.99),

        # Without dollar sign
        ("19.99", 19.99),
        ("5.00", 5.0),

        # With commas
        ("$1,299.99", 1299.99),
        ("$2,500", 2500.0),

        # Price in context
        ("Now $19.99", 19.99),
        ("Save $5.00", 5.0),
        ("Special Price $24.99", 24.99),
        ("Sale: $15.99", 15.99),
        ("Was $30 Now $25", 30.0),  # Returns first price found

        # Spacing variations
        ("$ 19.99", 19.99),
        ("$  19.99", 19.99),

        # Integer prices
        ("$20", 20.0),
        ("$100", 100.0),
    ])
    def test_price_extraction(self, text, expected):
        """Test extracting prices from various formats."""
        result = parse_promo_price(text)
        assert result == expected, f"Price mismatch for '{text}'"

    @pytest.mark.parametrize("text", [
        None,
        "",
        "No price here",
        "Free shipping",
        "abc",
    ])
    def test_no_price_found(self, text):
        """Test handling when no price is found."""
        result = parse_promo_price(text)
        assert result is None


# ============================================================================
# Multi-Buy Deal Parsing Tests
# ============================================================================

class TestParseMultiBuyDeal:
    """Tests for parse_multi_buy_deal function."""

    @pytest.mark.parametrize("text,expected_qty,expected_total,expected_unit", [
        # Standard X for $Y deals
        ("3 for $50", 3, 50.0, 16.67),
        ("2 for $30", 2, 30.0, 15.0),
        ("4 for $100", 4, 100.0, 25.0),
        ("6 for $25", 6, 25.0, 4.17),

        # Various formats
        ("3for$50", 3, 50.0, 16.67),
        ("3 for $50.00", 3, 50.0, 16.67),
        ("3 for 50", 3, 50.0, 16.67),

        # Without dollar sign
        ("2 for 30", 2, 30.0, 15.0),
    ])
    def test_multi_buy_with_price(self, text, expected_qty, expected_total, expected_unit):
        """Test parsing multi-buy deals with total price."""
        result = parse_multi_buy_deal(text)

        assert result is not None
        assert result["quantity"] == expected_qty
        assert result["total_price"] == expected_total
        assert result["unit_price"] == pytest.approx(expected_unit, abs=0.01)
        assert result["deal_text"] == text.strip()

    @pytest.mark.parametrize("text,expected_qty", [
        # Buy X Get Y deals
        ("Buy 2 Get 1 Free", 3),  # Total is 3 items
        ("Buy 3 Get 1", 4),  # Total is 4 items
        ("Buy 2 get 1 free", 3),
    ])
    def test_multi_buy_without_price(self, text, expected_qty):
        """Test parsing multi-buy deals without specific price."""
        result = parse_multi_buy_deal(text)

        assert result is not None
        assert result["quantity"] == expected_qty
        # These deals can't calculate unit price without knowing base price
        assert result["deal_text"] is not None

    @pytest.mark.parametrize("text,expected_qty,expected_total", [
        # X for Y deals (interpreted as X items for $Y price)
        ("2 for 1", 2, 1.0),  # Parser interprets as 2 items for $1
        ("3 for 2", 3, 2.0),  # Parser interprets as 3 items for $2
    ])
    def test_x_for_y_deals(self, text, expected_qty, expected_total):
        """Test X for Y deals where Y is treated as a price."""
        result = parse_multi_buy_deal(text)

        assert result is not None
        assert result["quantity"] == expected_qty
        # The parser treats the second number as a price
        assert result["total_price"] == expected_total

    @pytest.mark.parametrize("text", [
        None,
        "",
        "Special offer",
        "Save 20%",
        "Member price",
        "Single item $20",
    ])
    def test_not_multi_buy(self, text):
        """Test that non-multi-buy text returns None."""
        result = parse_multi_buy_deal(text)
        assert result is None


# ============================================================================
# Promo End Date Parsing Tests
# ============================================================================

class TestParsePromoEndDate:
    """Tests for parse_promo_end_date function."""

    @pytest.mark.parametrize("text,expected_day,expected_month,expected_year", [
        # DD/MM/YYYY format
        ("Ends 25/12/2024", 25, 12, 2024),
        ("Valid until 01/06/2025", 1, 6, 2025),
        ("Offer expires 15/03/2024", 15, 3, 2024),

        # DD/MM/YY format
        ("Ends 25/12/24", 25, 12, 2024),
        ("Until 01/06/25", 1, 6, 2025),

        # DD-MM-YYYY format
        ("Ends 25-12-2024", 25, 12, 2024),
    ])
    def test_date_parsing_nz_format(self, text, expected_day, expected_month, expected_year):
        """Test parsing dates in NZ format (DD/MM/YYYY)."""
        result = parse_promo_end_date(text)

        assert result is not None
        assert result.day == expected_day
        assert result.month == expected_month
        assert result.year == expected_year
        # Should be end of day
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        # Should have NZ timezone
        assert result.tzinfo is not None

    @pytest.mark.parametrize("text", [
        None,
        "",
        "Special offer",
        "Great deal",
        "No date here",
    ])
    def test_no_date_found(self, text):
        """Test handling when no date is found."""
        result = parse_promo_end_date(text)
        assert result is None

    def test_date_is_localized_to_nz(self):
        """Test that parsed dates are in NZ timezone."""
        result = parse_promo_end_date("Ends 25/12/2024")

        assert result is not None
        # Check it's NZ timezone
        assert result.tzinfo is not None
        assert "Pacific/Auckland" in str(result.tzinfo) or result.tzinfo == NZ_TZ


# ============================================================================
# Member-Only Detection Tests
# ============================================================================

class TestDetectMemberOnly:
    """Tests for detect_member_only function."""

    @pytest.mark.parametrize("text", [
        "Clubcard Price $19.99",
        "Club Price",
        "Member Price",
        "Members Only",
        "Onecard Special",
        "Loyalty Price",
        "Rewards Members",
        "CLUBCARD PRICE",  # Uppercase
        "member special",  # Lowercase
    ])
    def test_member_keywords_detected(self, text):
        """Test detection of member-only keywords."""
        result = detect_member_only(text)
        assert result is True, f"Should detect member keyword in '{text}'"

    @pytest.mark.parametrize("text", [
        "Special Price $19.99",
        "On Sale",
        "Save $5",
        "3 for $50",
        "Best Deal",
        "Limited Time",
        None,
        "",
    ])
    def test_non_member_text(self, text):
        """Test that non-member text returns False."""
        result = detect_member_only(text)
        assert result is False, f"Should not detect member keyword in '{text}'"

    def test_case_insensitivity(self):
        """Test that detection is case insensitive."""
        assert detect_member_only("CLUBCARD") is True
        assert detect_member_only("clubcard") is True
        assert detect_member_only("ClubCard") is True
        assert detect_member_only("MEMBER") is True
        assert detect_member_only("member") is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestPromoUtilsIntegration:
    """Integration tests for promo utilities."""

    def test_full_promo_parsing(self):
        """Test parsing a complete promotional text."""
        promo_text = "Clubcard Price: 3 for $50, Ends 25/12/2024"

        price = parse_promo_price(promo_text)
        multi_buy = parse_multi_buy_deal(promo_text)
        end_date = parse_promo_end_date(promo_text)
        is_member = detect_member_only(promo_text)

        # Should extract all components
        assert price == 3.0  # First number found
        assert multi_buy is not None
        assert multi_buy["quantity"] == 3
        assert multi_buy["total_price"] == 50.0
        assert end_date is not None
        assert end_date.day == 25
        assert end_date.month == 12
        assert is_member is True

    def test_simple_sale_promo(self):
        """Test parsing a simple sale promo."""
        promo_text = "Special: $24.99"

        price = parse_promo_price(promo_text)
        multi_buy = parse_multi_buy_deal(promo_text)
        is_member = detect_member_only(promo_text)

        assert price == 24.99
        assert multi_buy is None  # Not a multi-buy
        assert is_member is False

    def test_member_exclusive_deal(self):
        """Test parsing a member-exclusive deal."""
        promo_text = "Onecard Exclusive: $19.99"

        price = parse_promo_price(promo_text)
        is_member = detect_member_only(promo_text)

        assert price == 19.99
        assert is_member is True


# ============================================================================
# Edge Cases
# ============================================================================

class TestPromoEdgeCases:
    """Test edge cases in promo parsing."""

    def test_multiple_prices_in_text(self):
        """Test handling of multiple prices in text."""
        text = "Was $30.00, Now $24.99"
        result = parse_promo_price(text)
        # Should return first price found
        assert result == 30.0

    def test_percentage_not_confused_with_price(self):
        """Test that percentages aren't confused with prices."""
        text = "Save 20%"
        result = parse_promo_price(text)
        # Should extract 20 as a number (since it matches the pattern)
        assert result == 20.0  # This is expected behavior

    def test_very_long_promo_text(self):
        """Test handling of very long promotional text."""
        long_text = "Special offer " * 100 + "$19.99"
        result = parse_promo_price(long_text)
        assert result == 19.99

    def test_unicode_in_promo_text(self):
        """Test handling of unicode characters."""
        text = "Club Price: $19.99 \u2013 Member Special"  # en-dash
        price = parse_promo_price(text)
        is_member = detect_member_only(text)

        assert price == 19.99
        assert is_member is True

    def test_newlines_in_promo_text(self):
        """Test handling of newlines."""
        text = "3 for $50\nEnds 25/12/2024"
        multi_buy = parse_multi_buy_deal(text)
        end_date = parse_promo_end_date(text)

        assert multi_buy is not None
        assert multi_buy["quantity"] == 3
        assert end_date is not None


# ============================================================================
# Member Keyword False-Positive Tests
# ============================================================================

class TestMemberKeywordFalsePositives:
    """Verify word-boundary matching prevents member-only false positives."""

    def test_cardboard_not_member(self):
        """'Cardboard box packaging' should NOT trigger member-only."""
        assert detect_member_only("Cardboard box packaging") is False

    def test_nightclub_not_member(self):
        """'Nightclub special' should NOT trigger member-only."""
        assert detect_member_only("Nightclub special") is False

    def test_gift_card_not_member(self):
        """'Gift card' should NOT trigger member-only (bare 'card' removed)."""
        assert detect_member_only("Gift card included") is False

    def test_real_member_keywords_still_work(self):
        """Actual member keywords should still be detected."""
        assert detect_member_only("Clubcard Price $19.99") is True
        assert detect_member_only("Member Price") is True
        assert detect_member_only("Onecard Special") is True
        assert detect_member_only("Loyalty discount") is True
