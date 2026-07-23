from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.db.session import get_async_session
from app.schemas.location import validate_nz_location
from app.schemas.products import StoreListResponse
from app.services.search import fetch_stores_nearby

router = APIRouter(prefix="/stores", tags=["stores"])
settings = get_settings()


@router.get("", response_model=StoreListResponse)
async def stores_nearby(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float | None = Query(None),
) -> StoreListResponse:
    async with get_async_session() as session:
        radius = radius_km if radius_km is not None else settings.default_radius_km
        try:
            validate_nz_location(
                lat=lat,
                lon=lon,
                radius_km=radius,
                require=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return await fetch_stores_nearby(session, lat=lat, lon=lon, radius_km=radius)
