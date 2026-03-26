from __future__ import annotations

from typing import Any
from uuid import UUID

from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, and_, case, cast, func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography

from app.core.config import get_settings
from app.db.models import Price, PriceHistory, Product, Store
from app.schemas.products import CrossChainPrice, PriceHistoryPoint, PriceSchema, ProductDetailSchema, ProductListResponse, ProductSchema, StoreListResponse, StoreSchema
from app.schemas.queries import ProductQueryParams
from app.services.cache import cached_json
from app.services.parser_utils import CATEGORY_HIERARCHY, format_product_name
from app.services.pricing import STANDARD_DRINK_FACTOR, compute_pricing_metrics

settings = get_settings()

# Prices not seen in over 7 days are considered stale
_STALE_THRESHOLD = timedelta(days=7)

# NZ Sale and Supply of Alcohol Act 2012, s237
_MAX_PROMO_DISPLAY_DISCOUNT = 0.25


def _effective_price(price: Price) -> float:
    """Return the effective price, ignoring expired promos."""
    if price.promo_price_nzd is not None:
        if price.promo_ends_at is None or price.promo_ends_at > datetime.now(tz=timezone.utc):
            return price.promo_price_nzd
    return price.price_nzd


def _is_stale(price: Price) -> bool:
    """Return True if the price hasn't been seen recently."""
    if price.last_seen_at is None:
        return True
    cutoff = datetime.now(tz=timezone.utc)
    # last_seen_at may be naive (utcnow) — treat as UTC
    last_seen = price.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return (cutoff - last_seen) > _STALE_THRESHOLD


def _store_bucket_key(lat: float, lon: float, radius_km: float) -> str:
    return f"stores_nearby:{round(lat, 2)}:{round(lon, 2)}:{round(radius_km, 1)}"


