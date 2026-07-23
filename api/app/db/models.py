from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

UUID_TYPE = UUID(as_uuid=True)
MONEY_TYPE = Numeric(10, 2, asdecimal=True)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    api_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Store ID from API (e.g., PAK'nSAVE, New World APIs)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geog: Mapped[Optional[object]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        Computed(
            "CASE WHEN lat IS NULL OR lon IS NULL THEN NULL "
            "ELSE ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography END",
            persisted=True,
        ),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(String(255))
    region: Mapped[Optional[str]] = mapped_column(String(64))
    url: Mapped[Optional[str]] = mapped_column(String(255))

    # West Auckland licensing trust monopoly (Sale and Supply of Alcohol Act 2012).
    # If False, the store is geographically inside a Trust district AND not a
    # Trust-operated brand, so it cannot legally sell alcohol.
    sells_alcohol: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    licensing_trust_area: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    prices: Mapped[list["Price"]] = relationship(back_populates="store")

    __table_args__ = (
        UniqueConstraint("chain", "name", name="uq_store_chain_name"),
        UniqueConstraint("chain", "api_id", name="uq_store_chain_api_id"),
        Index("ix_store_chain", "chain"),  # For chain filtering queries
        Index(
            "ix_store_sells_alcohol",
            "sells_alcohol",
            postgresql_where=text("sells_alcohol = false"),
        ),
        Index("ix_stores_geog", "geog", postgresql_using="gist"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    source_product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    abv_percent: Mapped[Optional[float]] = mapped_column(Float)
    pack_count: Mapped[Optional[int]] = mapped_column()
    unit_volume_ml: Mapped[Optional[float]] = mapped_column(Float)
    total_volume_ml: Mapped[Optional[float]] = mapped_column(Float)
    image_url: Mapped[Optional[str]] = mapped_column(String(512))
    product_url: Mapped[Optional[str]] = mapped_column(String(512))
    is_sugar_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="0")
    canonical_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID_TYPE, nullable=True)

    prices: Mapped[list["Price"]] = relationship(back_populates="product")

    __table_args__ = (
        UniqueConstraint("chain", "source_product_id", name="uq_product_source"),
        Index("ix_product_chain", "chain"),  # For chain filtering queries
        Index(
            "ix_product_canonical",
            "canonical_product_id",
            postgresql_where=text("canonical_product_id IS NOT NULL"),
        ),
        Index(
            "ix_products_name_trgm",
            func.lower(name).label("name_lower"),
            postgresql_using="gin",
            postgresql_ops={"name_lower": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_brand_trgm",
            func.lower(brand).label("brand_lower"),
            postgresql_using="gin",
            postgresql_ops={"brand_lower": "gin_trgm_ops"},
            postgresql_where=text("brand IS NOT NULL"),
        ),
    )


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), default="NZD", server_default="NZD", nullable=False
    )
    price_nzd: Mapped[Decimal] = mapped_column(MONEY_TYPE, nullable=False)
    promo_price_nzd: Mapped[Optional[Decimal]] = mapped_column(MONEY_TYPE)
    promo_text: Mapped[Optional[str]] = mapped_column(String(255))
    promo_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_last_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_member_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(back_populates="prices")
    store: Mapped[Store] = relationship(back_populates="prices")

    __table_args__ = (
        CheckConstraint("price_nzd > 0", name="ck_price_positive"),
        CheckConstraint(
            "promo_price_nzd IS NULL OR promo_price_nzd > 0",
            name="ck_promo_price_positive",
        ),
        UniqueConstraint("product_id", "store_id", name="uq_price_product_store"),
        Index("ix_price_price_nzd", "price_nzd"),
        Index("ix_price_promo_price_nzd", "promo_price_nzd"),
        Index("ix_price_last_changed", "price_last_changed_at"),
        Index("ix_price_product_id", "product_id"),  # FK index for JOINs
        Index("ix_price_store_id", "store_id"),  # FK index for JOINs
        Index("ix_price_last_seen", "last_seen_at"),  # For cleanup queries
        Index(
            "ix_price_promo_ends_at_partial",
            "promo_ends_at",
            postgresql_where=text("promo_ends_at IS NOT NULL"),
        ),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    # Append-only table - no need for created_at/updated_at from Base
    created_at = None  # type: ignore[assignment]
    updated_at = None  # type: ignore[assignment]

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    price_nzd: Mapped[Decimal] = mapped_column(MONEY_TYPE, nullable=False)
    promo_price_nzd: Mapped[Optional[Decimal]] = mapped_column(MONEY_TYPE)
    is_member_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("price_nzd > 0", name="ck_price_history_positive"),
        CheckConstraint(
            "promo_price_nzd IS NULL OR promo_price_nzd > 0",
            name="ck_price_history_promo_positive",
        ),
        Index("ix_price_history_product_recorded", "product_id", "recorded_at"),
        Index("ix_price_history_recorded_at", "recorded_at"),
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    items_total: Mapped[int] = mapped_column(default=0)
    items_changed: Mapped[int] = mapped_column(default=0)
    items_failed: Mapped[int] = mapped_column(default=0)
    log_url: Mapped[Optional[str]] = mapped_column(String(255))
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_ingestion_run_chain_status", "chain", "status"),  # For status queries
        Index("ix_ingestion_run_chain_started", "chain", "started_at"),  # For recent run queries
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, server_default=text("gen_random_uuid()")
    )
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="queued", server_default="queued"
    )
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(255))
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
    claimed_by: Mapped[Optional[str]] = mapped_column(String(255))
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_ingestion_job_status",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= max_attempts",
            name="ck_ingestion_job_attempt_count",
        ),
        CheckConstraint(
            "max_attempts BETWEEN 1 AND 10",
            name="ck_ingestion_job_max_attempts",
        ),
        Index(
            "ix_ingestion_job_ready",
            "available_at",
            "created_at",
            postgresql_where=text("status = 'queued'"),
        ),
        Index(
            "ix_ingestion_job_expired_lease",
            "lease_expires_at",
            postgresql_where=text("status = 'running'"),
        ),
        Index(
            "uq_ingestion_job_dedupe_key",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
        Index(
            "uq_ingestion_job_active_chain",
            "chain",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )


class ProductView(Base):
    __tablename__ = "product_views"

    # Override Base timestamps - we only need last_viewed_at
    created_at = None  # type: ignore[assignment]
    updated_at = None  # type: ignore[assignment]

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_product_views_count", "view_count"),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True)
    default_lat: Mapped[Optional[float]] = mapped_column(Float)
    default_lng: Mapped[Optional[float]] = mapped_column(Float)
    default_radius_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=2.0, server_default="2.0"
    )
    preferred_stores: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID_TYPE), nullable=False, default=list, server_default="{}"
    )

    __table_args__ = (
        CheckConstraint(
            "(default_lat IS NULL AND default_lng IS NULL) OR "
            "(default_lat IS NOT NULL AND default_lng IS NOT NULL "
            "AND default_lat BETWEEN -47 AND -34 "
            "AND default_lng BETWEEN 165 AND 179)",
            name="ck_user_preferences_location",
        ),
        CheckConstraint(
            "default_radius_km BETWEEN 1 AND 10",
            name="ck_user_preferences_radius",
        ),
    )


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    threshold_price: Mapped[Optional[Decimal]] = mapped_column(MONEY_TYPE)
    alert_on_promo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_notified_price: Mapped[Optional[Decimal]] = mapped_column(MONEY_TYPE)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    __table_args__ = (
        CheckConstraint(
            "threshold_price IS NOT NULL OR alert_on_promo",
            name="ck_price_alert_has_condition",
        ),
        CheckConstraint(
            "threshold_price IS NULL OR threshold_price > 0",
            name="ck_price_alert_threshold_positive",
        ),
        Index("ix_price_alert_user_active", "user_id", "active"),
        Index("ix_price_alert_product_active", "product_id", "active"),
    )


__all__ = [
    "Store",
    "Product",
    "Price",
    "PriceHistory",
    "IngestionRun",
    "IngestionJob",
    "ProductView",
    "UserPreference",
    "PriceAlert",
]
