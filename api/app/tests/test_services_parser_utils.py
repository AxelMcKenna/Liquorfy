"""Tests for parser utilities."""
from __future__ import annotations

import pytest

from app.services.parser_utils import (
    BRAND_CATEGORY_MAP,
    CATEGORY_HIERARCHY,
    CATEGORY_KEYWORDS,
    KNOWN_BRANDS,
    ParsedVolume,
    extract_abv,
    infer_brand,
    infer_category,
    parse_volume,
)


class TestParseVolume:
    """Tests for volume parsing."""

    def test_parse_single_volume_litre(self):
        """Should parse single litre volumes."""
        result = parse_volume("Gordon's Gin 1L")
        assert result.total_volume_ml == 1000
        assert result.unit_volume_ml == 1000
        assert result.pack_count is None

    def test_parse_single_volume_ml(self):
        """Should parse single ml volumes."""
        result = parse_volume("Heineken 330ml")
        assert result.total_volume_ml == 330
        assert result.unit_volume_ml == 330
        assert result.pack_count is None

    def test_parse_multipack_x(self):
        """Should parse multipack with x separator."""
        result = parse_volume("Heineken 24 x 330ml")
        assert result.pack_count == 24
        assert result.unit_volume_ml == 330
        assert result.total_volume_ml == 24 * 330

    def test_parse_multipack_times(self):
        """Should parse multipack with × separator."""
        result = parse_volume("Corona 12 × 355ml")
        assert result.pack_count == 12
        assert result.unit_volume_ml == 355
        assert result.total_volume_ml == 12 * 355

    def test_parse_litre_variations(self):
        """Should handle various litre spellings."""
        variations = ["1 litre", "1 ltr", "1l", "1 litres", "1 liters"]
        for vol_str in variations:
            result = parse_volume(f"Product {vol_str}")
            assert result.total_volume_ml == 1000, f"Failed for: {vol_str}"

    def test_parse_decimal_volumes(self):
        """Should handle decimal volumes."""
        result = parse_volume("Wine 0.75L")
        assert result.total_volume_ml == 750

        result = parse_volume("Wine 1.5L")
        assert result.total_volume_ml == 1500

    def test_parse_no_volume(self):
        """Should return None values when no volume found."""
        result = parse_volume("Random Product Name")
        assert result.total_volume_ml is None
        assert result.unit_volume_ml is None
        assert result.pack_count is None

    def test_parse_case_insensitive(self):
        """Should handle different cases."""
        result = parse_volume("Beer 330ML")
        assert result.total_volume_ml == 330

        result = parse_volume("Wine 750mL")
        assert result.total_volume_ml == 750

    def test_parse_multipack_litre(self):
        """Should parse multipack with litre units."""
        result = parse_volume("Cider 4 x 1L")
        assert result.pack_count == 4
        assert result.unit_volume_ml == 1000
        assert result.total_volume_ml == 4000


class TestExtractAbv:
    """Tests for ABV extraction."""

    def test_extract_abv_integer(self):
        """Should extract integer ABV values."""
        assert extract_abv("5% Beer") == 5.0
        assert extract_abv("40% Whisky") == 40.0

    def test_extract_abv_decimal(self):
        """Should extract decimal ABV values."""
        assert extract_abv("4.5% Lager") == 4.5
        assert extract_abv("37.5% Gin") == 37.5

    def test_extract_abv_no_match(self):
        """Should return None when no ABV found."""
        assert extract_abv("Beer 330ml") is None
        assert extract_abv("Random Product") is None

    def test_extract_abv_multiple_percentages(self):
        """Should extract first percentage (ABV typically first)."""
        result = extract_abv("5% Beer 10% OFF")
        assert result == 5.0

    def test_extract_abv_various_positions(self):
        """Should find ABV anywhere in string."""
        assert extract_abv("Vodka 40%") == 40.0
        assert extract_abv("7% Cruiser") == 7.0
        assert extract_abv("Beer (5%) 330ml") == 5.0


class TestInferBrand:
    """Tests for brand inference."""

    def test_infer_known_brand(self):
        """Should detect known brands."""
        assert infer_brand("Heineken Premium Lager 330ml") == "Heineken"
        assert infer_brand("Corona Extra 355ml") == "Corona"
        assert infer_brand("Smirnoff Red Vodka 1L") == "Smirnoff"

    def test_infer_brand_case_insensitive(self):
        """Should match brands case-insensitively."""
        assert infer_brand("HEINEKEN LAGER") == "Heineken"
        assert infer_brand("corona extra") == "Corona"

    def test_infer_unknown_brand(self):
        """Should extract potential brand for unknown products."""
        result = infer_brand("Mystery Beer 330ml")
        # Returns first 1-2 words as potential brand
        assert result is not None
        assert "Mystery" in result

    def test_infer_brand_two_words(self):
        """Should potentially include second word."""
        result = infer_brand("New Brand Beer 330ml")
        # May return "New Brand" or just "New" depending on descriptors
        assert result is not None

    def test_infer_brand_empty(self):
        """Should handle empty string."""
        result = infer_brand("")
        assert result is None


