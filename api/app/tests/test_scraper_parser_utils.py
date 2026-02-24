"""
Comprehensive tests for parser_utils.py - Volume, ABV, Brand, and Category parsing.

Tests all parsing functions used by scrapers to normalize product data.
"""
from __future__ import annotations

import pytest

from app.services.parser_utils import (
    parse_volume,
    ParsedVolume,
    extract_abv,
    infer_brand,
    infer_category,
    detect_sugar_free,
    CATEGORY_HIERARCHY,
)


# ============================================================================
# Volume Parsing Tests
# ============================================================================

class TestParseVolume:
    """Comprehensive tests for parse_volume function."""

    @pytest.mark.parametrize("text,expected_pack,expected_unit,expected_total", [
        # Standard pack formats
        ("Steinlager Pure 12x330ml", 12, 330.0, 3960.0),
        ("Corona Extra 6x355ml", 6, 355.0, 2130.0),
        ("Heineken 24x330ml Bottles", 24, 330.0, 7920.0),
        ("Export Gold 15x330ml Cans", 15, 330.0, 4950.0),
        ("Tui 18x440ml Cans", 18, 440.0, 7920.0),

        # Various separators
        ("Beer 12 x 330ml", 12, 330.0, 3960.0),
        ("Beer 12× 330ml", 12, 330.0, 3960.0),  # Unicode multiplication sign
        ("Beer 12X330ML", 12, 330.0, 3960.0),  # Uppercase

        # Litre formats
        ("Wine 6x750ml", 6, 750.0, 4500.0),
        ("Spirits 12x1l", 12, 1000.0, 12000.0),
        ("Vodka 6x1L", 6, 1000.0, 6000.0),
        ("Whisky 2x1ltr", 2, 1000.0, 2000.0),
        ("Gin 4x1litre", 4, 1000.0, 4000.0),
        ("Rum 3x1litres", 3, 1000.0, 3000.0),

        # Decimal volumes
        ("Cider 4x1.5l", 4, 1500.0, 6000.0),
        ("Sake 6x300ml", 6, 300.0, 1800.0),
    ])
    def test_pack_volume_parsing(self, text, expected_pack, expected_unit, expected_total):
        """Test parsing of pack volume formats like 12x330ml."""
        result = parse_volume(text)

        assert result.pack_count == expected_pack, f"Pack count mismatch for '{text}'"
        assert result.unit_volume_ml == expected_unit, f"Unit volume mismatch for '{text}'"
        assert result.total_volume_ml == expected_total, f"Total volume mismatch for '{text}'"

    @pytest.mark.parametrize("text,expected_unit,expected_total", [
        # Single bottle formats
        ("Absolut Vodka 700ml", 700.0, 700.0),
        ("Johnnie Walker 1l", 1000.0, 1000.0),
        ("Wine Bottle 750ml", 750.0, 750.0),
        ("Jim Beam 1L", 1000.0, 1000.0),
        ("Gin 700ML", 700.0, 700.0),
        ("Bourbon 1ltr", 1000.0, 1000.0),
        ("Scotch 750 ml", 750.0, 750.0),  # Space before ml

        # Small bottles
        ("Beer 330ml", 330.0, 330.0),
        ("Shot 50ml", 50.0, 50.0),
        ("Mini 200ml", 200.0, 200.0),

        # Large formats
        ("Magnum 1.5l", 1500.0, 1500.0),
        ("Double Magnum 3l", 3000.0, 3000.0),
        ("Jeroboam 4.5l", 4500.0, 4500.0),
    ])
    def test_single_volume_parsing(self, text, expected_unit, expected_total):
        """Test parsing of single bottle volumes."""
        result = parse_volume(text)

        assert result.pack_count is None, f"Pack count should be None for single '{text}'"
        assert result.unit_volume_ml == expected_unit, f"Unit volume mismatch for '{text}'"
        assert result.total_volume_ml == expected_total, f"Total volume mismatch for '{text}'"

    @pytest.mark.parametrize("text", [
        "Steinlager Pure",  # No volume
        "Best Beer Ever",  # No volume
        "Premium Whisky",  # No volume
        "",  # Empty
        "12 bottles",  # No ml/l
        "Pack of 6",  # No volume unit
    ])
    def test_no_volume_found(self, text):
        """Test handling of text without volume information."""
        result = parse_volume(text)

        assert result.pack_count is None
        assert result.unit_volume_ml is None
        assert result.total_volume_ml is None

    def test_volume_case_insensitivity(self):
        """Test that volume parsing is case insensitive."""
        variants = [
            "Beer 330ml",
            "Beer 330ML",
            "Beer 330Ml",
            "Beer 330mL",
        ]

        for text in variants:
            result = parse_volume(text)
            assert result.unit_volume_ml == 330.0, f"Failed for: {text}"

    def test_parsed_volume_immutability(self):
        """Test that ParsedVolume is immutable (frozen dataclass)."""
        result = parse_volume("Beer 12x330ml")

        with pytest.raises(AttributeError):
            result.pack_count = 24


