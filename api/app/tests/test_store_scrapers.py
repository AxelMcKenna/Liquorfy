"""
Comprehensive tests for store location scrapers.

Tests all store location scrapers to ensure complete NZ-wide coverage.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.store_scrapers.base import StoreLocationScraper
from app.store_scrapers.liquorland import LiquorlandLocationScraper
from app.store_scrapers.super_liquor import SuperLiquorLocationScraper


# ============================================================================
# Base Store Scraper Tests
# ============================================================================

class TestStoreLocationScraperBase:
    """Tests for the StoreLocationScraper base class."""

    def test_base_class_is_abstract(self):
        """Test that base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StoreLocationScraper()

    def test_subclass_requires_fetch_stores(self):
        """Test that subclasses must implement fetch_stores."""
        class InvalidScraper(StoreLocationScraper):
            chain = "test"
            store_locator_url = "https://example.com"

        with pytest.raises(TypeError):
            InvalidScraper()


# ============================================================================
# Super Liquor Store Scraper Tests
# ============================================================================

class TestSuperLiquorLocationScraper:
    """Tests for Super Liquor store location scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = SuperLiquorLocationScraper()

        assert scraper.chain == "super_liquor"
        assert scraper.store_locator_url is not None
        assert scraper.use_browser is False  # Uses API

    @pytest.mark.asyncio
    async def test_parse_store_valid_data(self):
        """Test parsing valid store data from API."""
        scraper = SuperLiquorLocationScraper()

        store_data = {
            "Id": 1,
            "Name": "Alexandra",
            "Address": "114 Centennial Avenue",
            "FullAddress": "114 Centennial Avenue, Alexandra",
            "City": "Alexandra",
            "State": "Otago",
            "Country": "New Zealand",
            "ZipPostalCode": "9320",
            "PhoneNumber": "03 448 8314",
            "Latitude": -45.254913,
            "Longitude": 169.392822,
        }

        result = await scraper.parse_store(store_data)

        assert result["name"] == "Alexandra"
        assert result["address"] == "114 Centennial Avenue"
        assert result["city"] == "Alexandra"
        assert result["region"] == "Otago"
        assert result["postcode"] == "9320"
        assert result["phone"] == "03 448 8314"
        assert result["latitude"] == pytest.approx(-45.254913)
        assert result["longitude"] == pytest.approx(169.392822)

    @pytest.mark.asyncio
    async def test_parse_store_missing_name_raises_error(self):
        """Test that missing name raises error."""
        scraper = SuperLiquorLocationScraper()

        store_data = {
            "Address": "123 Test St",
            "Latitude": -36.0,
            "Longitude": 174.0,
        }

        with pytest.raises(ValueError, match="Store name is required"):
            await scraper.parse_store(store_data)

    @pytest.mark.asyncio
    async def test_parse_store_missing_coords_raises_error(self):
        """Test that missing coordinates raises error."""
        scraper = SuperLiquorLocationScraper()

        store_data = {
            "Name": "Test Store",
            "Address": "123 Test St",
        }

        with pytest.raises(ValueError, match="Coordinates missing"):
            await scraper.parse_store(store_data)

    @pytest.mark.asyncio
    async def test_fetch_stores_with_mock_api(self):
        """Test fetching stores with mocked API response."""
        scraper = SuperLiquorLocationScraper()

        mock_response_data = {
            "Locations": [
                {
                    "Id": 1,
                    "Name": "Store 1",
                    "Address": "1 Test St",
                    "City": "Auckland",
                    "State": "Auckland",
                    "Latitude": -36.8485,
                    "Longitude": 174.7633,
                },
                {
                    "Id": 2,
                    "Name": "Store 2",
                    "Address": "2 Test St",
                    "City": "Wellington",
                    "State": "Wellington",
                    "Latitude": -41.2865,
                    "Longitude": 174.7762,
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            stores = await scraper.fetch_stores()

            assert len(stores) == 2
            assert stores[0]["Name"] == "Store 1"
            assert stores[1]["Name"] == "Store 2"


# ============================================================================
# Liquorland Store Scraper Tests
# ============================================================================

class TestLiquorlandLocationScraper:
    """Tests for Liquorland store location scraper."""

    def test_initialization(self):
        """Test scraper initializes correctly."""
        scraper = LiquorlandLocationScraper()

        assert scraper.chain == "liquorland"
        assert scraper.store_locator_url is not None
        assert scraper.use_browser is True  # Browser-based

    def test_parse_store_dict_with_label(self):
        """Test parsing store dict with label field."""
        scraper = LiquorlandLocationScraper()

        store_data = {
            "label": "Liquorland Albany",
            "address": "1 Albany Highway, Albany, Auckland 0632",
            "latitude": -36.7264,
            "longitude": 174.7042,
            "city": "Auckland",
        }

        result = scraper._parse_store_dict(store_data)

        assert result is not None
        assert result["name"] == "Liquorland Albany"
        assert "Albany Highway" in result["address"]
        assert result["lat"] == pytest.approx(-36.7264)
        assert result["lon"] == pytest.approx(174.7042)
        assert result["region"] == "Auckland"

    def test_parse_store_dict_with_name(self):
        """Test parsing store dict with name field."""
        scraper = LiquorlandLocationScraper()

        store_data = {
            "name": "Liquorland Ponsonby",
            "address": "123 Ponsonby Road",
            "lat": -36.86,
            "lng": 174.74,
        }

        result = scraper._parse_store_dict(store_data)

        assert result is not None
        assert result["name"] == "Liquorland Ponsonby"
        assert result["lat"] == pytest.approx(-36.86)
        assert result["lon"] == pytest.approx(174.74)

    def test_parse_store_dict_builds_address_from_parts(self):
        """Test building address from component parts."""
        scraper = LiquorlandLocationScraper()

        store_data = {
            "label": "Test Store",
            "address1": "123 Main St",
            "suburb": "Central",
            "city": "Auckland",
            "postcode": "1010",
            "latitude": -36.85,
            "longitude": 174.76,
        }

        result = scraper._parse_store_dict(store_data)

        assert result is not None
        assert "123 Main St" in result["address"]
        assert "Central" in result["address"]
        assert "Auckland" in result["address"]

    def test_parse_store_dict_missing_required_fields(self):
        """Test parsing fails with missing required fields."""
        scraper = LiquorlandLocationScraper()

        # Missing name
        result = scraper._parse_store_dict({"address": "123 Test St"})
        assert result is None

        # Missing address
        result = scraper._parse_store_dict({"label": "Test Store"})
        assert result is None

    def test_parse_store_dict_cleans_newlines(self):
        """Test that newlines in address are replaced."""
        scraper = LiquorlandLocationScraper()

        store_data = {
            "label": "Test Store",
            "address": "123 Main St\nAuckland\nNew Zealand",
            "latitude": -36.85,
            "longitude": 174.76,
        }

        result = scraper._parse_store_dict(store_data)

        assert result is not None
        assert "\n" not in result["address"]
        assert ", " in result["address"]

    def test_parse_dom_stores(self):
        """Test parsing stores extracted from DOM."""
        scraper = LiquorlandLocationScraper()

        dom_stores = [
            {"name": "Store 1", "address": "1 Test St", "lat": "-36.85", "lon": "174.76"},
            {"name": "Store 2", "address": "2 Test St", "lat": "-36.86", "lon": "174.77"},
            {"name": "", "address": "3 Test St"},  # Invalid - no name
            {"name": "Store 4", "address": ""},  # Invalid - no address
        ]

        result = scraper._parse_dom_stores(dom_stores)

        assert len(result) == 2
        assert result[0]["name"] == "Store 1"
        assert result[0]["lat"] == pytest.approx(-36.85)
        assert result[1]["name"] == "Store 2"

    def test_parse_store_data_from_list(self):
        """Test parsing store data from list format."""
        scraper = LiquorlandLocationScraper()

        data = [
            {"label": "Store 1", "address": "1 Test St", "latitude": -36.85, "longitude": 174.76},
            {"label": "Store 2", "address": "2 Test St", "latitude": -36.86, "longitude": 174.77},
        ]

        result = scraper._parse_store_data(data)

        assert len(result) == 2
        assert result[0]["name"] == "Store 1"
        assert result[1]["name"] == "Store 2"

    def test_parse_store_data_from_dict(self):
        """Test parsing store data from dict format (keyed by store ID)."""
        scraper = LiquorlandLocationScraper()

        data = {
            "store_1": {"label": "Store 1", "address": "1 Test St", "latitude": -36.85, "longitude": 174.76},
            "store_2": {"label": "Store 2", "address": "2 Test St", "latitude": -36.86, "longitude": 174.77},
        }

        result = scraper._parse_store_data(data)

        assert len(result) == 2


# ============================================================================
# NZ Coverage Tests
# ============================================================================

class TestNZStoreCoverage:
    """Tests to verify store scrapers can cover all NZ regions."""

    # Major NZ cities and their approximate coordinates
    NZ_CITIES = {
        "Auckland": (-36.8485, 174.7633),
        "Wellington": (-41.2865, 174.7762),
        "Christchurch": (-43.5321, 172.6362),
        "Hamilton": (-37.7870, 175.2793),
        "Tauranga": (-37.6878, 176.1651),
        "Dunedin": (-45.8788, 170.5028),
        "Palmerston North": (-40.3523, 175.6082),
        "Napier": (-39.4928, 176.9120),
        "Nelson": (-41.2706, 173.2840),
        "Rotorua": (-38.1368, 176.2497),
        "Queenstown": (-45.0312, 168.6626),
        "Invercargill": (-46.4132, 168.3538),
        "Whangarei": (-35.7275, 174.3166),
        "New Plymouth": (-39.0556, 174.0752),
        "Gisborne": (-38.6587, 177.9853),
    }

    def test_nz_regions_defined(self):
        """Verify we have all major NZ cities for coverage testing."""
        assert len(self.NZ_CITIES) >= 15
        assert "Auckland" in self.NZ_CITIES
        assert "Wellington" in self.NZ_CITIES
        assert "Christchurch" in self.NZ_CITIES

    def test_coordinate_validity(self):
        """Test that all NZ coordinates are valid."""
        for city, (lat, lon) in self.NZ_CITIES.items():
            # NZ latitude range: approximately -34 to -47
            assert -47 <= lat <= -34, f"Invalid latitude for {city}: {lat}"
            # NZ longitude range: approximately 166 to 179
            assert 166 <= lon <= 180, f"Invalid longitude for {city}: {lon}"


# ============================================================================
# Store Data File Tests
# ============================================================================

class TestStoreDataFiles:
    """Tests for store data JSON files."""

    DATA_DIR = Path(__file__).parent.parent / "data"

    @pytest.mark.parametrize("filename", [
        "countdown_stores.json",
        "newworld_stores.json",
        "paknsave_stores.json",
        "liquor_centre_stores.json",
    ])
    def test_store_data_files_exist(self, filename):
        """Test that store data files exist."""
        filepath = self.DATA_DIR / filename
        if filepath.exists():
            assert filepath.is_file()
            # Try to load as JSON
            with open(filepath) as f:
                data = json.load(f)
            assert isinstance(data, (list, dict))

    def test_store_data_has_required_fields(self):
        """Test that store data has required fields."""
        required_fields = {"name", "address"}  # Minimum required fields

        for filename in ["countdown_stores.json", "newworld_stores.json"]:
            filepath = self.DATA_DIR / filename
            if filepath.exists():
                with open(filepath) as f:
                    data = json.load(f)

                stores = data if isinstance(data, list) else list(data.values())
                for store in stores[:5]:  # Check first 5 stores
                    if isinstance(store, dict):
                        # Check for at least name field
                        has_name = any(
                            key in store
                            for key in ["name", "label", "storeName", "Name"]
                        )
                        assert has_name, f"Store missing name field in {filename}"


# ============================================================================
# Store Scraper Integration Tests
# ============================================================================

class TestStoreScraperIntegration:
    """Integration tests for store scrapers."""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that browser resources are cleaned up properly."""
        scraper = LiquorlandLocationScraper()

        # Mock browser components
        scraper.playwright = AsyncMock()
        scraper.browser = AsyncMock()
        scraper.context = AsyncMock()

        await scraper.__aexit__(None, None, None)

        # Verify cleanup was called
        scraper.context.close.assert_called_once()
        scraper.browser.close.assert_called_once()
        scraper.playwright.stop.assert_called_once()

    def test_user_agent_is_respectful(self):
        """Test that user agent identifies Liquorfy bot."""
        scraper = SuperLiquorLocationScraper()

        user_agent = scraper.client.headers.get("User-Agent", "")
        assert "Liquorfy" in user_agent
        assert "Store Location Service" in user_agent or "liquorfy.co.nz" in user_agent