async def _get_store_ids_within_radius(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> list[UUID]:
    cache_key = _store_bucket_key(lat, lon, radius_km)

    async def producer() -> list[str]:
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        user_point_geog = cast(user_point, Geography)
        radius_m = radius_km * 1000
        query = (
            select(Store.id)
            .where(Store.geog.is_not(None))
            .where(func.ST_DWithin(Store.geog, user_point_geog, radius_m))
        )
        result = await session.execute(query)
        return [str(store_id) for store_id in result.scalars().all()]

    cached_ids = await cached_json(cache_key, settings.api_cache_ttl_seconds, producer)
    return [UUID(store_id) for store_id in cached_ids]


def _build_sort_order(
    *,
    sort: str,
    discount_ratio: Any,
    price_per_100ml: Any,
    price_per_standard_drink: Any,
    effective_price: Any,
    distance_m: Any | None,
    text_similarity: Any | None = None,
) -> list[Any]:
    tie_breakers = [Price.price_last_changed_at.desc(), Product.name.asc(), Price.id.asc()]
    if sort == "relevance" and text_similarity is not None:
        return [text_similarity.desc().nulls_last(), *tie_breakers]
    if sort == "discount":
        return [discount_ratio.desc().nulls_last(), *tie_breakers]
    if sort == "price_per_standard_drink":
        return [price_per_standard_drink.asc().nulls_last(), *tie_breakers]
    if sort == "total_price":
        return [effective_price.asc().nulls_last(), *tie_breakers]
    if sort == "newest":
        return [Price.price_last_changed_at.desc(), Product.name.asc(), Price.id.asc()]
    if sort == "distance" and distance_m is not None:
        return [distance_m.asc().nulls_last(), *tie_breakers]
    return [price_per_100ml.asc().nulls_last(), *tie_breakers]


async def fetch_products(
    session: AsyncSession,
    params: ProductQueryParams,
) -> ProductListResponse:
    page = max(params.page, 1)
    page_size = max(min(params.page_size, 100), 1)

    filters = []
    user_point_geog = None
    if params.lat is not None and params.lon is not None and params.radius_km is not None:
        nearby_store_ids = await _get_store_ids_within_radius(
            session,
            lat=params.lat,
            lon=params.lon,
            radius_km=params.radius_km,
        )
        if not nearby_store_ids:
            return ProductListResponse(items=[], total=0, page=page, page_size=page_size)

        user_point = func.ST_SetSRID(func.ST_MakePoint(params.lon, params.lat), 4326)
        user_point_geog = cast(user_point, Geography)
        filters.append(Store.id.in_(nearby_store_ids))

    # Trigram similarity threshold for fuzzy text search (0 = no match, 1 = exact)
    _TRGM_THRESHOLD = 0.15

    text_similarity = None
    if params.q:
        q_lower = params.q.lower().strip()
        # Use trigram similarity for fuzzy matching (leverages GIN trgm indexes)
        name_sim = func.similarity(func.lower(Product.name), q_lower)
        brand_sim = func.coalesce(func.similarity(func.lower(Product.brand), q_lower), literal(0))
        # Also keep LIKE for substring matches that similarity might miss
        # (e.g. "12pk" inside "Steinlager Classic 12pk 330ml Bottles")
        pattern = f"%{q_lower}%"
        like_match = or_(
            func.lower(Product.name).like(pattern),
            func.lower(Product.brand).like(pattern),
        )
        filters.append(
            or_(
                name_sim >= _TRGM_THRESHOLD,
                brand_sim >= _TRGM_THRESHOLD,
                like_match,
            )
        )
        # Best similarity score across name and brand — used for relevance sorting
        text_similarity = func.greatest(name_sim, brand_sim).label("text_similarity")
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
    valid_promo = case(
        (
            and_(
                Price.promo_price_nzd.is_not(None),
                or_(Price.promo_ends_at.is_(None), Price.promo_ends_at > now_ts),
            ),
            Price.promo_price_nzd,
        ),
        else_=None,
    )
    effective_price = func.coalesce(valid_promo, Price.price_nzd)
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
            < _MAX_PROMO_DISPLAY_DISCOUNT
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

    sort_order = _build_sort_order(
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
        inner = (
            select(
                Product.id.label("product_id"),
                Price.id.label("price_id"),
                Store.id.label("store_id"),
                discount_ratio,
                distance_m_or_null,
                func.row_number()
                .over(
                    partition_by=(name_key, Product.pack_count, Product.total_volume_ml),
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
            select(Product, Price, Store, inner_subq.c.discount_ratio, inner_subq.c.distance_m)
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

    for row in rows:
        if params.unique_products:
            product, price, store, _, distance_m_value = row
        else:
            product, price, store, distance_m_value = row
        effective = _effective_price(price)
        metrics = compute_pricing_metrics(
            total_volume_ml=product.total_volume_ml,
            abv_percent=product.abv_percent,
            effective_price_nzd=effective,
        )
        distance = round(distance_m_value / 1000, 2) if distance_m_value is not None else None

        # Suppress promo display for discounts >= 25% (NZ alcohol advertising law, s237)
        suppress_promo = False
        if price.promo_price_nzd is not None and price.price_nzd > 0:
            discount = (price.price_nzd - effective) / price.price_nzd
            suppress_promo = discount >= _MAX_PROMO_DISPLAY_DISCOUNT

        items.append(
            ProductSchema(
                id=product.id,
                name=format_product_name(product.name, product.brand),
                brand=product.brand,
                category=product.category,
                chain=product.chain,
                abv_percent=product.abv_percent,
                total_volume_ml=product.total_volume_ml,
                pack_count=product.pack_count,
                unit_volume_ml=product.unit_volume_ml,
                image_url=product.image_url,
                product_url=product.product_url,
                is_sugar_free=product.is_sugar_free,
                price=PriceSchema(
                    store_id=store.id,
                    store_name=store.name,
                    chain=store.chain,
                    price_nzd=effective if suppress_promo else price.price_nzd,
                    promo_price_nzd=None if suppress_promo else price.promo_price_nzd,
                    promo_text=None if suppress_promo else price.promo_text,
                    promo_ends_at=None if suppress_promo else price.promo_ends_at,
                    price_per_100ml=metrics.price_per_100ml,
                    standard_drinks=metrics.standard_drinks,
                    price_per_standard_drink=metrics.price_per_standard_drink,
                    is_member_only=False if suppress_promo else price.is_member_only,
                    is_stale=_is_stale(price),
                    distance_km=distance,
                ),
                last_updated=price.last_seen_at,
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

    user_point_geog = None
    distance_m: Any = literal(None).label("distance_m")
    if lat is not None and lon is not None and radius_km is not None:
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        user_point_geog = cast(user_point, Geography)
        distance_m = func.ST_Distance(Store.geog, user_point_geog).label("distance_m")

    query = (
        select(Product, Price, Store, distance_m)
        .join(Price, Price.product_id == Product.id)
        .join(Store, Store.id == Price.store_id)
        .where(Product.id.in_(product_ids))
        .order_by(Price.price_nzd.asc())
    )

    result = await session.execute(query)
    rows = result.all()

    # Keep only the cheapest price per product
    seen: set[UUID] = set()
    items: list[ProductSchema] = []
    for product, price, store, distance_m_value in rows:
        if product.id in seen:
            continue
        seen.add(product.id)

        effective = _effective_price(price)
        metrics = compute_pricing_metrics(
            total_volume_ml=product.total_volume_ml,
            abv_percent=product.abv_percent,
            effective_price_nzd=effective,
        )
        distance = round(distance_m_value / 1000, 2) if distance_m_value is not None else None

        suppress_promo = False
        if price.promo_price_nzd is not None and price.price_nzd > 0:
            discount = (price.price_nzd - effective) / price.price_nzd
            suppress_promo = discount >= _MAX_PROMO_DISPLAY_DISCOUNT

        items.append(
            ProductSchema(
                id=product.id,
                name=format_product_name(product.name, product.brand),
                brand=product.brand,
                category=product.category,
                chain=product.chain,
                abv_percent=product.abv_percent,
                total_volume_ml=product.total_volume_ml,
                pack_count=product.pack_count,
                unit_volume_ml=product.unit_volume_ml,
                image_url=product.image_url,
                product_url=product.product_url,
                is_sugar_free=product.is_sugar_free,
                price=PriceSchema(
                    store_id=store.id,
                    store_name=store.name,
                    chain=store.chain,
                    price_nzd=effective if suppress_promo else price.price_nzd,
                    promo_price_nzd=None if suppress_promo else price.promo_price_nzd,
                    promo_text=None if suppress_promo else price.promo_text,
                    promo_ends_at=None if suppress_promo else price.promo_ends_at,
                    price_per_100ml=metrics.price_per_100ml,
                    standard_drinks=metrics.standard_drinks,
                    price_per_standard_drink=metrics.price_per_standard_drink,
                    is_member_only=False if suppress_promo else price.is_member_only,
                    is_stale=_is_stale(price),
                    distance_km=distance,
                ),
                last_updated=price.last_seen_at,
            )
        )

    return items


async def fetch_product_detail(
    session: AsyncSession,
    product_id: UUID,
    *,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> ProductDetailSchema:
    has_location = lat is not None and lon is not None and radius_km is not None

    if has_location:
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        distance_m = func.ST_Distance(
            Store.geog, cast(user_point, Geography)
        )
        query = (
            select(Product, Price, Store, distance_m.label("distance_m"))
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
            .where(Product.id == product_id, distance_m <= radius_km * 1000)
            .order_by(Price.price_nzd.asc())
        )
    else:
        query = (
            select(Product, Price, Store, literal(None).label("distance_m"))
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
            .where(Product.id == product_id)
            .order_by(Price.price_nzd.asc())
        )

    result = await session.execute(query)
    rows = result.all()
    if not rows:
        raise ValueError("Product not found")

    def _build_price_schema(price: "Price", store: "Store", dist_m=None) -> PriceSchema:
        effective = _effective_price(price)
        metrics = compute_pricing_metrics(
            total_volume_ml=rows[0][0].total_volume_ml,
            abv_percent=rows[0][0].abv_percent,
            effective_price_nzd=effective,
        )
        suppress_promo = False
        if price.promo_price_nzd is not None and price.price_nzd > 0:
            discount = (price.price_nzd - effective) / price.price_nzd
            suppress_promo = discount >= _MAX_PROMO_DISPLAY_DISCOUNT
        return PriceSchema(
            store_id=store.id,
            store_name=store.name,
            chain=store.chain,
            price_nzd=effective if suppress_promo else price.price_nzd,
            promo_price_nzd=None if suppress_promo else price.promo_price_nzd,
            promo_text=None if suppress_promo else price.promo_text,
            promo_ends_at=None if suppress_promo else price.promo_ends_at,
            price_per_100ml=metrics.price_per_100ml,
            standard_drinks=metrics.standard_drinks,
            price_per_standard_drink=metrics.price_per_standard_drink,
            is_member_only=False if suppress_promo else price.is_member_only,
            is_stale=_is_stale(price),
            distance_km=round(dist_m / 1000, 1) if dist_m is not None else None,
        )

    product, first_price, first_store, first_dist = rows[0]
    primary_price = _build_price_schema(first_price, first_store, first_dist)
    other_prices = [_build_price_schema(p, s, d) for _, p, s, d in rows[1:]]

    # Cross-chain comparison: find same product at other chains
    cross_chain_prices: list[CrossChainPrice] = []
    if product.canonical_product_id is not None:

        if has_location:
            user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
            distance_m = func.ST_Distance(
                Store.geog, cast(user_point, Geography)
            )
            cc_query = (
                select(Product, Price, Store, distance_m.label("distance_m"))
                .join(Price, Price.product_id == Product.id)
                .join(Store, Store.id == Price.store_id)
                .where(
                    Product.canonical_product_id == product.canonical_product_id,
                    Product.id != product.id,
                    distance_m <= radius_km * 1000,
                )
                .order_by(Price.price_nzd.asc())
            )
        else:
            cc_query = (
                select(Product, Price, Store, literal(None).label("distance_m"))
                .join(Price, Price.product_id == Product.id)
                .join(Store, Store.id == Price.store_id)
                .where(
                    Product.canonical_product_id == product.canonical_product_id,
                    Product.id != product.id,
                )
                .order_by(Price.price_nzd.asc())
            )

        cc_result = await session.execute(cc_query)
        cc_rows = cc_result.all()

        # Keep only the best price per chain (cheapest store per chain)
        seen_chains: set[str] = set()
        for cc_product, cc_price, cc_store, dist_m in cc_rows:
            if cc_store.chain in seen_chains:
                continue
            seen_chains.add(cc_store.chain)

            effective = _effective_price(cc_price)
            metrics = compute_pricing_metrics(
                total_volume_ml=cc_product.total_volume_ml,
                abv_percent=cc_product.abv_percent,
                effective_price_nzd=effective,
            )

            dist_km = round(dist_m / 1000, 1) if dist_m is not None else None

            suppress_promo = False
            if cc_price.promo_price_nzd is not None and cc_price.price_nzd > 0:
                discount = (cc_price.price_nzd - effective) / cc_price.price_nzd
                suppress_promo = discount >= _MAX_PROMO_DISPLAY_DISCOUNT

            cross_chain_prices.append(CrossChainPrice(
                product_id=cc_product.id,
                product_name=format_product_name(cc_product.name, cc_product.brand),
                product_url=cc_product.product_url,
                image_url=cc_product.image_url,
                chain=cc_store.chain,
                store_id=cc_store.id,
                store_name=cc_store.name,
                price_nzd=effective if suppress_promo else cc_price.price_nzd,
                promo_price_nzd=None if suppress_promo else cc_price.promo_price_nzd,
                promo_text=None if suppress_promo else cc_price.promo_text,
                promo_ends_at=None if suppress_promo else cc_price.promo_ends_at,
                price_per_100ml=metrics.price_per_100ml,
                price_per_standard_drink=metrics.price_per_standard_drink,
                is_member_only=False if suppress_promo else cc_price.is_member_only,
                is_stale=_is_stale(cc_price),
                distance_km=dist_km,
            ))

    # Price history (30-day rolling, best price per day)
    history_query = (
        select(
            func.date(PriceHistory.recorded_at).label("day"),
            func.min(PriceHistory.price_nzd).label("price_nzd"),
            func.min(PriceHistory.promo_price_nzd).label("promo_price_nzd"),
        )
        .where(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= func.now() - text("interval '30 days'"),
        )
        .group_by(text("day"))
        .order_by(text("day"))
    )
    history_result = await session.execute(history_query)
    price_history = [
        PriceHistoryPoint(
            date=str(row.day),
            price_nzd=row.price_nzd,
            promo_price_nzd=row.promo_price_nzd,
        )
        for row in history_result.all()
    ]

    return ProductDetailSchema(
        id=product.id,
        name=format_product_name(product.name, product.brand),
        brand=product.brand,
        category=product.category,
        chain=product.chain,
        abv_percent=product.abv_percent,
        total_volume_ml=product.total_volume_ml,
        pack_count=product.pack_count,
        unit_volume_ml=product.unit_volume_ml,
        image_url=product.image_url,
        product_url=product.product_url,
        is_sugar_free=product.is_sugar_free,
        price=primary_price,
        other_prices=other_prices,
        cross_chain_prices=cross_chain_prices,
        price_history=price_history,
        last_updated=first_price.last_seen_at,
    )


async def fetch_stores_nearby(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_km: float,
) -> StoreListResponse:
    user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    user_point_geog = cast(user_point, Geography)

    store_ids = await _get_store_ids_within_radius(session, lat=lat, lon=lon, radius_km=radius_km)
    if not store_ids:
        return StoreListResponse(items=[])

    distance_m = func.ST_Distance(Store.geog, user_point_geog).label("distance_m")
    query = (
        select(Store, distance_m)
        .where(Store.id.in_(store_ids))
        .order_by(distance_m)
    )
    result = await session.execute(query)
    items = [
        StoreSchema(
            id=store.id,
            name=store.name,
            chain=store.chain,
            lat=store.lat,
            lon=store.lon,
            address=store.address,
            region=store.region,
            distance_km=round(distance / 1000, 2),
        )
        for store, distance in result.all()
    ]
    return StoreListResponse(items=items)


async def fetch_autocomplete(
    session: AsyncSession,
    q: str,
    limit: int = 8,
) -> list[dict]:
    """Fast autocomplete: trigram similarity + popularity boost, no price/store joins."""
    from app.db.models import ProductView

    q_lower = q.lower().strip()
    if len(q_lower) < 2:
        return []

    _TRGM_THRESHOLD = 0.15
    # Popularity boost: log(view_count+1) scaled to add up to ~0.3 to the similarity score
    _POPULARITY_WEIGHT = 0.05

    name_sim = func.similarity(func.lower(Product.name), q_lower)
    brand_sim = func.coalesce(func.similarity(func.lower(Product.brand), q_lower), literal(0))
    text_sim = func.greatest(name_sim, brand_sim)

    # Blend in popularity: similarity + small log(views) boost
    popularity_boost = (
        func.coalesce(func.log(cast(ProductView.view_count + 1, Float)), literal(0))
        * _POPULARITY_WEIGHT
    )
    blended_score = (text_sim + popularity_boost).label("score")

    pattern = f"%{q_lower}%"
    like_match = or_(
        func.lower(Product.name).like(pattern),
        func.lower(Product.brand).like(pattern),
    )

    # Deduplicate by lower(name) to avoid showing the same product from multiple chains
    name_key = func.lower(func.trim(Product.name)).label("name_key")
    inner = (
        select(
            Product.id,
            Product.name,
            Product.brand,
            Product.category,
            Product.image_url,
            Product.chain,
            blended_score,
            func.row_number()
            .over(partition_by=name_key, order_by=blended_score.desc())
            .label("rn"),
        )
        .select_from(Product)
        .outerjoin(ProductView, ProductView.product_id == Product.id)
        .where(
            or_(
                name_sim >= _TRGM_THRESHOLD,
                brand_sim >= _TRGM_THRESHOLD,
                like_match,
            )
        )
    )
    subq = inner.subquery()

    query = (
        select(
            subq.c.id,
            subq.c.name,
            subq.c.brand,
            subq.c.category,
            subq.c.image_url,
            subq.c.chain,
            subq.c.score,
        )
        .where(subq.c.rn == 1)
        .order_by(subq.c.score.desc())
        .limit(limit)
    )

    result = await session.execute(query)
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
        for row in result.all()
    ]


async def fetch_popular(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """Return the most-viewed products (last 7 days)."""
    from app.db.models import ProductView

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
            ProductView.last_viewed_at >= func.now() - text("interval '7 days'"),
        )
        .order_by(ProductView.view_count.desc())
        .limit(limit)
    )

    result = await session.execute(query)
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
        for row in result.all()
    ]


__all__ = ["fetch_products", "fetch_product_detail", "fetch_stores_nearby", "fetch_autocomplete", "fetch_popular"]
