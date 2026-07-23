"""User preference schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, root_validator

from app.schemas.location import validate_nz_location


class UserPreferencesUpdate(BaseModel):
    """Request body for creating/updating user preferences."""

    default_lat: float | None = None
    default_lng: float | None = None
    default_radius_km: float = Field(2.0, ge=1.0, le=10.0)
    preferred_stores: list[UUID] = Field(default_factory=list, max_items=100)

    @root_validator
    def _validate_location_values(cls, values):
        lat = values.get("default_lat")
        lng = values.get("default_lng")
        if (lat is None) != (lng is None):
            raise ValueError("default_lat and default_lng must be provided together")
        if lat is not None:
            validate_nz_location(
                lat=lat,
                lon=lng,
                radius_km=values.get("default_radius_km"),
            )
        return values


class UserPreferencesResponse(BaseModel):
    """Response body for user preferences."""

    user_id: UUID
    default_lat: float | None
    default_lng: float | None
    default_radius_km: float
    preferred_stores: list[UUID]
    created_at: datetime
    updated_at: datetime


__all__ = ["UserPreferencesUpdate", "UserPreferencesResponse"]
