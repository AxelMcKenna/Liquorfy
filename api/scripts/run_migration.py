"""Recompute canonical_product_id for all products using Python variant extraction."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncpg
from app.services.canonical import compute_canonical_id

DB_URL = os.environ.get("DATABASE_URL", "")

async def run():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("SET statement_timeout = '0'")

    rows = await conn.fetch("""
        SELECT id, name, brand, total_volume_ml, pack_count, abv_percent, category, is_sugar_free
        FROM products
        WHERE brand IS NOT NULL AND total_volume_ml IS NOT NULL AND pack_count IS NOT NULL
    """)
    print(f"Computing canonical IDs for {len(rows)} products...")

    batch = []
    for row in rows:
        cid = compute_canonical_id(
            name=row["name"],
            brand=row["brand"],
            total_volume_ml=row["total_volume_ml"],
            pack_count=row["pack_count"],
            abv_percent=row["abv_percent"],
            category=row["category"],
            is_sugar_free=row["is_sugar_free"],
        )
        if cid:
            batch.append((cid, row["id"]))

    # Batch update
    await conn.executemany(
        "UPDATE products SET canonical_product_id = $1 WHERE id = $2",
        batch,
    )

    # Check results
    stats = await conn.fetchrow("""
        SELECT COUNT(*) as total,
               COUNT(canonical_product_id) as with_canonical
        FROM products
    """)
    cross = await conn.fetchrow("""
        SELECT COUNT(DISTINCT cp) as cross_chain
        FROM (
            SELECT canonical_product_id as cp
            FROM products WHERE canonical_product_id IS NOT NULL
            GROUP BY canonical_product_id HAVING COUNT(DISTINCT chain) > 1
        ) m
    """)
    print(f"Done! {stats['with_canonical']}/{stats['total']} with canonical IDs, {cross['cross_chain']} cross-chain products")
    await conn.close()

asyncio.run(run())
