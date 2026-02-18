from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PriceSchema(BaseModel):
    store_id: UUID
    store_name: str
    chain: str
    price_nzd: float
    promo_price_nzd: Optional[float]
    promo_text: Optional[str]
    promo_ends_at: Optional[datetime]
    price_per_100ml: Optional[float]
    standard_drinks: Optional[float]
    price_per_standard_drink: Optional[float]
    is_member_only: bool
    is_stale: bool = False
    distance_km: Optional[float]


class ProductSchema(BaseModel):
    id: UUID
    name: str
    brand: Optional[str]
    category: Optional[str]
    chain: str
    abv_percent: Optional[float]
    total_volume_ml: Optional[float]
    pack_count: Optional[int]
    unit_volume_ml: Optional[float]
    image_url: Optional[str]
    product_url: Optional[str]
    price: PriceSchema
    last_updated: datetime


class ProductDetailSchema(ProductSchema):
    description: Optional[str] = Field(None, description="Placeholder for future enrichment")


class ProductListResponse(BaseModel):
    items: list[ProductSchema]
    total: int
    page: int
    page_size: int


class StoreSchema(BaseModel):
    id: UUID
    name: str
    chain: str
    lat: Optional[float]
    lon: Optional[float]
    address: Optional[str]
    region: Optional[str]
    distance_km: Optional[float]


class StoreListResponse(BaseModel):
    items: list[StoreSchema]


__all__ = [
    "PriceSchema",
    "ProductSchema",
    "ProductDetailSchema",
    "ProductListResponse",
    "StoreSchema",
    "StoreListResponse",
]
