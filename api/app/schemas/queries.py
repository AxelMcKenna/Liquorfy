from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, root_validator, validator

from app.schemas.location import OptionalLocationParams

VALID_SORTS = {
    "discount",
    "price_per_100ml",
    "price_per_standard_drink",
    "total_price",
    "price_nzd",
    "newest",
    "distance",
    "relevance",
}


class ProductQueryParams(OptionalLocationParams):
    q: Optional[str] = Field(default=None, max_length=100)
    chain: list[str] = Field(default_factory=list, max_items=20)
    store: list[str] = Field(default_factory=list, max_items=100)
    category: list[str] = Field(default_factory=list, max_items=20)
    abv_min: Optional[float] = Field(default=None, ge=0, le=100)
    abv_max: Optional[float] = Field(default=None, ge=0, le=100)
    pack_min: Optional[int] = Field(default=None, ge=1)
    pack_max: Optional[int] = Field(default=None, ge=1)
    vol_min_ml: Optional[float] = Field(default=None, gt=0)
    vol_max_ml: Optional[float] = Field(default=None, gt=0)
    price_min: Optional[float] = Field(default=None, ge=0)
    price_max: Optional[float] = Field(default=None, ge=0)
    sugar_free: Optional[bool] = None
    promo_only: bool = False
    unique_products: bool = False
    sort: str = "price_per_100ml"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

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

    @root_validator
    def validate_ranges(cls, values):
        ranges = (
            ("abv_min", "abv_max"),
            ("pack_min", "pack_max"),
            ("vol_min_ml", "vol_max_ml"),
            ("price_min", "price_max"),
        )
        for lower_name, upper_name in ranges:
            lower = values.get(lower_name)
            upper = values.get(upper_name)
            if lower is not None and upper is not None and lower > upper:
                raise ValueError(f"{lower_name} cannot exceed {upper_name}")
        return values


__all__ = ["ProductQueryParams"]
