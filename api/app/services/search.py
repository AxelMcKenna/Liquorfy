from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import and_, cast, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Price, Product, Store
from app.schemas.products import (
    ProductListResponse,
    ProductSchema,
)
from app.schemas.queries import ProductQueryParams
from app.services.discovery import (
    fetch_autocomplete,
    fetch_popular,
    fetch_stores_nearby,
)
from app.services.parser_utils import CATEGORY_HIERARCHY
from app.services.pricing import STANDARD_DRINK_FACTOR
from app.services.product_detail import fetch_product_detail
from app.services.product_presenter import (
    MAX_PROMO_DISPLAY_DISCOUNT,
    build_product_schema,
)
from app.services.search_support import (
    build_sort_order,
    effective_price_expression,
    get_store_ids_within_radius,
)


async def fetch_products(
    session: AsyncSession,
    params: ProductQueryParams,
) -> ProductListResponse:
    page = params.page
    page_size = params.page_size

    # Every product in this DB is an alcoholic beverage, so any store with
    # sells_alcohol=False must be excluded unconditionally - those stores cannot
    # legally sell alcohol under the West Auckland Trust monopoly.
    filters: list[Any] = [Store.sells_alcohol.is_(True)]
    user_point_geog = None
    has_location = (
        params.lat is not None and params.lon is not None and params.radius_km is not None
    )
    if has_location:
        assert params.lat is not None
        assert params.lon is not None
        assert params.radius_km is not None
        user_point = func.ST_SetSRID(func.ST_MakePoint(params.lon, params.lat), 4326)
        user_point_geog = cast(user_point, Geography)

    text_similarity = None
    if params.q:
        # Two-CTE pattern: forces the planner to use ix_products_name_trgm (GIN on
        # lower(name)) and ix_prices_product_store. Without MATERIALIZED the CTEs
        # get inlined and the planner reverts to a slow geo-first plan.
        q_lower = params.q.lower().strip()
        pattern = f"%{q_lower}%"

        matching_products_cte = (
            select(Product.id.label("id"))
            .where(func.lower(Product.name).like(pattern))
            .cte(name="matching_products")
            .prefix_with("MATERIALIZED")
        )
        filters.append(Product.id.in_(select(matching_products_cte.c.id)))

        if has_location:
            assert params.radius_km is not None
            radius_m = params.radius_km * 1000
            nearby_stores_cte = (
                select(Store.id.label("id"))
                .where(Store.geog.is_not(None))
                .where(func.ST_DWithin(Store.geog, user_point_geog, radius_m))
                .cte(name="nearby_stores")
                .prefix_with("MATERIALIZED")
            )
            filters.append(Store.id.in_(select(nearby_stores_cte.c.id)))

        # Similarity is computed only in SELECT for relevance sort, never as a
        # predicate - predicate use bypasses the trigram index.
        name_sim = func.similarity(func.lower(Product.name), q_lower)
        brand_sim = func.coalesce(func.similarity(func.lower(Product.brand), q_lower), literal(0))
        text_similarity = func.greatest(name_sim, brand_sim).label("text_similarity")
    elif has_location:
        # No text search: use the cached store-IDs fast path.
        assert params.lat is not None
        assert params.lon is not None
        assert params.radius_km is not None
        nearby_store_ids = await get_store_ids_within_radius(
            session,
            lat=params.lat,
            lon=params.lon,
            radius_km=params.radius_km,
        )
        if not nearby_store_ids:
            return ProductListResponse(items=[], total=0, page=page, page_size=page_size)
        filters.append(Store.id.in_(nearby_store_ids))
    if params.chain:
        filters.append(Product.chain.in_(params.chain))
    if params.store:
        filters.append(Store.id.in_([UUID(store_id) for store_id in params.store]))
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
    # Only count a promo as valid if promo_ends_at is NULL or in the future
    now_ts = func.now()
    effective_price = effective_price_expression()
    if params.price_min is not None:
        filters.append(effective_price >= params.price_min)
    if params.price_max is not None:
        filters.append(effective_price <= params.price_max)
    if params.sugar_free is not None:
        filters.append(Product.is_sugar_free == params.sugar_free)
    if params.promo_only:
        # Only return products with actual, non-expired discounts
        filters.append(Price.promo_price_nzd.is_not(None))
        filters.append(Price.promo_price_nzd < Price.price_nzd)
        filters.append(or_(Price.promo_ends_at.is_(None), Price.promo_ends_at > now_ts))
        # Exclude discounts >= 25% (NZ alcohol advertising law, s237)
        filters.append(
            (Price.price_nzd - Price.promo_price_nzd)
            / func.nullif(Price.price_nzd, 0)
            < MAX_PROMO_DISPLAY_DISCOUNT
        )

    discount_ratio = (
        (Price.price_nzd - effective_price)
        / func.nullif(Price.price_nzd, 0)
    ).label("discount_ratio")
    price_per_100ml = (
        effective_price / func.nullif(Product.total_volume_ml / 100.0, 0)
    ).label("price_per_100ml_sort")
    standard_drinks_expr = (
        (Product.total_volume_ml / 1000.0)
        * (Product.abv_percent / 100.0)
        * STANDARD_DRINK_FACTOR
    )
    price_per_standard_drink = (
        effective_price / func.nullif(standard_drinks_expr, 0)
    ).label("price_per_standard_drink_sort")
    distance_m = (
        func.ST_Distance(Store.geog, user_point_geog).label("distance_m")
        if user_point_geog is not None
        else None
    )
    distance_m_or_null = distance_m if distance_m is not None else literal(None).label("distance_m")

    sort_order = build_sort_order(
        sort=params.sort,
        discount_ratio=discount_ratio,
        price_per_100ml=price_per_100ml,
        price_per_standard_drink=price_per_standard_drink,
        effective_price=effective_price,
        distance_m=distance_m,
        text_similarity=text_similarity,
    )

    if params.unique_products:
        name_key = func.lower(func.trim(Product.name)).label("name_key")
        # Partition groups all nearby store-listings of the same product. We reuse
        # it for the row_number dedup and to derive the cheapest-nearby signal
        # (min effective price + store count) at no extra sort cost.
        dedup_partition = (name_key, Product.pack_count, Product.total_volume_ml)
        inner = (
            select(
                Product.id.label("product_id"),
                Price.id.label("price_id"),
                Store.id.label("store_id"),
                discount_ratio,
                distance_m_or_null,
                effective_price.label("eff_price"),
                func.min(effective_price).over(partition_by=dedup_partition).label("min_eff_price"),
                func.count().over(partition_by=dedup_partition).label("store_count"),
                func.row_number()
                .over(
                    partition_by=dedup_partition,
                    order_by=tuple(sort_order),
                )
                .label("rn"),
            )
            .select_from(Product)
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
        )
        if filters:
            inner = inner.where(and_(*filters))

        inner_subq = inner.subquery()
        query = (
            select(
                Product,
                Price,
                Store,
                inner_subq.c.discount_ratio,
                inner_subq.c.distance_m,
                inner_subq.c.eff_price,
                inner_subq.c.min_eff_price,
                inner_subq.c.store_count,
            )
            .select_from(inner_subq)
            .join(Product, Product.id == inner_subq.c.product_id)
            .join(Price, Price.id == inner_subq.c.price_id)
            .join(Store, Store.id == inner_subq.c.store_id)
            .where(inner_subq.c.rn == 1)
        )
        query = query.order_by(*sort_order)

        total_result = await session.execute(
            select(func.count()).select_from(inner_subq).where(inner_subq.c.rn == 1)
        )
        total = total_result.scalar_one()
    else:
        query = (
            select(Product, Price, Store, distance_m_or_null)
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
        )
        count_query = (
            select(func.count(Price.id))
            .select_from(Product)
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
        )
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)

        query = query.order_by(*sort_order)
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

    query = query.limit(page_size).offset((page - 1) * page_size)

    result = await session.execute(query)
    rows = result.all()
    items: list[ProductSchema] = []
    response_time = datetime.now(tz=timezone.utc)

    for row in rows:
        is_cheapest_nearby = False
        if params.unique_products:
            product, price, store, _, distance_m_value, eff_price, min_eff_price, store_count = row
            # "Cheapest nearby" only when there's something to compare against
            # (more than one nearby store) and this listing matches the lowest
            # effective price. Requires a location to mean "nearby".
            if (
                has_location
                and store_count
                and store_count > 1
                and min_eff_price is not None
                and eff_price is not None
            ):
                is_cheapest_nearby = (
                    eff_price <= min_eff_price + Decimal("0.001")
                )
        else:
            product, price, store, distance_m_value = row
        items.append(
            build_product_schema(
                product=product,
                price=price,
                store=store,
                distance_m=distance_m_value,
                is_cheapest_nearby=is_cheapest_nearby,
                now=response_time,
            )
        )

    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