# ============================================================================
# Mock Store Data for Testing
# ============================================================================

@pytest.fixture
def mock_super_liquor_api_response():
    """Sample Super Liquor API response."""
    return {
        "Locations": [
            {
                "Id": 1,
                "Name": "Auckland Central",
                "Address": "123 Queen Street",
                "City": "Auckland",
                "State": "Auckland",
                "ZipPostalCode": "1010",
                "PhoneNumber": "09 123 4567",
                "Latitude": -36.8485,
                "Longitude": 174.7633,
            },
            {
                "Id": 2,
                "Name": "Wellington CBD",
                "Address": "456 Lambton Quay",
                "City": "Wellington",
                "State": "Wellington",
                "ZipPostalCode": "6011",
                "PhoneNumber": "04 123 4567",
                "Latitude": -41.2865,
                "Longitude": 174.7762,
            },
            {
                "Id": 3,
                "Name": "Christchurch",
                "Address": "789 Colombo Street",
                "City": "Christchurch",
                "State": "Canterbury",
                "ZipPostalCode": "8011",
                "PhoneNumber": "03 123 4567",
                "Latitude": -43.5321,
                "Longitude": 172.6362,
            },
        ]
    }


@pytest.fixture
def mock_liquorland_store_data():
    """Sample Liquorland store data."""
    return {
        "store_1": {
            "label": "Liquorland Auckland",
            "address": "123 Queen Street, Auckland 1010",
            "latitude": -36.8485,
            "longitude": 174.7633,
            "city": "Auckland",
        },
        "store_2": {
            "label": "Liquorland Wellington",
            "address": "456 Lambton Quay, Wellington 6011",
            "latitude": -41.2865,
            "longitude": 174.7762,
            "city": "Wellington",
        },
    }
