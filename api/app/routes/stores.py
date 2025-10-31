from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.db.session import get_async_session
from app.schemas.products import StoreListResponse
from app.services.search import fetch_stores_nearby

router = APIRouter(prefix="/stores", tags=["stores"])
settings = get_settings()


@router.get("")
async def stores_nearby(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float | None = Query(None),
) -> StoreListResponse:
    async with get_async_session() as session:
        radius = radius_km or settings.default_radius_km
        if radius <= 0:
            raise HTTPException(status_code=400, detail="radius_km must be positive")
        return await fetch_stores_nearby(session, lat=lat, lon=lon, radius_km=radius)
