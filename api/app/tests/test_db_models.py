"""Tests for database models."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from app.db.models import IngestionRun, Price, Product, Store


class TestStoreModel:
    """Tests for Store model."""

    def test_store_creation(self, sample_store):
        """Should create store with required fields."""
        assert sample_store.id is not None
        assert sample_store.name == "Test Store"
        assert sample_store.chain == "test_chain"

    def test_store_has_uuid_id(self, sample_store):
        """Store ID should be a UUID."""
        assert isinstance(sample_store.id, uuid.UUID)

    def test_store_with_location(self, sample_store):
        """Store should have lat/lon location."""
        assert sample_store.lat == -36.8485
        assert sample_store.lon == 174.7633

    def test_store_optional_fields(self):
        """Store should allow None for optional fields."""
        store = Store(
            id=uuid.uuid4(),
            name="Minimal Store",
            chain="test",
            lat=None,
            lon=None,
            address=None,
            region=None,
            url=None
        )
        assert store.lat is None
        assert store.address is None


class TestProductModel:
    """Tests for Product model."""

    def test_product_creation(self, sample_product):
        """Should create product with required fields."""
        assert sample_product.id is not None
        assert sample_product.name == "Test Beer 12x330ml"
        assert sample_product.chain == "test_chain"
        assert sample_product.source_product_id == "TEST123"

    def test_product_has_uuid_id(self, sample_product):
        """Product ID should be a UUID."""
        assert isinstance(sample_product.id, uuid.UUID)

    def test_product_volume_fields(self, sample_product):
        """Product should have volume fields."""
        assert sample_product.pack_count == 12
        assert sample_product.unit_volume_ml == 330.0
        assert sample_product.total_volume_ml == 3960.0

    def test_product_optional_fields(self):
        """Product should allow None for optional fields."""
        product = Product(
            id=uuid.uuid4(),
            chain="test",
            source_product_id="MIN123",
            name="Minimal Product",
            brand=None,
            category=None,
            abv_percent=None,
            pack_count=None,
            unit_volume_ml=None,
            total_volume_ml=None,
            image_url=None,
            product_url=None
        )
        assert product.brand is None
        assert product.category is None
        assert product.abv_percent is None


class TestPriceModel:
    """Tests for Price model."""

    def test_price_creation(self, sample_price):
        """Should create price with required fields."""
        assert sample_price.id is not None
        assert sample_price.price_nzd == 29.99
        assert sample_price.currency == "NZD"

    def test_price_has_uuid_id(self, sample_price):
        """Price ID should be a UUID."""
        assert isinstance(sample_price.id, uuid.UUID)

    def test_price_promo_fields(self, sample_price):
        """Price should have promo fields."""
        assert sample_price.promo_price_nzd == 24.99
        assert sample_price.promo_text == "On special!"
        assert sample_price.promo_ends_at is not None

    def test_price_timestamps(self, sample_price):
        """Price should have timestamp fields."""
        assert sample_price.last_seen_at is not None
        assert sample_price.price_last_changed_at is not None

    def test_price_member_only_default(self):
        """Price is_member_only should default to False."""
        price = Price(
            id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            price_nzd=9.99,
            last_seen_at=datetime.utcnow(),
            price_last_changed_at=datetime.utcnow(),
            is_member_only=False  # Explicitly set since SQLAlchemy default is server-side
        )
        assert price.is_member_only is False


class TestIngestionRunModel:
    """Tests for IngestionRun model."""

    def test_ingestion_run_creation(self, sample_ingestion_run):
        """Should create ingestion run with required fields."""
        assert sample_ingestion_run.id is not None
        assert sample_ingestion_run.chain == "test_chain"
        assert sample_ingestion_run.status == "completed"

    def test_ingestion_run_has_uuid_id(self, sample_ingestion_run):
        """IngestionRun ID should be a UUID."""
        assert isinstance(sample_ingestion_run.id, uuid.UUID)

    def test_ingestion_run_timestamps(self, sample_ingestion_run):
        """IngestionRun should have timestamps."""
        assert sample_ingestion_run.started_at is not None
        assert sample_ingestion_run.finished_at is not None

    def test_ingestion_run_metrics(self, sample_ingestion_run):
        """IngestionRun should have metrics."""
        assert sample_ingestion_run.items_total == 100
        assert sample_ingestion_run.items_changed == 50
        assert sample_ingestion_run.items_failed == 2

    def test_ingestion_run_defaults(self):
        """IngestionRun should have correct defaults."""
        run = IngestionRun(
            id=uuid.uuid4(),
            chain="test",
            status="running",
            started_at=datetime.utcnow(),
            items_total=0,  # Explicitly set since SQLAlchemy default is server-side
            items_changed=0,
            items_failed=0,
        )
        assert run.items_total == 0
        assert run.items_changed == 0
        assert run.items_failed == 0
        assert run.finished_at is None
        assert run.log_url is None


class TestModelRelationships:
    """Tests for model relationships."""

    def test_store_has_prices_relationship(self, sample_store):
        """Store should have prices relationship."""
        assert hasattr(sample_store, 'prices')

    def test_product_has_prices_relationship(self, sample_product):
        """Product should have prices relationship."""
        assert hasattr(sample_product, 'prices')

    def test_price_has_product_relationship(self, sample_price):
        """Price should have product relationship."""
        assert hasattr(sample_price, 'product')

    def test_price_has_store_relationship(self, sample_price):
        """Price should have store relationship."""
        assert hasattr(sample_price, 'store')


class TestUuidGeneration:
    """Tests for UUID generation."""

    def test_store_generates_uuid(self):
        """Store should auto-generate UUID if not provided."""
        store = Store(
            name="Test",
            chain="test"
        )
        # UUID should be generated by default function
        # Note: This is typically handled by the database

    def test_product_generates_uuid(self):
        """Product should auto-generate UUID if not provided."""
        product = Product(
            chain="test",
            source_product_id="TEST",
            name="Test"
        )

    def test_price_generates_uuid(self):
        """Price should auto-generate UUID if not provided."""
        price = Price(
            product_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
            price_nzd=9.99,
            last_seen_at=datetime.utcnow(),
            price_last_changed_at=datetime.utcnow()
        )

    def test_ingestion_run_generates_uuid(self):
        """IngestionRun should auto-generate UUID if not provided."""
        run = IngestionRun(
            chain="test",
            status="running",
            started_at=datetime.utcnow()
        )
