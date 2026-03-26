import asyncio
import asyncpg
import os

async def run():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])

    # Disable statement timeout
    await conn.execute("SET statement_timeout = '0'")
    await conn.execute("SET lock_timeout = '30s'")

    print("Adding column...")
    await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS canonical_product_id UUID")
    print("Column added!")

    print("Creating index...")
    await conn.execute("CREATE INDEX IF NOT EXISTS ix_product_canonical ON products (canonical_product_id) WHERE canonical_product_id IS NOT NULL")
    print("Index created!")

    print("Running backfill...")
    await conn.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
    """)

    # Backfill in batches by category to avoid long-running transactions
    categories = await conn.fetch("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")
    cat_list = [r['category'] for r in categories]

    total_updated = 0
    for cat in cat_list:
        result = await conn.execute("""
            UPDATE products
            SET canonical_product_id = uuid_generate_v5(
                'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
                LOWER(TRIM(brand)) || '|' || total_volume_ml::text || '|' || pack_count::text || '|' ||
                COALESCE(abv_percent::text, 'NO_ABV') || '|' || LOWER(TRIM(category)) || '|' || is_sugar_free::text
            )
            WHERE brand IS NOT NULL AND total_volume_ml IS NOT NULL AND pack_count IS NOT NULL
              AND canonical_product_id IS NULL AND category = $1
        """, cat)
        count = int(result.split()[-1])
        total_updated += count
        print(f"  {cat}: {count} updated")

    # Handle NULL category
    result = await conn.execute("""
        UPDATE products
        SET canonical_product_id = uuid_generate_v5(
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
            LOWER(TRIM(brand)) || '|' || total_volume_ml::text || '|' || pack_count::text || '|' ||
            COALESCE(abv_percent::text, 'NO_ABV') || '|' || 'NO_CAT' || '|' || is_sugar_free::text
        )
        WHERE brand IS NOT NULL AND total_volume_ml IS NOT NULL AND pack_count IS NOT NULL
          AND canonical_product_id IS NULL AND category IS NULL
    """)
    count = int(result.split()[-1])
    total_updated += count
    print(f"  (no category): {count} updated")

    row = await conn.fetchrow("SELECT COUNT(*) as total, COUNT(canonical_product_id) as filled FROM products")
    print(f"\nDone! {row['filled']}/{row['total']} products have canonical IDs ({total_updated} updated)")
    await conn.close()

asyncio.run(run())
