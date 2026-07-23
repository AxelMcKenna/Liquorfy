"""Shared location validation for every public API surface."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, root_validator

NZ_LAT_MIN = -47.0
NZ_LAT_MAX = -34.0
NZ_LON_MIN = 165.0
NZ_LON_MAX = 179.0
MIN_RADIUS_KM = 1.0
MAX_RADIUS_KM = 10.0


def validate_nz_location(
    *,
    lat: Optional[float],
    lon: Optional[float],
    radius_km: Optional[float],
    require: bool = False,
) -> None:
    """Validate an optional all-or-nothing New Zealand search location."""
    supplied = (lat is not None, lon is not None, radius_km is not None)
    if require and not all(supplied):
        raise ValueError("lat, lon, and radius_km are required")
    if any(supplied) and not all(supplied):
        raise ValueError("lat, lon, and radius_km must be provided together")
    if not all(supplied):
        return
    assert lat is not None
    assert lon is not None
    assert radius_km is not None
    if not (NZ_LAT_MIN <= lat <= NZ_LAT_MAX and NZ_LON_MIN <= lon <= NZ_LON_MAX):
        raise ValueError("Location must be within New Zealand")
    if not MIN_RADIUS_KM <= radius_km <= MAX_RADIUS_KM:
        raise ValueError(
            f"radius_km must be between {MIN_RADIUS_KM:g} and {MAX_RADIUS_KM:g}"
        )


class OptionalLocationParams(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = Field(
        default=None, ge=MIN_RADIUS_KM, le=MAX_RADIUS_KM
    )

    @root_validator
    def validate_location(cls, values):
        validate_nz_location(
            lat=values.get("lat"),
            lon=values.get("lon"),
            radius_km=values.get("radius_km"),
        )
        return values

    @property
    def has_location(self) -> bool:
        return self.lat is not None


__all__ = [
    "MAX_RADIUS_KM",
    "MIN_RADIUS_KM",
    "NZ_LAT_MAX",
    "NZ_LAT_MIN",
    "NZ_LON_MAX",
    "NZ_LON_MIN",
    "OptionalLocationParams",
    "validate_nz_location",
]
