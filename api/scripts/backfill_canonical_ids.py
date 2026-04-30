"""Enhanced backfill: compute canonical_product_id for all products.

Improvements over the original:
- Processes ALL products (not just those with all fields already set)
- Re-infers brand from name to normalize cross-chain brand inconsistencies
- Applies standard volume inference (wine→750ml, spirits→700ml) for
  products with no volume in their name
- Selects only needed columns to minimise memory within 256 MiB container

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

PAGE_SIZE = 5000

_WINE_CATS = frozenset({
    "wine", "red_wine", "white_wine", "rose", "sparkling", "champagne", "fortified_wine",
})
_SPIRIT_CATS = frozenset({
    "spirits", "vodka", "gin", "rum", "whisky", "bourbon", "scotch",
    "tequila", "brandy", "cognac", "liqueur",
})


def _infer_standard_volume(category: str | None) -> tuple[float | None, int | None]:
    if not category:
        return None, None
    cat = category.lower()
    if cat in _WINE_CATS:
        return 750.0, 1
    if cat in _SPIRIT_CATS:
        return 700.0, 1
    return None, None


async def backfill() -> None:
    async with get_async_session() as session:
        count_result = await session.execute(select(func.count()).select_from(Product))
        total = count_result.scalar_one()

    print(f"Total products to process: {total}")

    updated = 0
    skipped = 0
    unmatchable = 0
    offset = 0

    # Select only the 7 columns we need — avoids loading large text/image fields
    cols = (
        Product.id,
        Product.name,
        Product.brand,
        Product.total_volume_ml,
        Product.pack_count,
        Product.category,
        Product.is_sugar_free,
        Product.canonical_product_id,
    )

    while offset < total:
        async with get_async_session() as session:
            result = await session.execute(
                select(*cols).order_by(Product.id).offset(offset).limit(PAGE_SIZE)
            )
            rows = result.all()

        if not rows:
            break

        batch_updates: list[tuple] = []

        for row in rows:
            (prod_id, name, brand, vol_ml, pack, category,
             is_sugar_free, existing_cid) = row

            # Re-infer brand from name to normalize across chains
            if name:
                inferred = infer_brand(name)
                if inferred:
                    brand = inferred

            # Apply standard volume inference when volume is missing
            if vol_ml is None or pack is None:
                cat = category
                if cat is None and name:
                    cat = infer_category(name)
                inf_vol, inf_pack = _infer_standard_volume(cat)
                if vol_ml is None:
                    vol_ml = inf_vol
                if pack is None:
                    pack = inf_pack

            canonical_id = compute_canonical_id(
                name=name,
                brand=brand,
                total_volume_ml=vol_ml,
                pack_count=pack,
                category=category,
                is_sugar_free=is_sugar_free or False,
            )

            if canonical_id is None:
                unmatchable += 1
            elif canonical_id != existing_cid:
                batch_updates.append((prod_id, canonical_id))
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

        offset += len(rows)
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
