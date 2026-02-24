from __future__ import annotations

from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, validator

VALID_SORTS = {
    "discount",
    "price_per_100ml",
    "price_per_standard_drink",
    "total_price",
    "price_nzd",
    "newest",
    "distance",
}


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
    sugar_free: Optional[bool] = None
    promo_only: bool = False
    unique_products: bool = False
    sort: str = "price_per_100ml"
    page: int = 1
    page_size: int = 20
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = Field(default=None, ge=1, le=10)

    @validator("sort", pre=True)
    @classmethod
    def normalize_sort(cls, value: str) -> str:
        if value == "price_nzd":
            return "total_price"
        if value not in VALID_SORTS:
            raise ValueError(f"sort must be one of: {', '.join(sorted(VALID_SORTS))}")
        return value

    @validator("store", each_item=True)
    @classmethod
    def validate_store_uuid(cls, value: str) -> str:
        try:
            UUID(value)
        except ValueError as exc:
            raise ValueError("store must contain valid UUID values") from exc
        return value

    @validator('radius_km')
    @classmethod
    def validate_location_params(cls, v: Optional[float], values) -> Optional[float]:
        """Ensure lat and lon are provided when radius_km is set"""
        if v is not None:
            lat = values.get('lat')
            lon = values.get('lon')
            if lat is None or lon is None:
                raise ValueError('lat and lon must be provided when radius_km is set')
        return v

    @validator("sort")
    @classmethod
    def validate_distance_sort_requires_location(cls, value: str, values) -> str:
        if value == "distance":
            lat = values.get("lat")
            lon = values.get("lon")
            radius_km = values.get("radius_km")
            if lat is None or lon is None or radius_km is None:
                raise ValueError("lat, lon, and radius_km are required when sort=distance")
        return value


__all__ = ["ProductQueryParams"]