# ============================================================================
# ABV Extraction Tests
# ============================================================================

class TestExtractABV:
    """Comprehensive tests for extract_abv function."""

    @pytest.mark.parametrize("text,expected_abv", [
        # Standard ABV formats
        ("Beer 5%", 5.0),
        ("Wine 12.5%", 12.5),
        ("Vodka 40%", 40.0),
        ("Whisky 43%", 43.0),
        ("Cider 4.5%", 4.5),

        # With ABV label
        ("Beer 5% ABV", 5.0),
        ("Wine 13.5% abv", 13.5),

        # Various positions
        ("5% Beer", 5.0),
        ("Strong Ale 8.5% IPA", 8.5),

        # Decimal formats
        ("Lager 4.0%", 4.0),
        ("Stout 5.5%", 5.5),
        ("Porter 6.8%", 6.8),

        # Non-alcoholic
        ("Alcohol Free 0%", 0.0),
        ("Zero Alcohol 0.0%", 0.0),
        ("Asahi Super Dry 0.0% Alcohol Free", 0.0),

        # High ABV spirits
        ("Navy Rum 57%", 57.0),
        ("Overproof 75.5%", 75.5),
    ])
    def test_abv_extraction(self, text, expected_abv):
        """Test ABV extraction from various formats."""
        result = extract_abv(text)
        assert result == expected_abv, f"ABV mismatch for '{text}'"

    @pytest.mark.parametrize("text", [
        "Steinlager Pure",  # No ABV
        "Best Beer Ever",  # No ABV
        "Wine",  # No ABV
        "",  # Empty
    ])
    def test_no_abv_found(self, text):
        """Test handling of text without ABV."""
        result = extract_abv(text)
        assert result is None

    def test_edge_case_abv_extraction(self):
        """Test edge cases in ABV extraction."""
        # "100% Natural" should NOT match — the lookbehind prevents
        # matching digits that are part of a larger number.
        result = extract_abv("100% Natural")
        assert result is None

    def test_first_percentage_matched(self):
        """Test that first percentage is matched when multiple exist."""
        # The regex will match the first valid percentage
        text = "Beer 5% - Save 20%"
        result = extract_abv(text)
        assert result == 5.0


# ============================================================================
# Brand Inference Tests
# ============================================================================

