"""Enhanced backfill: compute canonical_product_id for all products.

Improvements over the original:
- Processes ALL products (not just those with all fields already set)
- Re-infers brand from name to normalize cross-chain brand inconsistencies
- Applies standard volume inference (wine→750ml, spirits→700ml) for
  products with no volume in their name
- Uses paginated queries to stay within container memory limits

Usage:
    cd api && python scripts/backfill_canonical_ids.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select, update

from app.db.models import Product
from app.db.session import async_transaction, get_async_session
from app.services.canonical import compute_canonical_id
from app.services.parser_utils import infer_brand, infer_category

PAGE_SIZE = 2000

_WINE_CATS = frozenset({
    "wine", "red_wine", "white_wine", "rose", "sparkling", "champagne", "fortified_wine",
})
_SPIRIT_CATS = frozenset({
    "spirits", "vodka", "gin", "rum", "whisky", "bourbon", "scotch",
    "tequila", "brandy", "cognac", "liqueur",
})


def _infer_standard_volume(category: str | None) -> tuple[float | None, int | None]:
    """Return (total_volume_ml, pack_count) for single-unit products by category."""
    if not category:
        return None, None
    cat = category.lower()
    if cat in _WINE_CATS:
        return 750.0, 1
    if cat in _SPIRIT_CATS:
        return 700.0, 1
    return None, None


async def backfill() -> None:
    # Get total count
    async with get_async_session() as session:
        count_result = await session.execute(select(func.count()).select_from(Product))
        total = count_result.scalar_one()

    print(f"Total products to process: {total}")

    updated = 0
    skipped = 0
    unmatchable = 0
    offset = 0

    while offset < total:
        # Load one page
        async with get_async_session() as session:
            result = await session.execute(
                select(Product).order_by(Product.id).offset(offset).limit(PAGE_SIZE)
            )
            products = result.scalars().all()

        if not products:
            break

        batch_updates: list[tuple] = []  # (id, canonical_product_id)

        for product in products:
            # Re-infer brand from name to normalize across chains.
            brand = product.brand
            if product.name:
                inferred = infer_brand(product.name)
                if inferred:
                    brand = inferred

            # Resolve volume: use stored values, or infer from category.
            vol_ml = product.total_volume_ml
            pack = product.pack_count
            if vol_ml is None or pack is None:
                cat = product.category
                if cat is None and product.name:
                    cat = infer_category(product.name)
                inf_vol, inf_pack = _infer_standard_volume(cat)
                if vol_ml is None:
                    vol_ml = inf_vol
                if pack is None:
                    pack = inf_pack

            canonical_id = compute_canonical_id(
                name=product.name,
                brand=brand,
                total_volume_ml=vol_ml,
                pack_count=pack,
                category=product.category,
                is_sugar_free=product.is_sugar_free or False,
            )

            if canonical_id is None:
                unmatchable += 1
            elif canonical_id != product.canonical_product_id:
                batch_updates.append((product.id, canonical_id))
                updated += 1
            else:
                skipped += 1

        if batch_updates:
            async with async_transaction() as session:
                for prod_id, cid in batch_updates:
                    await session.execute(
                        update(Product)
                        .where(Product.id == prod_id)
                        .values(canonical_product_id=cid)
                    )

        offset += len(products)
        print(
            f"  {offset}/{total} — "
            f"updated={updated}, skipped={skipped}, unmatchable={unmatchable}"
        )

    print(f"\nBackfill complete:")
    print(f"  Updated:     {updated}")
    print(f"  Skipped:     {skipped} (canonical ID already correct)")
    print(f"  Unmatchable: {unmatchable} (missing brand/volume even after inference)")


if __name__ == "__main__":
    asyncio.run(backfill())
