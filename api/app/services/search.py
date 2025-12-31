from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Price, Product, Store
from app.schemas.products import PriceSchema, ProductDetailSchema, ProductListResponse, ProductSchema, StoreListResponse, StoreSchema
from app.schemas.queries import ProductQueryParams
from app.services.geospatial import haversine_distance, within_radius
from app.services.parser_utils import CATEGORY_HIERARCHY
from app.services.pricing import compute_pricing_metrics


async def fetch_products(
    session: AsyncSession,
    params: ProductQueryParams,
) -> ProductListResponse:
    query: Select[Any] = (
        select(Product, Price, Store)
        .join(Price, Price.product_id == Product.id)
        .join(Store, Store.id == Price.store_id)
    )

    # Filter stores by location first if params provided
    allowed_store_ids = None
    if params.lat is not None and params.lon is not None and params.radius_km is not None:
        # Get all stores
        stores_result = await session.execute(select(Store))
        all_stores = stores_result.scalars().all()

        # Filter by radius using existing geospatial utility
        store_distances = within_radius(
            stores=[(str(store.id), store.lat, store.lon) for store in all_stores],
            lat=params.lat,
            lon=params.lon,
            radius_km=params.radius_km,
        )

        # Extract store IDs within radius
        allowed_store_ids = [UUID(store_id) for store_id, _ in store_distances]

        # Early return if no stores in radius
        if not allowed_store_ids:
            return ProductListResponse(items=[], total=0, page=params.page, page_size=params.page_size)

    filters = []
    # Add location-based store filter
    if allowed_store_ids is not None:
        filters.append(Store.id.in_(allowed_store_ids))
    if params.q:
        pattern = f"%{params.q.lower()}%"
        filters.append(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.brand).like(pattern),
            )
        )
    if params.chain:
        filters.append(Product.chain.in_(params.chain))
    if params.store:
        filters.append(Store.id.in_([UUID(s) for s in params.store]))
    if params.category:
        # Expand categories to include subcategories
        # e.g., if filtering by "beer", also include "lager", "ipa", "ale", etc.
        expanded_categories = set(params.category)
        for requested_cat in params.category:
            # Add all subcategories that have this as parent
            for subcat, parent in CATEGORY_HIERARCHY.items():
                if parent == requested_cat:
                    expanded_categories.add(subcat)
        filters.append(Product.category.in_(list(expanded_categories)))
    if params.abv_min is not None:
        filters.append(Product.abv_percent >= params.abv_min)
    if params.abv_max is not None:
        filters.append(Product.abv_percent <= params.abv_max)
    if params.pack_min is not None:
        filters.append(Product.pack_count >= params.pack_min)
    if params.pack_max is not None:
        filters.append(Product.pack_count <= params.pack_max)
    if params.vol_min_ml is not None:
        filters.append(Product.total_volume_ml >= params.vol_min_ml)
    if params.vol_max_ml is not None:
        filters.append(Product.total_volume_ml <= params.vol_max_ml)
    if params.price_min is not None:
        filters.append(Price.price_nzd >= params.price_min)
    if params.price_max is not None:
        filters.append(Price.price_nzd <= params.price_max)
    if params.promo_only:
        # Only return products with actual discounts (promo price < regular price)
        filters.append(Price.promo_price_nzd.is_not(None))
        filters.append(Price.promo_price_nzd < Price.price_nzd)

    if filters:
        query = query.where(and_(*filters))

    effective_price = func.coalesce(Price.promo_price_nzd, Price.price_nzd)
    if params.sort == "price_per_standard_drink":
        query = query.order_by(effective_price / func.nullif(Product.abv_percent, 0))
    elif params.sort == "total_price":
        query = query.order_by(effective_price)
    elif params.sort == "newest":
        query = query.order_by(Price.price_last_changed_at.desc())
    else:
        # default price per 100ml
        query = query.order_by(effective_price / func.nullif(Product.total_volume_ml, 0))

    total_result = await session.execute(query.with_only_columns(func.count()).order_by(None))
    total = total_result.scalar_one()

    page = max(params.page, 1)
    page_size = max(min(params.page_size, 100), 1)
    query = query.limit(page_size).offset((page - 1) * page_size)

    result = await session.execute(query)
    rows = result.all()
    items: list[ProductSchema] = []

    for product, price, store in rows:
        effective = price.promo_price_nzd or price.price_nzd
        metrics = compute_pricing_metrics(
            total_volume_ml=product.total_volume_ml,
            abv_percent=product.abv_percent,
            effective_price_nzd=effective,
        )
        distance = None
        if params.lat is not None and params.lon is not None:
            distance = round(haversine_distance(params.lat, params.lon, store.lat, store.lon), 2)
        items.append(
            ProductSchema(
                id=product.id,
                name=product.name,
                brand=product.brand,
                category=product.category,
                chain=product.chain,
                abv_percent=product.abv_percent,
                total_volume_ml=product.total_volume_ml,
                pack_count=product.pack_count,
                unit_volume_ml=product.unit_volume_ml,
                image_url=product.image_url,
                product_url=product.product_url,
                price=PriceSchema(
                    store_id=store.id,
                    store_name=store.name,
                    chain=store.chain,
                    price_nzd=price.price_nzd,
                    promo_price_nzd=price.promo_price_nzd,
                    promo_text=price.promo_text,
                    promo_ends_at=price.promo_ends_at,
                    price_per_100ml=metrics.price_per_100ml,
                    standard_drinks=metrics.standard_drinks,
                    price_per_standard_drink=metrics.price_per_standard_drink,
                    is_member_only=price.is_member_only,
                    distance_km=distance,
                ),
                last_updated=price.last_seen_at,
            )
        )

    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