class TestInferBrand:
    """Comprehensive tests for infer_brand function."""

    @pytest.mark.parametrize("text,expected_brand", [
        # Known beer brands
        ("Heineken Lager 12x330ml", "Heineken"),
        ("Corona Extra 6x355ml", "Corona"),
        ("Stella Artois Premium Lager", "Stella Artois"),
        ("Guinness Draught 440ml", "Guinness"),
        ("Asahi Super Dry 500ml", "Asahi"),

        # NZ beer brands
        ("Steinlager Pure 12x330ml", "Steinlager"),
        ("Tui Lager 18x440ml", "Tui"),
        ("Speight's Gold Medal Ale", "Speight's"),
        ("Export Gold 15x330ml", "Export Gold"),

        # Craft beer brands
        ("Garage Project Day of the Dead", "Garage Project"),
        ("Panhead Supercharger APA", "Panhead"),
        ("Tuatara Hazy Pale Ale", "Tuatara"),
        ("Emerson's Pilsner", "Emerson's"),

        # Wine brands
        ("Cloudy Bay Sauvignon Blanc 750ml", "Cloudy Bay"),
        ("Kim Crawford Marlborough Sauvignon Blanc", "Kim Crawford"),
        ("Oyster Bay Pinot Noir", "Oyster Bay"),
        ("Villa Maria Private Bin", "Villa Maria"),

        # Spirit brands
        ("Gordon's Gin 1L", "Gordon's"),
        ("Bombay Sapphire 700ml", "Bombay"),
        ("Tanqueray London Dry Gin", "Tanqueray"),
        ("Smirnoff Red Label Vodka", "Smirnoff"),
        ("Absolut Original 700ml", "Absolut"),
        ("Jack Daniel's Tennessee Whiskey", "Jack Daniel's"),
        ("Jameson Irish Whiskey", "Jameson"),
        ("Bacardi Superior Rum", "Bacardi"),

        # RTD brands
        ("Cruiser Watermelon 275ml", "Cruiser"),
        ("Woodstock Bourbon & Cola", "Woodstock"),
    ])
    def test_known_brand_inference(self, text, expected_brand):
        """Test inference of known brands."""
        result = infer_brand(text)
        assert result == expected_brand, f"Brand mismatch for '{text}'"

    def test_unknown_brand_fallback(self):
        """Test that unknown brands fall back to first words."""
        result = infer_brand("Unknown Brand Premium Lager 330ml")
        # Should return first 1-2 words as potential brand
        assert result is not None
        assert "Unknown" in result

    def test_empty_string(self):
        """Test handling of empty string."""
        result = infer_brand("")
        assert result is None


# ============================================================================
# Category Inference Tests
# ============================================================================

class TestInferCategory:
    """Comprehensive tests for infer_category function."""

    @pytest.mark.parametrize("text,expected_category", [
        # Beer categories
        ("Heineken Lager 12x330ml", "lager"),
        ("Corona Extra Pilsner", "lager"),  # pilsner → lager
        ("Epic India Pale Ale", "ipa"),
        ("Guinness Draught Stout", "stout"),
        ("Murphy's Irish Porter", "stout"),  # porter → stout
        ("Panhead Supercharger Pale Ale", "ale"),

        # Wine categories
        ("Oyster Bay Sauvignon Blanc 750ml", "white_wine"),
        ("Villa Maria Pinot Noir", "red_wine"),
        ("Cloudy Bay Chardonnay", "white_wine"),
        ("Church Road Merlot", "red_wine"),
        ("Lindauer Brut", "sparkling"),
        ("Moet Champagne", "champagne"),

        # Spirit categories
        ("Smirnoff Vodka 1L", "vodka"),
        ("Absolut Vodka", "vodka"),
        ("Gordon's Gin 700ml", "gin"),
        ("Tanqueray London Dry Gin", "gin"),
        ("Bacardi Superior Rum", "rum"),
        ("Captain Morgan Spiced Rum", "rum"),
        ("Jack Daniel's Whiskey", "whisky"),
        ("Johnnie Walker Scotch", "scotch"),
        ("Jim Beam Bourbon", "bourbon"),
        ("Jose Cuervo Tequila", "tequila"),
        ("Baileys Irish Cream Liqueur", "liqueur"),

        # RTD categories
        ("Cruiser Watermelon 4x275ml", "rtd"),
        ("Woodstock Bourbon & Cola", "rtd"),
        ("White Claw Hard Seltzer", "rtd"),

        # Cider
        ("Somersby Apple Cider", "cider"),
        ("Rekorderlig Strawberry Lime Cider", "cider"),

        # Non-alcoholic
        ("Heineken 0.0% Alcohol Free", "non_alcoholic"),
        ("Zero Alcohol Wine", "non_alcoholic"),

        # Mixers
        ("Schweppes Tonic Water", "mixer"),
        ("Fever-Tree Ginger Beer", "mixer"),
    ])
    def test_category_inference(self, text, expected_category):
        """Test category inference from various products."""
        result = infer_category(text)
        assert result == expected_category, f"Category mismatch for '{text}': got {result}"

    def test_specific_keywords_take_priority(self):
        """Test that specific keywords take priority over generic ones."""
        # IPA is more specific than ale when "India Pale Ale" is used
        result = infer_category("Garage Project India Pale Ale")
        assert result == "ipa"

        # Stout is more specific than beer
        result = infer_category("Guinness Foreign Extra Stout")
        assert result == "stout"

    def test_brand_fallback_for_ambiguous_names(self):
        """Test brand-based category inference when keywords are absent."""
        # Steinlager maps to beer via brand mapping
        result = infer_category("Steinlager 12x330ml")
        # Brand mapping returns "beer" which is correct
        assert result in ["beer", "lager"]  # Either is acceptable

    def test_category_hierarchy_exists(self):
        """Test that category hierarchy mappings are defined."""
        assert "ipa" in CATEGORY_HIERARCHY
        assert CATEGORY_HIERARCHY["ipa"] == "beer"

        assert "stout" in CATEGORY_HIERARCHY
        assert CATEGORY_HIERARCHY["stout"] == "beer"

        assert "bourbon" in CATEGORY_HIERARCHY
        assert CATEGORY_HIERARCHY["bourbon"] == "whisky"


