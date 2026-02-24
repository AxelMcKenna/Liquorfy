from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Computed, DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from .base import Base

UUID_TYPE = UUID(as_uuid=True)


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
        Geography(geometry_type="POINT", srid=4326),
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

    prices: Mapped[list["Price"]] = relationship(back_populates="store")

    __table_args__ = (
        UniqueConstraint("chain", "name", name="uq_store_chain_name"),
        UniqueConstraint("chain", "api_id", name="uq_store_chain_api_id"),
        Index("ix_store_chain", "chain"),  # For chain filtering queries
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

    prices: Mapped[list["Price"]] = relationship(back_populates="product")

    __table_args__ = (
        UniqueConstraint("chain", "source_product_id", name="uq_product_source"),
        Index("ix_product_chain", "chain"),  # For chain filtering queries
    )


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NZD")
    price_nzd: Mapped[float] = mapped_column(Float, nullable=False)
    promo_price_nzd: Mapped[Optional[float]] = mapped_column(Float)
    promo_text: Mapped[Optional[str]] = mapped_column(String(255))
    promo_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_last_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_member_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(back_populates="prices")
    store: Mapped[Store] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_price_product_store"),
        Index("ix_price_price_nzd", "price_nzd"),
        Index("ix_price_promo_price_nzd", "promo_price_nzd"),
        Index("ix_price_last_changed", "price_last_changed_at"),
        Index("ix_price_product_id", "product_id"),  # FK index for JOINs
        Index("ix_price_store_id", "store_id"),  # FK index for JOINs
        Index("ix_price_last_seen", "last_seen_at"),  # For cleanup queries
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

    __table_args__ = (
        Index("ix_ingestion_run_chain_status", "chain", "status"),  # For status queries
        Index("ix_ingestion_run_chain_started", "chain", "started_at"),  # For recent run queries
    )


__all__ = ["Store", "Product", "Price", "IngestionRun"]
