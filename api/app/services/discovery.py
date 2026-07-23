"""Store proximity and product discovery queries."""
from __future__ import annotations

from geoalchemy2 import Geography
from sqlalchemy import Float, cast, func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, ProductView, Store
from app.schemas.products import StoreListResponse, StoreSchema
from app.services.parser_utils import format_product_name
from app.services.search_support import get_store_ids_within_radius


async def fetch_stores_nearby(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> StoreListResponse:
    user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    user_point_geog = cast(user_point, Geography)
    store_ids = await get_store_ids_within_radius(
        session,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )
    if not store_ids:
        return StoreListResponse(items=[])

    distance_m = func.ST_Distance(Store.geog, user_point_geog).label("distance_m")
    query = (
        select(Store, distance_m)
        .where(Store.id.in_(store_ids), Store.sells_alcohol.is_(True))
        .order_by(distance_m)
    )
    return StoreListResponse(
        items=[
            StoreSchema(
                id=store.id,
                name=store.name,
                chain=store.chain,
                lat=store.lat,
                lon=store.lon,
                address=store.address,
                region=store.region,
                distance_km=round(distance / 1000, 2),
                sells_alcohol=store.sells_alcohol,
                licensing_trust_area=store.licensing_trust_area,
            )
            for store, distance in (await session.execute(query)).all()
        ]
    )


async def fetch_autocomplete(
    session: AsyncSession,
    q: str,
    limit: int = 8,
) -> list[dict]:
    """Return deduplicated text matches with a bounded popularity boost."""
    normalized_query = q.lower().strip()
    if len(normalized_query) < 2:
        return []

    trigram_threshold = 0.15
    popularity_weight = 0.05
    name_similarity = func.similarity(
        func.lower(Product.name), normalized_query
    )
    brand_similarity = func.coalesce(
        func.similarity(func.lower(Product.brand), normalized_query),
        literal(0),
    )
    text_similarity = func.greatest(name_similarity, brand_similarity)
    popularity_boost = (
        func.coalesce(
            func.log(cast(ProductView.view_count + 1, Float)),
            literal(0),
        )
        * popularity_weight
    )
    score = (text_similarity + popularity_boost).label("score")
    pattern = f"%{normalized_query}%"
    like_match = or_(
        func.lower(Product.name).like(pattern),
        func.lower(Product.brand).like(pattern),
    )
    name_key = func.lower(func.trim(Product.name)).label("name_key")
    candidates = (
        select(
            Product.id,
            Product.name,
            Product.brand,
            Product.category,
            Product.image_url,
            Product.chain,
            score,
            func.row_number()
            .over(partition_by=name_key, order_by=score.desc())
            .label("row_number"),
        )
        .select_from(Product)
        .outerjoin(ProductView, ProductView.product_id == Product.id)
        .where(
            or_(
                name_similarity >= trigram_threshold,
                brand_similarity >= trigram_threshold,
                like_match,
            )
        )
        .subquery()
    )
    query = (
        select(
            candidates.c.id,
            candidates.c.name,
            candidates.c.brand,
            candidates.c.category,
            candidates.c.image_url,
            candidates.c.chain,
            candidates.c.score,
        )
        .where(candidates.c.row_number == 1)
        .order_by(candidates.c.score.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(row.id),
            "name": format_product_name(row.name, row.brand),
            "brand": row.brand,
            "category": row.category,
            "image_url": row.image_url,
            "chain": row.chain,
            "score": round(float(row.score), 3),
        }
        for row in (await session.execute(query)).all()
    ]


async def fetch_popular(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """Return the most-viewed products over the rolling seven-day window."""
    query = (
        select(
            Product.id,
            Product.name,
            Product.brand,
            Product.category,
            Product.image_url,
            Product.chain,
            ProductView.view_count,
        )
        .join(ProductView, ProductView.product_id == Product.id)
        .where(
            ProductView.last_viewed_at
            >= func.now() - text("interval '7 days'"),
        )
        .order_by(ProductView.view_count.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(row.id),
            "name": format_product_name(row.name, row.brand),
            "brand": row.brand,
            "category": row.category,
            "image_url": row.image_url,
            "chain": row.chain,
            "view_count": row.view_count,
        }
        for row in (await session.execute(query)).all()
    ]


__all__ = ["fetch_autocomplete", "fetch_popular", "fetch_stores_nearby"]