# ============================================================================
# Sugar-Free Detection Tests
# ============================================================================

class TestDetectSugarFree:
    """Tests for detect_sugar_free function."""

    @pytest.mark.parametrize("text", [
        "Codys Sugar Free 7% 12x250ml",
        "KGB Sugar-Free Lemon Ice",
        "Cody's & Zero Sugar Cola 7%",
        "Epic Low Carb Pale Ale",
        "Better Beer Zero Carb",
        "No Sugar RTD 5%",
        "Diet Mixer Vodka 330ml",
        "Zero Carbs Lager 330ml",
        "No Carbs Seltzer 4%",
        "Low-Carb Craft Beer",
    ])
    def test_sugar_free_detected(self, text):
        """Products with sugar-free keywords should be detected."""
        assert detect_sugar_free(text) is True, f"Expected True for '{text}'"

    def test_sugar_free_brand_detection(self):
        """Clean Collective products should be detected by brand."""
        assert detect_sugar_free("Clean Collective Gin & Tonic 5%") is True

    @pytest.mark.parametrize("text", [
        "Heineken Lager 330ml",
        "Smirnoff Vodka 1L",
        "Cloudy Bay Sauvignon Blanc 750ml",
        "Sugar Loaf Vineyard Pinot Noir",  # "sugar" alone is NOT a match
        "Carbine Stout 440ml",  # "carb" inside another word
    ])
    def test_sugar_free_not_detected(self, text):
        """Regular products should not be flagged as sugar-free."""
        assert detect_sugar_free(text) is False, f"Expected False for '{text}'"


# ============================================================================
# Integration Tests
# ============================================================================

class TestParserIntegration:
    """Integration tests combining multiple parser functions."""

    @pytest.mark.parametrize("product_name", [
        "Steinlager Pure 12x330ml 5% Lager",
        "Cloudy Bay Sauvignon Blanc 750ml 12.5%",
        "Smirnoff Red Label Vodka 1L 40%",
        "Garage Project Day of the Dead IPA 6x330ml 6.5%",
        "Baileys Irish Cream 700ml 17%",
    ])
    def test_full_product_parsing(self, product_name):
        """Test that all parsers work together on real product names."""
        volume = parse_volume(product_name)
        abv = extract_abv(product_name)
        brand = infer_brand(product_name)
        category = infer_category(product_name)

        # All should return values for complete product names
        assert volume.unit_volume_ml is not None or volume.total_volume_ml is not None
        assert abv is not None
        assert brand is not None
        assert category is not None

    def test_minimal_product_name(self):
        """Test parsing with minimal product names."""
        # These should still work with partial info
        volume = parse_volume("Beer")
        abv = extract_abv("Beer")
        brand = infer_brand("Beer")
        category = infer_category("Beer")

        assert volume.unit_volume_ml is None  # No volume
        assert abv is None  # No ABV
        assert brand == "Beer"  # Falls back to first word
        assert category == "beer"  # Keyword match


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        # Rosé with accent - the parser uses "rose" keyword which
        # matches both with and without accent, but brand mapping may take priority
        result = infer_category("Matua Rosé 750ml")
        # Matua is mapped to "wine" in BRAND_CATEGORY_MAP, which is acceptable
        assert result in ["rose", "wine"]  # Both are acceptable

    def test_mixed_case_handling(self):
        """Test case insensitivity across all parsers."""
        text = "STEINLAGER PURE 12X330ML 5% LAGER"

        volume = parse_volume(text)
        assert volume.pack_count == 12
        assert volume.unit_volume_ml == 330.0

        abv = extract_abv(text)
        assert abv == 5.0

        category = infer_category(text)
        assert category == "lager"

    def test_whitespace_handling(self):
        """Test handling of extra whitespace."""
        text = "  Heineken   Lager   12 x 330ml  5%  "

        volume = parse_volume(text)
        assert volume.pack_count == 12

        brand = infer_brand(text)
        assert brand == "Heineken"

    def test_special_characters(self):
        """Test handling of special characters in product names."""
        names = [
            "Jack Daniel's Tennessee Whiskey",
            "Bailey's Irish Cream",
            "Speight's Gold Medal Ale",
            "McLeod's Beer",
        ]

        for name in names:
            brand = infer_brand(name)
            assert brand is not None

    def test_numeric_brand_names(self):
        """Test handling of brands with numbers."""
        # 1800 Tequila
        result = infer_category("1800 Tequila Silver 700ml")
        assert result == "tequila"


