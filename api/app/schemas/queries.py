from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProductQueryParams(BaseModel):
    q: Optional[str] = None
    chain: list[str] = Field(default_factory=list)
    store: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)
    abv_min: Optional[float] = None
    abv_max: Optional[float] = None
    pack_min: Optional[int] = None
    pack_max: Optional[int] = None
    vol_min_ml: Optional[float] = None
    vol_max_ml: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    promo_only: bool = False
    sort: str = "price_per_100ml"
    page: int = 1
    page_size: int = 20
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = None


__all__ = ["ProductQueryParams"]