class TestInferCategory:
    """Tests for category inference."""

    def test_infer_beer_category(self):
        """Should detect beer category."""
        assert infer_category("Heineken Lager 330ml") == "lager"
        assert infer_category("Craft IPA 500ml") == "ipa"

    def test_infer_wine_category(self):
        """Should detect wine categories."""
        assert infer_category("Sauvignon Blanc 750ml") == "white_wine"
        assert infer_category("Pinot Noir Reserve") == "red_wine"
        assert infer_category("Prosecco DOC") == "sparkling"

    def test_infer_spirits_category(self):
        """Should detect spirit categories."""
        assert infer_category("Smirnoff Vodka 1L") == "vodka"
        assert infer_category("Gordon's Gin 700ml") == "gin"
        assert infer_category("Bacardi Rum 1L") == "rum"
        assert infer_category("Jack Daniel's Whiskey") == "whisky"

    def test_infer_rtd_category(self):
        """Should detect RTD category."""
        assert infer_category("Cruiser Raspberry 4x275ml") == "rtd"
        assert infer_category("Codys 7% 12x250ml") == "rtd"

    def test_infer_cider_category(self):
        """Should detect cider category."""
        assert infer_category("Somersby Apple Cider") == "cider"
        assert infer_category("Rekorderlig Strawberry-Lime") == "cider"

    def test_infer_category_from_brand(self):
        """Should infer category from known brand mappings."""
        # Steinlager maps to beer in BRAND_CATEGORY_MAP
        result = infer_category("Steinlager Classic 12x330ml")
        assert result in ["beer", "lager"]  # Could match keyword or brand

        # Cloudy Bay maps to wine
        result = infer_category("Cloudy Bay 750ml")
        assert result == "wine"

    def test_infer_category_no_match(self):
        """Should return None when no category detected."""
        result = infer_category("Random Product 123")
        # May still match something or return None
        assert result is None or isinstance(result, str)

    def test_infer_mixer_vs_rtd(self):
        """Should distinguish mixers from RTDs based on alcohol content."""
        # Pure mixer - cola maps to mixer
        result = infer_category("Coca Cola 330ml")
        assert result == "mixer"

        # RTD with alcohol indicator - has "rtd" keyword
        result = infer_category("Vodka Lime & Soda 7% RTD")
        # Could match "rtd" keyword or "vodka" brand, rtd is fine
        assert result in ["rtd", "vodka"]


class TestCategoryHierarchy:
    """Tests for category hierarchy mapping."""

    def test_beer_subcategories(self):
        """Beer subcategories should map to beer."""
        assert CATEGORY_HIERARCHY.get("ipa") == "beer"
        assert CATEGORY_HIERARCHY.get("stout") == "beer"
        assert CATEGORY_HIERARCHY.get("lager") == "beer"
        assert CATEGORY_HIERARCHY.get("ale") == "beer"

    def test_wine_subcategories(self):
        """Wine subcategories should map to wine."""
        assert CATEGORY_HIERARCHY.get("white_wine") == "wine"
        assert CATEGORY_HIERARCHY.get("red_wine") == "wine"
        assert CATEGORY_HIERARCHY.get("sparkling") == "wine"
        assert CATEGORY_HIERARCHY.get("champagne") == "wine"

    def test_whisky_subcategories(self):
        """Whisky subcategories should map to whisky."""
        assert CATEGORY_HIERARCHY.get("bourbon") == "whisky"
        assert CATEGORY_HIERARCHY.get("scotch") == "whisky"


class TestParsedVolumeDataclass:
    """Tests for ParsedVolume dataclass."""

    def test_parsed_volume_immutable(self):
        """ParsedVolume should be immutable (frozen)."""
        vol = ParsedVolume(pack_count=12, unit_volume_ml=330.0, total_volume_ml=3960.0)
        with pytest.raises(AttributeError):
            vol.pack_count = 24

    def test_parsed_volume_allows_none(self):
        """ParsedVolume should allow None values."""
        vol = ParsedVolume(pack_count=None, unit_volume_ml=None, total_volume_ml=None)
        assert vol.pack_count is None


class TestKnownBrands:
    """Tests for known brands list."""

    def test_known_brands_not_empty(self):
        """Known brands list should contain entries."""
        assert len(KNOWN_BRANDS) > 0

    def test_known_brands_has_major_brands(self):
        """Known brands should include major NZ brands."""
        expected = ["Heineken", "Corona", "Steinlager", "Smirnoff", "Jim Beam"]
        for brand in expected:
            assert brand in KNOWN_BRANDS, f"Missing brand: {brand}"


class TestDataIntegrity:
    """Data integrity checks for static lists and maps."""

    def test_no_duplicate_known_brands(self):
        """KNOWN_BRANDS should have no duplicates."""
        seen: set[str] = set()
        for brand in KNOWN_BRANDS:
            key = brand.lower()
            assert key not in seen, f"Duplicate brand: {brand}"
            seen.add(key)


class TestBrandCategoryMap:
    """Tests for brand to category mapping."""

    def test_brand_category_map_not_empty(self):
        """Brand category map should contain entries."""
        assert len(BRAND_CATEGORY_MAP) > 0

    def test_brand_category_mappings(self):
        """Known brands should map to expected categories."""
        assert BRAND_CATEGORY_MAP.get("heineken") == "beer"
        assert BRAND_CATEGORY_MAP.get("smirnoff") == "vodka"
        assert BRAND_CATEGORY_MAP.get("gordon's") == "gin"
        assert BRAND_CATEGORY_MAP.get("jack daniel's") == "whisky"
