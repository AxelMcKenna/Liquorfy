"""One-time backfill: compute canonical_product_id for existing products.

Usage:
    cd api && python scripts/backfill_canonical_ids.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update

from app.db.models import Product
from app.db.session import get_async_session
from app.services.canonical import compute_canonical_id

BATCH_SIZE = 1000


async def backfill() -> None:
    async with get_async_session() as session:
        # Fetch all products that could be matched (have brand + volume + pack)
        result = await session.execute(
            select(Product).where(
                Product.brand.isnot(None),
                Product.total_volume_ml.isnot(None),
                Product.pack_count.isnot(None),
            )
        )
        products = result.scalars().all()

        updated = 0
        skipped = 0

        for i in range(0, len(products), BATCH_SIZE):
            batch = products[i : i + BATCH_SIZE]
            for product in batch:
                canonical_id = compute_canonical_id(
                    brand=product.brand,
                    total_volume_ml=product.total_volume_ml,
                    pack_count=product.pack_count,
                    abv_percent=product.abv_percent,
                    category=product.category,
                    is_sugar_free=product.is_sugar_free,
                )
                if canonical_id and canonical_id != product.canonical_product_id:
                    await session.execute(
                        update(Product)
                        .where(Product.id == product.id)
                        .values(canonical_product_id=canonical_id)
                    )
                    updated += 1
                else:
                    skipped += 1

            await session.commit()
            print(f"  Processed {min(i + BATCH_SIZE, len(products))}/{len(products)}")

        # Count products that couldn't be matched (null required fields)
        null_result = await session.execute(
            select(Product).where(
                (Product.brand.is_(None))
                | (Product.total_volume_ml.is_(None))
                | (Product.pack_count.is_(None))
            )
        )
        unmatchable = len(null_result.scalars().all())

        print(f"\nBackfill complete:")
        print(f"  Updated:     {updated}")
        print(f"  Skipped:     {skipped} (already correct)")
        print(f"  Unmatchable: {unmatchable} (missing brand/volume/pack)")


if __name__ == "__main__":
    asyncio.run(backfill())
