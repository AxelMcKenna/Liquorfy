from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import get_settings
from app.db.session import get_async_session
from app.schemas.products import ProductDetailSchema, ProductListResponse
from app.schemas.queries import ProductQueryParams
from app.services.cache import cached_json
from app.services.search import fetch_product_detail, fetch_products

router = APIRouter(prefix="/products", tags=["products"])
settings = get_settings()


async def _params(
    q: Optional[str] = Query(None),
    chain: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    abv_min: Optional[float] = Query(None),
    abv_max: Optional[float] = Query(None),
    pack_min: Optional[int] = Query(None),
    pack_max: Optional[int] = Query(None),
    vol_min_ml: Optional[float] = Query(None),
    vol_max_ml: Optional[float] = Query(None),
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    promo_only: bool = Query(False),
    sort: str = Query("price_per_100ml"),
    page: int = Query(1),
    page_size: int = Query(20),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None),
) -> ProductQueryParams:
    return ProductQueryParams(
        q=q,
        chain=chain.split(",") if chain else [],
        store=store.split(",") if store else [],
        category=category.split(",") if category else [],
        abv_min=abv_min,
        abv_max=abv_max,
        pack_min=pack_min,
        pack_max=pack_max,
        vol_min_ml=vol_min_ml,
        vol_max_ml=vol_max_ml,
        price_min=price_min,
        price_max=price_max,
        promo_only=promo_only,
        sort=sort,
        page=page,
        page_size=page_size,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )


@router.get("", response_model=ProductListResponse)
async def list_products(params: ProductQueryParams = Depends(_params)) -> ProductListResponse:
    async with get_async_session() as session:
        cache_key = json.dumps(params.dict(), sort_keys=True)

        async def producer() -> dict:
            response = await fetch_products(session, params)
            return json.loads(response.json())

        payload = await cached_json(cache_key, settings.api_cache_ttl_seconds, producer)
        return ProductListResponse.parse_obj(payload)


@router.get("/{product_id}", response_model=ProductDetailSchema)
async def product_detail(product_id: UUID) -> ProductDetailSchema:
    async with get_async_session() as session:
        try:
            product = await fetch_product_detail(session, product_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return product
