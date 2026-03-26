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
    is_sugar_free: bool = False
    price: PriceSchema
    last_updated: datetime


class CrossChainPrice(BaseModel):
    product_id: UUID
    product_name: str
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    chain: str
    store_id: UUID
    store_name: str
    price_nzd: float
    promo_price_nzd: Optional[float] = None
    promo_text: Optional[str] = None
    promo_ends_at: Optional[datetime] = None
    price_per_100ml: Optional[float] = None
    price_per_standard_drink: Optional[float] = None
    is_member_only: bool = False
    is_stale: bool = False
    distance_km: Optional[float] = None


class ProductDetailSchema(ProductSchema):
    description: Optional[str] = Field(None, description="Placeholder for future enrichment")
    other_prices: list[PriceSchema] = Field(default_factory=list, description="Same product at other stores")
    cross_chain_prices: list[CrossChainPrice] = Field(
        default_factory=list, description="Same product at other chains"
    )


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
    "CrossChainPrice",
    "ProductDetailSchema",
    "ProductListResponse",
    "StoreSchema",
    "StoreListResponse",
]
