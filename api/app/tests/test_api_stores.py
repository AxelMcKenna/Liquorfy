"""Tests for stores API endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestStoresNearbyEndpoint:
    """Tests for GET /stores endpoint."""

    def test_stores_requires_lat_lon(self, client: TestClient):
        """Stores endpoint should require lat and lon parameters."""
        response = client.get("/stores")
        assert response.status_code == 422  # Missing required params

    def test_stores_missing_lat(self, client: TestClient):
        """Stores endpoint should require lat parameter."""
        response = client.get("/stores?lon=174.7633")
        assert response.status_code == 422

    def test_stores_missing_lon(self, client: TestClient):
        """Stores endpoint should require lon parameter."""
        response = client.get("/stores?lat=-36.8485")
        assert response.status_code == 422

    def test_stores_valid_location(self, client: TestClient):
        """Stores endpoint should accept valid location."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            response = client.get("/stores?lat=-36.8485&lon=174.7633")

        assert response.status_code == 200

    def test_stores_with_radius(self, client: TestClient):
        """Stores endpoint should accept radius parameter."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=5")

        assert response.status_code == 200

    def test_stores_uses_default_radius(self, client: TestClient):
        """Stores endpoint should use default radius if not specified."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])
        mock_fetch = AsyncMock(return_value=mock_response)

        with patch("app.routes.stores.fetch_stores_nearby", mock_fetch):
            client.get("/stores?lat=-36.8485&lon=174.7633")

        # Should use default (2km from settings)
        call_kwargs = mock_fetch.call_args.kwargs
        assert call_kwargs["radius_km"] == 2.0

    def test_stores_radius_max_exceeded(self, client: TestClient):
        """Stores endpoint should reject radius > 10km."""
        response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=11")
        assert response.status_code == 400
        assert "10km" in response.json()["detail"]

    def test_stores_radius_zero_rejected(self, client: TestClient):
        """Stores endpoint should reject radius <= 0."""
        response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=0")
        assert response.status_code == 400

    def test_stores_radius_negative_rejected(self, client: TestClient):
        """Stores endpoint should reject negative radius."""
        response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=-5")
        assert response.status_code == 400
        assert "positive" in response.json()["detail"]

    def test_stores_response_structure(self, client: TestClient):
        """Stores response should have correct structure."""
        import uuid
        from app.schemas.products import StoreListResponse, StoreSchema

        mock_store = StoreSchema(
            id=uuid.uuid4(),
            name="Test Store",
            chain="countdown",
            lat=-36.8485,
            lon=174.7633,
            address="123 Queen St",
            region="Auckland",
            distance_km=1.5,
        )
        mock_response = StoreListResponse(items=[mock_store])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            response = client.get("/stores?lat=-36.8485&lon=174.7633")

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


class TestStoresEdgeCases:
    """Edge case tests for stores endpoint."""

    def test_stores_invalid_lat_type(self, client: TestClient):
        """Stores endpoint should reject non-numeric lat."""
        response = client.get("/stores?lat=abc&lon=174.7633")
        assert response.status_code == 422

    def test_stores_invalid_lon_type(self, client: TestClient):
        """Stores endpoint should reject non-numeric lon."""
        response = client.get("/stores?lat=-36.8485&lon=xyz")
        assert response.status_code == 422

    def test_stores_extreme_lat(self, client: TestClient):
        """Stores should handle extreme but valid lat values."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            # Stewart Island - southern NZ
            response = client.get("/stores?lat=-46.9&lon=168.0")

        assert response.status_code == 200

    def test_stores_float_radius(self, client: TestClient):
        """Stores endpoint should accept float radius."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=7.5")

        assert response.status_code == 200

    def test_stores_radius_at_max(self, client: TestClient):
        """Stores endpoint should accept radius at max (10km)."""
        from app.schemas.products import StoreListResponse

        mock_response = StoreListResponse(items=[])

        with patch("app.routes.stores.fetch_stores_nearby", AsyncMock(return_value=mock_response)):
            response = client.get("/stores?lat=-36.8485&lon=174.7633&radius_km=10")

        assert response.status_code == 200
