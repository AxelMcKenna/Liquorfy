"""Tests for products API endpoints."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestListProductsEndpoint:
    """Tests for GET /products endpoint."""

    def test_products_requires_location_for_non_promo(self, client: TestClient):
        """Products endpoint should require location for non-promo queries."""
        response = client.get("/products")
        assert response.status_code == 400
        assert "Location parameters" in response.json()["detail"]

    def test_products_promo_only_no_location_ok(self, client: TestClient):
        """Small promo-only queries should work without location."""
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }

        with patch("app.routes.products.fetch_products", AsyncMock(return_value=type(
            "MockResponse", (), {"json": lambda self: '{"items":[],"total":0,"page":1,"page_size":20}'}
        )())):
            with patch("app.routes.products.cached_json", AsyncMock(return_value=mock_response)):
                response = client.get("/products?promo_only=true&page_size=10")

        # Should succeed (not require location)
        assert response.status_code == 200

    def test_products_validates_nz_location(self, client: TestClient):
        """Products should reject locations outside New Zealand."""
        # Sydney, Australia - outside NZ bounds
        response = client.get("/products?lat=-33.8688&lon=151.2093&radius_km=10")
        assert response.status_code == 400
        assert "New Zealand" in response.json()["detail"]

    def test_products_validates_max_radius(self, client: TestClient):
        """Products should reject radius > 10km."""
        # Auckland location with excessive radius
        response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=11")
        # Should be rejected by either pydantic validation (422) or route validation (400)
        assert response.status_code in [400, 422]

    def test_products_valid_nz_location(self, client: TestClient):
        """Products should accept valid NZ location."""
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }

        with patch("app.routes.products.cached_json", AsyncMock(return_value=mock_response)):
            # Auckland CBD - valid NZ location
            response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=10")

        assert response.status_code == 200

    def test_products_query_params(self, client: TestClient):
        """Products endpoint should accept various query parameters."""
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10
        }

        with patch("app.routes.products.cached_json", AsyncMock(return_value=mock_response)):
            response = client.get(
                "/products"
                "?lat=-36.8485&lon=174.7633&radius_km=10"
                "&q=beer"
                "&chain=countdown,paknsave"
                "&category=beer"
                "&abv_min=4&abv_max=8"
                "&price_min=10&price_max=50"
                "&promo_only=true"
                "&sort=price_nzd"
                "&page=1&page_size=10"
            )

        assert response.status_code == 200

    def test_products_supports_repeated_chain_params(self, client: TestClient):
        """Products should parse repeated chain params like chain=a&chain=b."""
        mock_response = {"items": [], "total": 0, "page": 1, "page_size": 20}

        async def check_cache_key(cache_key: str, *_args):
            parsed = json.loads(cache_key)
            assert parsed["chain"] == ["countdown", "paknsave"]
            return mock_response

        with patch("app.routes.products.cached_json", AsyncMock(side_effect=check_cache_key)):
            response = client.get(
                "/products"
                "?lat=-36.8485&lon=174.7633&radius_km=5"
                "&chain=countdown&chain=paknsave"
            )

        assert response.status_code == 200

    def test_products_distance_sort_requires_location(self, client: TestClient):
        """Distance sort should return 422 when location is missing."""
        response = client.get("/products?promo_only=true&sort=distance&page_size=10")
        assert response.status_code == 422

    def test_products_invalid_store_uuid_rejected(self, client: TestClient):
        """Invalid store IDs should fail validation."""
        response = client.get(
            "/products?lat=-36.8485&lon=174.7633&radius_km=5&store=not-a-uuid"
        )
        assert response.status_code == 422

    def test_products_response_structure(self, client: TestClient):
        """Products response should have correct structure."""
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }

        with patch("app.routes.products.cached_json", AsyncMock(return_value=mock_response)):
            response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=10")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    def test_products_edge_of_nz_bounds(self, client: TestClient):
        """Products should accept locations at edge of NZ bounds."""
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }

        with patch("app.routes.products.cached_json", AsyncMock(return_value=mock_response)):
            # Bluff - southernmost town
            response = client.get("/products?lat=-46.6&lon=168.3&radius_km=10")

        assert response.status_code == 200


class TestProductDetailEndpoint:
    """Tests for GET /products/{product_id} endpoint."""

    def test_product_detail_not_found(self, client: TestClient):
        """Product detail should return 404 for non-existent product."""
        import uuid

        with patch("app.routes.products.fetch_product_detail",
                   AsyncMock(side_effect=ValueError("Product not found"))):
            response = client.get(f"/products/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_product_detail_invalid_uuid(self, client: TestClient):
        """Product detail should return 422 for invalid UUID."""
        response = client.get("/products/not-a-uuid")
        assert response.status_code == 422

    def test_product_detail_success(self, client: TestClient):
        """Product detail should return product data."""
        import uuid
        from datetime import datetime
        from app.schemas.products import ProductDetailSchema, PriceSchema

        product_id = uuid.uuid4()
        store_id = uuid.uuid4()

        # Use actual Pydantic schema
        mock_price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="test",
            price_nzd=9.99,
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
            price_per_100ml=3.03,
            standard_drinks=1.3,
            price_per_standard_drink=7.68,
            is_member_only=False,
            distance_km=None,
        )

        mock_product = ProductDetailSchema(
            id=product_id,
            name="Test Beer",
            brand="Test Brand",
            category="beer",
            chain="test",
            abv_percent=5.0,
            total_volume_ml=330.0,
            pack_count=1,
            unit_volume_ml=330.0,
            image_url=None,
            product_url=None,
            description=None,
            price=mock_price,
            last_updated=datetime.utcnow(),
        )

        with patch("app.routes.products.fetch_product_detail", AsyncMock(return_value=mock_product)):
            response = client.get(f"/products/{product_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Beer"
        assert data["brand"] == "Test Brand"


class TestProductsLocationValidation:
    """Tests for location validation edge cases."""

    def test_lat_out_of_range_north(self, client: TestClient):
        """Latitude north of NZ should be rejected."""
        response = client.get("/products?lat=-30.0&lon=174.7633&radius_km=10")
        assert response.status_code == 400

    def test_lat_out_of_range_south(self, client: TestClient):
        """Latitude south of NZ should be rejected."""
        response = client.get("/products?lat=-50.0&lon=174.7633&radius_km=10")
        assert response.status_code == 400

    def test_lon_out_of_range_west(self, client: TestClient):
        """Longitude west of NZ should be rejected."""
        response = client.get("/products?lat=-36.8485&lon=160.0&radius_km=10")
        assert response.status_code == 400

    def test_lon_out_of_range_east(self, client: TestClient):
        """Longitude east of NZ should be rejected."""
        response = client.get("/products?lat=-36.8485&lon=180.0&radius_km=10")
        assert response.status_code == 400

    def test_zero_radius_rejected(self, client: TestClient):
        """Zero radius should be rejected by validation."""
        response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=0")
        # Should be rejected (400 or 422)
        assert response.status_code in [400, 422]

    def test_negative_radius_rejected(self, client: TestClient):
        """Negative radius should be rejected."""
        response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=-10")
        assert response.status_code in [400, 422]

    def test_radius_below_minimum(self, client: TestClient):
        """Radius below 1km should be rejected."""
        response = client.get("/products?lat=-36.8485&lon=174.7633&radius_km=0.5")
        assert response.status_code in [400, 422]