async def fetch_products_by_ids(
    session: AsyncSession,
    product_ids: list[UUID],
    *,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> list[ProductSchema]:
    """Fetch multiple products by their IDs, returning one row per product (cheapest price)."""
    if not product_ids:
        return []

    distance_m: Any = literal(None).label("distance_m")
    filters: list[Any] = [Store.sells_alcohol.is_(True)]
    if lat is not None and lon is not None and radius_km is not None:
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        user_point_geog = cast(user_point, Geography)
        distance_m = func.ST_Distance(Store.geog, user_point_geog).label("distance_m")
        filters.extend(
            [
                Store.geog.is_not(None),
                func.ST_DWithin(Store.geog, user_point_geog, radius_km * 1000),
            ]
        )

    effective_price = effective_price_expression()
    query = (
        select(Product, Price, Store, distance_m)
        .join(Price, Price.product_id == Product.id)
        .join(Store, Store.id == Price.store_id)
        .where(Product.id.in_(product_ids))
        .where(and_(*filters))
        .order_by(Product.id.asc(), effective_price.asc(), Price.id.asc())
    )

    result = await session.execute(query)
    rows = result.all()

    # Keep only the cheapest price per product
    seen: set[UUID] = set()
    items_by_product: dict[UUID, ProductSchema] = {}
    response_time = datetime.now(tz=timezone.utc)
    for product, price, store, distance_m_value in rows:
        if product.id in seen:
            continue
        seen.add(product.id)
        items_by_product[product.id] = build_product_schema(
            product=product,
            price=price,
            store=store,
            distance_m=distance_m_value,
            now=response_time,
        )

    return [
        items_by_product[product_id]
        for product_id in product_ids
        if product_id in items_by_product
    ]


__all__ = [
    "fetch_autocomplete",
    "fetch_popular",
    "fetch_product_detail",
    "fetch_products",
    "fetch_products_by_ids",
    "fetch_stores_nearby",
]
