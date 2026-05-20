"""Re-parse total_volume_ml / pack_count from product names for rows that
have NULL canonical_product_id.

The volume parser was recently taught to handle CityHive's truncated
size suffixes ("330c", "330b", "700m"). Existing rows that pre-date the
parser fix still have NULL volume and therefore NULL canonical_product_id.
This script re-parses each name, updates the volume columns, and re-runs
the canonical matcher in one pass.

Idempotent: safe to re-run. Rows that still can't yield a volume after
the new parser are left untouched.

Usage:
    cd api && python scripts/maintenance/backfill_volume_from_name.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import select, update

from app.db.models import Product
from app.db.session import async_transaction, get_async_session
from app.services.canonical import compute_canonical_id
from app.services.parser_utils import (
    expand_cityhive_size_codes,
    parse_volume,
)

PAGE_SIZE = 1000


async def main(dry_run: bool) -> None:
    examined = 0
    parsed = 0
    matched = 0
    still_unparsed = 0

    cols = (
        Product.id,
        Product.chain,
        Product.name,
        Product.brand,
        Product.is_sugar_free,
    )

    last_id = None
    while True:
        async with get_async_session() as session:
            q = (
                select(*cols)
                .where(Product.canonical_product_id.is_(None))
                .order_by(Product.id)
                .limit(PAGE_SIZE)
            )
            if last_id is not None:
                q = q.where(Product.id > last_id)
            rows = (await session.execute(q)).all()

        if not rows:
            break

        updates: list[dict] = []
        for row in rows:
            examined += 1
            last_id = row.id

            if not row.name:
                still_unparsed += 1
                continue

            expanded = expand_cityhive_size_codes(row.name)
            volume = parse_volume(expanded)
            if volume.total_volume_ml is None:
                still_unparsed += 1
                continue

            parsed += 1
            canonical = compute_canonical_id(
                name=row.name,
                brand=row.brand,
                total_volume_ml=volume.total_volume_ml,
                pack_count=volume.pack_count,
                is_sugar_free=bool(row.is_sugar_free),
            )
            if canonical is not None:
                matched += 1

            updates.append(
                {
                    "id": row.id,
                    "total_volume_ml": volume.total_volume_ml,
                    "unit_volume_ml": volume.unit_volume_ml,
                    "pack_count": volume.pack_count,
                    "canonical_product_id": canonical,
                }
            )

        if updates and not dry_run:
            async with async_transaction() as session:
                for u in updates:
                    await session.execute(
                        update(Product)
                        .where(Product.id == u["id"])
                        .values(
                            total_volume_ml=u["total_volume_ml"],
                            unit_volume_ml=u["unit_volume_ml"],
                            pack_count=u["pack_count"],
                            canonical_product_id=u["canonical_product_id"],
                        )
                    )

        print(
            f"  examined={examined} parsed={parsed} matched={matched} "
            f"still_unparsed={still_unparsed}"
        )

    print()
    print("Summary:")
    print(f"  Examined:        {examined:,}")
    print(f"  Volume parsed:   {parsed:,}")
    print(f"  Canonical set:   {matched:,}")
    print(f"  Still unparsed:  {still_unparsed:,}")
    if dry_run:
        print("\n--dry-run: no rows modified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