async def fetch_product_detail(session: AsyncSession, product_id: UUID) -> ProductDetailSchema:
    query = (
        select(Product, Price, Store)
        .join(Price, Price.product_id == Product.id)
        .join(Store, Store.id == Price.store_id)
        .where(Product.id == product_id)
    )
    result = await session.execute(query)
    row = result.first()
    if not row:
        raise ValueError("Product not found")
    product, price, store = row
    effective = price.promo_price_nzd or price.price_nzd
    metrics = compute_pricing_metrics(
        total_volume_ml=product.total_volume_ml,
        abv_percent=product.abv_percent,
        effective_price_nzd=effective,
    )
    return ProductDetailSchema(
        id=product.id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        chain=product.chain,
        abv_percent=product.abv_percent,
        total_volume_ml=product.total_volume_ml,
        pack_count=product.pack_count,
        unit_volume_ml=product.unit_volume_ml,
        image_url=product.image_url,
        product_url=product.product_url,
        price=PriceSchema(
            store_id=store.id,
            store_name=store.name,
            chain=store.chain,
            price_nzd=price.price_nzd,
            promo_price_nzd=price.promo_price_nzd,
            promo_text=price.promo_text,
            promo_ends_at=price.promo_ends_at,
            price_per_100ml=metrics.price_per_100ml,
            standard_drinks=metrics.standard_drinks,
            price_per_standard_drink=metrics.price_per_standard_drink,
            is_member_only=price.is_member_only,
            distance_km=None,
        ),
        last_updated=price.last_seen_at,
    )


async def fetch_stores_nearby(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> StoreListResponse:
    result = await session.execute(select(Store))
    stores = result.scalars().all()
    store_distances = within_radius(
        stores=[(str(store.id), store.lat, store.lon) for store in stores],
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )
    distance_lookup = {UUID(store_id): distance for store_id, distance in store_distances}
    items = [
        StoreSchema(
            id=store.id,
            name=store.name,
            chain=store.chain,
            lat=store.lat,
            lon=store.lon,
            address=store.address,
            region=store.region,
            distance_km=round(distance_lookup.get(store.id, 0.0), 2),
        )
        for store in stores
        if store.id in distance_lookup
    ]
    return StoreListResponse(items=items)


__all__ = ["fetch_products", "fetch_product_detail", "fetch_stores_nearby"]
