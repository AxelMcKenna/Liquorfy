"""User preference schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserPreferencesUpdate(BaseModel):
    """Request body for creating/updating user preferences."""

    default_lat: float | None = None
    default_lng: float | None = None
    default_radius_km: float = Field(2.0, ge=1.0, le=10.0)
    preferred_stores: list[str] = Field(default_factory=list)


class UserPreferencesResponse(BaseModel):
    """Response body for user preferences."""

    user_id: UUID
    default_lat: float | None
    default_lng: float | None
    default_radius_km: float
    preferred_stores: list[str]
    created_at: datetime
    updated_at: datetime


__all__ = ["UserPreferencesUpdate", "UserPreferencesResponse"]
