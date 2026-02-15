from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator


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
    unique_products: bool = False
    sort: str = "price_per_100ml"
    page: int = 1
    page_size: int = 20
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = Field(None, ge=1, le=10)

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


__all__ = ["ProductQueryParams"]
