"""Tests for Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.products import (
    PriceSchema,
    ProductDetailSchema,
    ProductListResponse,
    ProductSchema,
    StoreListResponse,
    StoreSchema,
)
from app.schemas.queries import ProductQueryParams


class TestProductQueryParams:
    """Tests for ProductQueryParams schema."""

    def test_default_values(self):
        """Should have correct default values."""
        params = ProductQueryParams()
        assert params.q is None
        assert params.chain == []
        assert params.store == []
        assert params.category == []
        assert params.promo_only is False
        assert params.unique_products is False
        assert params.sort == "price_per_100ml"
        assert params.page == 1
        assert params.page_size == 20

    def test_radius_requires_lat_lon(self):
        """Should validate that lat/lon required when radius_km set."""
        with pytest.raises(ValidationError) as exc_info:
            ProductQueryParams(radius_km=10)

        assert "lat and lon must be provided" in str(exc_info.value)

    def test_radius_with_lat_lon(self):
        """Should accept radius when lat/lon provided."""
        params = ProductQueryParams(lat=-36.8, lon=174.7, radius_km=10)
        assert params.radius_km == 10
        assert params.lat == -36.8
        assert params.lon == 174.7

    def test_radius_range_validation(self):
        """Should validate radius is within range (1-10)."""
        with pytest.raises(ValidationError):
            ProductQueryParams(lat=-36.8, lon=174.7, radius_km=0.5)

        with pytest.raises(ValidationError):
            ProductQueryParams(lat=-36.8, lon=174.7, radius_km=11)

    def test_valid_radius_at_bounds(self):
        """Should accept radius at bounds."""
        params = ProductQueryParams(lat=-36.8, lon=174.7, radius_km=1)
        assert params.radius_km == 1

        params = ProductQueryParams(lat=-36.8, lon=174.7, radius_km=10)
        assert params.radius_km == 10

    def test_accepts_filter_lists(self):
        """Should accept filter lists."""
        store_1 = str(uuid.uuid4())
        store_2 = str(uuid.uuid4())
        params = ProductQueryParams(
            chain=["countdown", "paknsave"],
            category=["beer", "wine"],
            store=[store_1, store_2]
        )
        assert len(params.chain) == 2
        assert len(params.category) == 2
        assert len(params.store) == 2

    def test_rejects_invalid_store_uuid(self):
        """Store filter values must be UUIDs."""
        with pytest.raises(ValidationError):
            ProductQueryParams(store=["not-a-uuid"])

    def test_sort_alias_price_nzd_maps_to_total_price(self):
        """Legacy sort alias should normalize to total_price."""
        params = ProductQueryParams(sort="price_nzd")
        assert params.sort == "total_price"

    def test_distance_sort_requires_location(self):
        """Distance sort requires full location context."""
        with pytest.raises(ValidationError):
            ProductQueryParams(sort="distance")


class TestPriceSchema:
    """Tests for PriceSchema."""

    def test_required_fields(self):
        """Should require essential fields."""
        store_id = uuid.uuid4()

        # Valid minimal price
        price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="countdown",
            price_nzd=9.99,
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
            price_per_100ml=None,
            standard_drinks=None,
            price_per_standard_drink=None,
            is_member_only=False,
            distance_km=None
        )
        assert price.price_nzd == 9.99

    def test_optional_fields_can_be_none(self):
        """Optional fields should accept None."""
        store_id = uuid.uuid4()
        price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="countdown",
            price_nzd=9.99,
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
            price_per_100ml=None,
            standard_drinks=None,
            price_per_standard_drink=None,
            is_member_only=False,
            distance_km=None
        )
        assert price.promo_price_nzd is None
        assert price.promo_text is None


class TestProductSchema:
    """Tests for ProductSchema."""

    def test_full_product(self):
        """Should accept full product data."""
        product_id = uuid.uuid4()
        store_id = uuid.uuid4()

        price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="countdown",
            price_nzd=29.99,
            promo_price_nzd=24.99,
            promo_text="On Sale!",
            promo_ends_at=datetime.utcnow(),
            price_per_100ml=3.03,
            standard_drinks=1.3,
            price_per_standard_drink=23.07,
            is_member_only=False,
            distance_km=1.5
        )

        product = ProductSchema(
            id=product_id,
            name="Test Beer 12x330ml",
            brand="Test Brand",
            category="beer",
            chain="countdown",
            abv_percent=5.0,
            total_volume_ml=3960.0,
            pack_count=12,
            unit_volume_ml=330.0,
            image_url="https://example.com/image.jpg",
            product_url="https://example.com/product",
            price=price,
            last_updated=datetime.utcnow()
        )

        assert product.name == "Test Beer 12x330ml"
        assert product.price.price_nzd == 29.99


class TestProductDetailSchema:
    """Tests for ProductDetailSchema."""

    def test_inherits_from_product_schema(self):
        """ProductDetailSchema should extend ProductSchema."""
        product_id = uuid.uuid4()
        store_id = uuid.uuid4()

        price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="countdown",
            price_nzd=29.99,
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
            price_per_100ml=None,
            standard_drinks=None,
            price_per_standard_drink=None,
            is_member_only=False,
            distance_km=None
        )

        detail = ProductDetailSchema(
            id=product_id,
            name="Test Product",
            brand=None,
            category=None,
            chain="countdown",
            abv_percent=None,
            total_volume_ml=None,
            pack_count=None,
            unit_volume_ml=None,
            image_url=None,
            product_url=None,
            price=price,
            last_updated=datetime.utcnow(),
            description="A detailed description"
        )

        assert detail.description == "A detailed description"

    def test_description_defaults_to_none(self):
        """Description should default to None."""
        product_id = uuid.uuid4()
        store_id = uuid.uuid4()

        price = PriceSchema(
            store_id=store_id,
            store_name="Test Store",
            chain="countdown",
            price_nzd=29.99,
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
            price_per_100ml=None,
            standard_drinks=None,
            price_per_standard_drink=None,
            is_member_only=False,
            distance_km=None
        )

        detail = ProductDetailSchema(
            id=product_id,
            name="Test Product",
            brand=None,
            category=None,
            chain="countdown",
            abv_percent=None,
            total_volume_ml=None,
            pack_count=None,
            unit_volume_ml=None,
            image_url=None,
            product_url=None,
            price=price,
            last_updated=datetime.utcnow()
        )

        assert detail.description is None


class TestProductListResponse:
    """Tests for ProductListResponse."""

    def test_empty_list(self):
        """Should accept empty items list."""
        response = ProductListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20
        )
        assert len(response.items) == 0
        assert response.total == 0

    def test_pagination_fields(self):
        """Should include pagination fields."""
        response = ProductListResponse(
            items=[],
            total=100,
            page=3,
            page_size=20
        )
        assert response.page == 3
        assert response.page_size == 20
        assert response.total == 100


class TestStoreSchema:
    """Tests for StoreSchema."""

    def test_store_with_location(self):
        """Should accept store with location."""
        store = StoreSchema(
            id=uuid.uuid4(),
            name="Test Store",
            chain="countdown",
            lat=-36.8485,
            lon=174.7633,
            address="123 Queen St",
            region="Auckland",
            distance_km=1.5
        )
        assert store.lat == -36.8485
        assert store.lon == 174.7633

    def test_store_without_location(self):
        """Should accept store without location."""
        store = StoreSchema(
            id=uuid.uuid4(),
            name="Test Store",
            chain="countdown",
            lat=None,
            lon=None,
            address=None,
            region=None,
            distance_km=None
        )
        assert store.lat is None
        assert store.lon is None


class TestStoreListResponse:
    """Tests for StoreListResponse."""

    def test_empty_list(self):
        """Should accept empty items list."""
        response = StoreListResponse(items=[])
        assert len(response.items) == 0

    def test_with_stores(self):
        """Should accept list of stores."""
        stores = [
            StoreSchema(
                id=uuid.uuid4(),
                name=f"Store {i}",
                chain="countdown",
                lat=-36.8 + i * 0.01,
                lon=174.7 + i * 0.01,
                address=None,
                region=None,
                distance_km=i * 0.5
            )
            for i in range(3)
        ]
        response = StoreListResponse(items=stores)
        assert len(response.items) == 3
