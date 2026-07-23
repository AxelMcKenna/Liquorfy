"""Product detail, comparison, and price-history queries."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Price, PriceHistory, Product, Store
from app.schemas.products import (
    CrossChainPrice,
    PriceHistoryPoint,
    ProductDetailSchema,
)
from app.services.parser_utils import format_product_name
from app.services.product_presenter import (
    build_cross_chain_price,
    build_price_schema,
)
from app.services.search_support import effective_price_expression


async def fetch_product_detail(
    session: AsyncSession,
    product_id: UUID,
    *,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> ProductDetailSchema:
    has_location = lat is not None and lon is not None and radius_km is not None
    effective_price = effective_price_expression()

    if has_location:
        assert lat is not None
        assert lon is not None
        assert radius_km is not None
        user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        distance_m = func.ST_Distance(Store.geog, cast(user_point, Geography))
        query = (
            select(Product, Price, Store, distance_m.label("distance_m"))
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
            .where(
                Product.id == product_id,
                distance_m <= radius_km * 1000,
                Store.sells_alcohol.is_(True),
            )
            .order_by(effective_price.asc(), Price.id.asc())
        )
    else:
        query = (
            select(Product, Price, Store, literal(None).label("distance_m"))
            .join(Price, Price.product_id == Product.id)
            .join(Store, Store.id == Price.store_id)
            .where(Product.id == product_id, Store.sells_alcohol.is_(True))
            .order_by(effective_price.asc(), Price.id.asc())
        )

    rows = (await session.execute(query)).all()
    if not rows:
        raise ValueError("Product not found")

    response_time = datetime.now(tz=timezone.utc)
    product, first_price, first_store, first_dist = rows[0]
    primary_price = build_price_schema(
        product=product,
        price=first_price,
        store=first_store,
        distance_m=first_dist,
        now=response_time,
    )
    other_prices = [
        build_price_schema(
            product=other_product,
            price=price,
            store=store,
            distance_m=distance,
            now=response_time,
        )
        for other_product, price, store, distance in rows[1:]
    ]

    cross_chain_prices: list[CrossChainPrice] = []
    if product.canonical_product_id is not None:
        if has_location:
            assert lat is not None
            assert lon is not None
            assert radius_km is not None
            user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
            distance_m = func.ST_Distance(Store.geog, cast(user_point, Geography))
            comparison_query = (
                select(Product, Price, Store, distance_m.label("distance_m"))
                .join(Price, Price.product_id == Product.id)
                .join(Store, Store.id == Price.store_id)
                .where(
                    Product.canonical_product_id == product.canonical_product_id,
                    Product.id != product.id,
                    distance_m <= radius_km * 1000,
                    Store.sells_alcohol.is_(True),
                )
                .order_by(effective_price.asc(), Price.id.asc())
            )
        else:
            comparison_query = (
                select(Product, Price, Store, literal(None).label("distance_m"))
                .join(Price, Price.product_id == Product.id)
                .join(Store, Store.id == Price.store_id)
                .where(
                    Product.canonical_product_id == product.canonical_product_id,
                    Product.id != product.id,
                    Store.sells_alcohol.is_(True),
                )
                .order_by(effective_price.asc(), Price.id.asc())
            )

        seen_chains: set[str] = set()
        for compared_product, compared_price, compared_store, distance in (
            await session.execute(comparison_query)
        ).all():
            if compared_store.chain in seen_chains:
                continue
            seen_chains.add(compared_store.chain)
            cross_chain_prices.append(
                build_cross_chain_price(
                    product=compared_product,
                    price=compared_price,
                    store=compared_store,
                    distance_m=distance,
                    now=response_time,
                )
            )

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
    price_history = [
        PriceHistoryPoint(
            date=str(row.day),
            price_nzd=row.price_nzd,
            promo_price_nzd=row.promo_price_nzd,
        )
        for row in (await session.execute(history_query)).all()
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


__all__ = ["fetch_product_detail"]