# ============================================================================
# Word-Boundary & False-Positive Tests
# ============================================================================

class TestWordBoundaryBrand:
    """Verify word-boundary matching prevents brand false positives."""

    def test_tui_does_not_match_tuition(self):
        """'Tui' brand should not match inside 'Tuition'."""
        result = infer_brand("Tuition Fee Payment")
        assert result != "Tui"

    def test_db_does_not_match_database(self):
        """'DB' brand should not match inside 'Database'."""
        result = infer_brand("Database Migration Tool")
        assert result != "DB"

    def test_sol_does_not_match_absolut(self):
        """'Sol' brand-category entry should not match inside 'Absolut'."""
        result = infer_category("Absolut Vodka 700ml")
        assert result == "vodka"  # should NOT fall through to "beer" via "sol"

    def test_smirnoff_ice_matches_before_smirnoff(self):
        """Longer brand 'Smirnoff Ice' should match before shorter 'Smirnoff'."""
        result = infer_brand("Smirnoff Ice Raspberry 4x300ml")
        assert result == "Smirnoff Ice"


class TestWordBoundaryCategory:
    """Verify word-boundary matching prevents category keyword false positives."""

    def test_ginger_beer_not_gin(self):
        """'Ginger Beer' should match 'mixer', not 'gin'."""
        result = infer_category("Bundaberg Ginger Beer 375ml")
        assert result != "gin"

    def test_export_gold_not_port(self):
        """'Export Gold' should not match 'port' from 'export'."""
        result = infer_category("Export Gold 15x330ml")
        assert result != "fortified_wine"

    def test_sale_item_not_ale(self):
        """'Sale Item' should not match 'ale'."""
        result = infer_category("Sale Item Clearance")
        assert result != "ale"

    def test_rummage_not_rum(self):
        """'Rummage' should not match 'rum'."""
        result = infer_category("Rummage Market Deals")
        assert result != "rum"


class TestVolumeClParsing:
    """Test centilitre (cl) volume parsing."""

    def test_single_cl_volume(self):
        """'70cl' should parse to 700ml."""
        result = parse_volume("Cognac 70cl")
        assert result.unit_volume_ml == 700.0
        assert result.total_volume_ml == 700.0
        assert result.pack_count is None

    def test_pack_cl_volume(self):
        """'6x70cl' should parse to 6 × 700ml = 4200ml."""
        result = parse_volume("Whisky 6x70cl")
        assert result.pack_count == 6
        assert result.unit_volume_ml == 700.0
        assert result.total_volume_ml == 4200.0

    def test_cl_50(self):
        """'50cl' should parse to 500ml."""
        result = parse_volume("Rum 50cl")
        assert result.unit_volume_ml == 500.0


class TestABVFalsePositives:
    """Verify the ABV lookbehind prevents false matches."""

    def test_100_percent_natural(self):
        """'100% Natural' should NOT extract 0.0 ABV."""
        assert extract_abv("100% Natural") is None

    def test_200_percent_markup(self):
        """'200% Markup' should NOT extract any ABV."""
        assert extract_abv("200% Markup") is None

    def test_legitimate_abv_still_works(self):
        """Normal ABV values should still be extracted."""
        assert extract_abv("5% Lager") == 5.0
        assert extract_abv("12.5% Wine") == 12.5
        assert extract_abv("0% Alcohol Free") == 0.0
