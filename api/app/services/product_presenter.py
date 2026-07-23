"""Consistent product and price response mapping."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.db.models import Price, Product, Store
from app.schemas.products import CrossChainPrice, PriceSchema, ProductSchema
from app.services.parser_utils import format_product_name
from app.services.pricing import compute_pricing_metrics

STALE_THRESHOLD = timedelta(days=7)
MAX_PROMO_DISPLAY_DISCOUNT = Decimal("0.25")


def effective_price(price: Price, *, now: datetime | None = None) -> Decimal:
    """Return the current payable price, excluding expired promotions."""
    current_time = now or datetime.now(tz=timezone.utc)
    if price.promo_price_nzd is not None:
        if price.promo_ends_at is None or price.promo_ends_at > current_time:
            return price.promo_price_nzd
    return price.price_nzd


def is_stale(price: Price, *, now: datetime | None = None) -> bool:
    """Return whether a price has not been observed within the freshness window."""
    if price.last_seen_at is None:
        return True
    current_time = now or datetime.now(tz=timezone.utc)
    last_seen = price.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return current_time - last_seen > STALE_THRESHOLD


def should_suppress_promo(
    price: Price, *, current_price: Decimal | None = None
) -> bool:
    """Apply the single promotion-display policy used by all API responses."""
    if price.promo_price_nzd is None or price.price_nzd <= 0:
        return False
    payable = current_price if current_price is not None else effective_price(price)
    discount = (price.price_nzd - payable) / price.price_nzd
    return discount >= MAX_PROMO_DISPLAY_DISCOUNT


def build_price_schema(
    *,
    product: Product,
    price: Price,
    store: Store,
    distance_m: float | None = None,
    now: datetime | None = None,
) -> PriceSchema:
    payable = effective_price(price, now=now)
    metrics = compute_pricing_metrics(
        total_volume_ml=product.total_volume_ml,
        abv_percent=product.abv_percent,
        effective_price_nzd=payable,
    )
    suppress_promo = should_suppress_promo(price, current_price=payable)
    return PriceSchema(
        store_id=store.id,
        store_name=store.name,
        chain=store.chain,
        price_nzd=payable if suppress_promo else price.price_nzd,
        promo_price_nzd=None if suppress_promo else price.promo_price_nzd,
        promo_text=None if suppress_promo else price.promo_text,
        promo_ends_at=None if suppress_promo else price.promo_ends_at,
        price_per_100ml=metrics.price_per_100ml,
        standard_drinks=metrics.standard_drinks,
        price_per_standard_drink=metrics.price_per_standard_drink,
        is_member_only=False if suppress_promo else price.is_member_only,
        is_stale=is_stale(price, now=now),
        distance_km=round(distance_m / 1000, 2) if distance_m is not None else None,
    )


def build_product_schema(
    *,
    product: Product,
    price: Price,
    store: Store,
    distance_m: float | None = None,
    is_cheapest_nearby: bool = False,
    now: datetime | None = None,
) -> ProductSchema:
    return ProductSchema(
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
        price=build_price_schema(
            product=product,
            price=price,
            store=store,
            distance_m=distance_m,
            now=now,
        ),
        is_cheapest_nearby=is_cheapest_nearby,
        last_updated=price.last_seen_at,
    )


def build_cross_chain_price(
    *,
    product: Product,
    price: Price,
    store: Store,
    distance_m: float | None = None,
    now: datetime | None = None,
) -> CrossChainPrice:
    mapped_price = build_price_schema(
        product=product,
        price=price,
        store=store,
        distance_m=distance_m,
        now=now,
    )
    return CrossChainPrice(
        product_id=product.id,
        product_name=format_product_name(product.name, product.brand),
        product_url=product.product_url,
        image_url=product.image_url,
        chain=store.chain,
        store_id=store.id,
        store_name=store.name,
        price_nzd=mapped_price.price_nzd,
        promo_price_nzd=mapped_price.promo_price_nzd,
        promo_text=mapped_price.promo_text,
        promo_ends_at=mapped_price.promo_ends_at,
        price_per_100ml=mapped_price.price_per_100ml,
        price_per_standard_drink=mapped_price.price_per_standard_drink,
        is_member_only=mapped_price.is_member_only,
        is_stale=mapped_price.is_stale,
        distance_km=mapped_price.distance_km,
    )


__all__ = [
    "MAX_PROMO_DISPLAY_DISCOUNT",
    "STALE_THRESHOLD",
    "build_cross_chain_price",
    "build_price_schema",
    "build_product_schema",
    "effective_price",
    "is_stale",
    "should_suppress_promo",
]
