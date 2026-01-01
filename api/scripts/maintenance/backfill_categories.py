"""Backfill missing categories for products with category: None"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.services.parser_utils import infer_category

async def backfill():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy')

    async with engine.begin() as conn:
        # Get products with NULL category
        result = await conn.execute(text("""
            SELECT id, name, category
            FROM products
            WHERE chain = 'liquor_centre' AND category IS NULL
        """))

        products = result.fetchall()

        print('\n' + '='*80)
        print('BACKFILLING MISSING CATEGORIES')
        print('='*80)
        print(f'\nFound {len(products):,} products with category: None')

        # Infer categories and update
        updated_count = 0
        still_null_count = 0

        for product_id, name, old_category in products:
            inferred = infer_category(name)

            if inferred:
                await conn.execute(text("""
                    UPDATE products
                    SET category = :category, updated_at = NOW()
                    WHERE id = :id
                """), {"category": inferred, "id": product_id})
                updated_count += 1
            else:
                still_null_count += 1

            # Progress indicator
            if (updated_count + still_null_count) % 500 == 0:
                print(f'  Processed {updated_count + still_null_count:,} / {len(products):,}...')

        # Get final count
        result = await conn.execute(text("""
            SELECT COUNT(*)
            FROM products
            WHERE chain = 'liquor_centre' AND category IS NULL
        """))
        final_null_count = result.scalar()

        # Get category distribution
        result = await conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM products
            WHERE chain = 'liquor_centre'
            GROUP BY category
            ORDER BY count DESC
            LIMIT 15
        """))

        categories = result.fetchall()

        print('\n' + '='*80)
        print('BACKFILL COMPLETE')
        print('='*80)
        print(f'\n✅ Updated: {updated_count:,} products')
        print(f'❌ Still NULL: {final_null_count:,} products')

        print('\n📊 Category Distribution (Top 15):')
        for cat, count in categories:
            cat_display = cat if cat else "None"
            print(f'  • {cat_display:<20} {count:>5,}')

        print('\n' + '='*80)

    await engine.dispose()

asyncio.run(backfill())
