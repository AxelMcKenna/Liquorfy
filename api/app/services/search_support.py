"""Shared SQL expressions and proximity-cache helpers for product queries."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import and_, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Price, Product, Store
from app.services.cache import cached_json


def store_bucket_key(lat: float, lon: float, radius_km: float) -> str:
    return f"stores_nearby:{lat:.6f}:{lon:.6f}:{radius_km:.3f}"


def effective_price_expression() -> Any:
    valid_promo = case(
        (
            and_(
                Price.promo_price_nzd.is_not(None),
                or_(
                    Price.promo_ends_at.is_(None),
                    Price.promo_ends_at > func.now(),
                ),
            ),
            Price.promo_price_nzd,
        ),
        else_=None,
    )
    return func.coalesce(valid_promo, Price.price_nzd)


async def get_store_ids_within_radius(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> list[UUID]:
    cache_key = store_bucket_key(lat, lon, radius_km)

    async def producer() -> list[str]:
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        user_point_geog = cast(user_point, Geography)
        query = (
            select(Store.id)
            .where(Store.geog.is_not(None))
            .where(
                func.ST_DWithin(
                    Store.geog,
                    user_point_geog,
                    radius_km * 1000,
                )
            )
        )
        result = await session.execute(query)
        return [str(store_id) for store_id in result.scalars().all()]

    cached_ids = await cached_json(
        cache_key,
        get_settings().api_cache_ttl_seconds,
        producer,
    )
    return [UUID(store_id) for store_id in cached_ids]


def build_sort_order(
    *,
    sort: str,
    discount_ratio: Any,
    price_per_100ml: Any,
    price_per_standard_drink: Any,
    effective_price: Any,
    distance_m: Any | None,
    text_similarity: Any | None = None,
) -> list[Any]:
    tie_breakers = [
        Price.price_last_changed_at.desc(),
        Product.name.asc(),
        Price.id.asc(),
    ]
    if sort == "relevance" and text_similarity is not None:
        return [text_similarity.desc().nulls_last(), *tie_breakers]
    if sort == "discount":
        return [discount_ratio.desc().nulls_last(), *tie_breakers]
    if sort == "price_per_standard_drink":
        return [price_per_standard_drink.asc().nulls_last(), *tie_breakers]
    if sort == "total_price":
        return [effective_price.asc().nulls_last(), *tie_breakers]
    if sort == "newest":
        return [
            Price.price_last_changed_at.desc(),
            Product.name.asc(),
            Price.id.asc(),
        ]
    if sort == "distance" and distance_m is not None:
        return [distance_m.asc().nulls_last(), *tie_breakers]
    return [price_per_100ml.asc().nulls_last(), *tie_breakers]


__all__ = [
    "build_sort_order",
    "effective_price_expression",
    "get_store_ids_within_radius",
    "store_bucket_key",
]
