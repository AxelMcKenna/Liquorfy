"""Price alert schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CreateAlertRequest(BaseModel):
    """Request body for creating a price alert."""

    product_id: UUID
    threshold_price: float | None = Field(None, gt=0)
    alert_on_promo: bool = False

    @validator("threshold_price", "alert_on_promo")
    def require_at_least_one_condition(cls, v, values):
        # Only validate once both fields are available
        if "threshold_price" in values and "alert_on_promo" in values:
            if values["threshold_price"] is None and not values["alert_on_promo"]:
                raise ValueError(
                    "Must set either threshold_price or alert_on_promo (or both)"
                )
        return v


class UpdateAlertRequest(BaseModel):
    """Request body for updating a price alert."""

    threshold_price: float | None = None
    alert_on_promo: bool | None = None
    active: bool | None = None


class AlertResponse(BaseModel):
    """Response body for a price alert."""

    id: UUID
    product_id: UUID
    product_name: str | None = None
    threshold_price: float | None
    alert_on_promo: bool
    last_triggered_at: datetime | None
    active: bool
    created_at: datetime


class AlertListResponse(BaseModel):
    """Response body for listing alerts."""

    items: list[AlertResponse]


__all__ = [
    "CreateAlertRequest",
    "UpdateAlertRequest",
    "AlertResponse",
    "AlertListResponse",
]
