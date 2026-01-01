"""Clean up duplicate stores and add unique constraint"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def cleanup():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy')

    async with engine.begin() as conn:
        print('\n' + '='*80)
        print('CLEANING UP DUPLICATE STORES')
        print('='*80)

        # Count before
        result = await conn.execute(text("SELECT COUNT(*) FROM stores WHERE chain = 'liquor_centre'"))
        before_count = result.scalar()
        print(f'\n📊 Before: {before_count:,} Liquor Centre stores')

        # Strategy: For each unique (chain, url) combination, keep the oldest record
        # and delete the rest, after updating all foreign key references

        print('\n🔍 Finding duplicates...')

        # Get unique stores (keep oldest)
        result = await conn.execute(text("""
            WITH ranked_stores AS (
                SELECT id, chain, url,
                       ROW_NUMBER() OVER (
                           PARTITION BY chain, url
                           ORDER BY created_at ASC
                       ) as rn
                FROM stores
                WHERE chain = 'liquor_centre'
            )
            SELECT
                (SELECT COUNT(*) FROM ranked_stores WHERE rn = 1) as stores_to_keep,
                (SELECT COUNT(*) FROM ranked_stores WHERE rn > 1) as stores_to_delete
        """))
        keep, delete = result.fetchone()
        print(f'  ✅ Stores to keep: {keep:,}')
        print(f'  ❌ Stores to delete: {delete:,}')

        print('\n🔄 Updating price references to point to canonical stores...')

        # Update prices to point to canonical store (oldest per chain+url)
        result = await conn.execute(text("""
            WITH canonical_stores AS (
                SELECT id, chain, url,
                       ROW_NUMBER() OVER (
                           PARTITION BY chain, url
                           ORDER BY created_at ASC
                       ) as rn
                FROM stores
                WHERE chain = 'liquor_centre'
            ),
            store_mapping AS (
                SELECT
                    d.id as duplicate_id,
                    c.id as canonical_id
                FROM stores d
                JOIN canonical_stores c ON d.chain = c.chain AND d.url = c.url AND c.rn = 1
                WHERE d.chain = 'liquor_centre'
            )
            UPDATE prices
            SET store_id = sm.canonical_id
            FROM store_mapping sm
            WHERE prices.store_id = sm.duplicate_id
        """))
        print(f'  ✅ Updated price references')

        print('\n🗑️  Deleting duplicate stores...')

        # Delete duplicate stores (keep oldest)
        result = await conn.execute(text("""
            WITH canonical_stores AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY chain, url
                           ORDER BY created_at ASC
                       ) as rn
                FROM stores
                WHERE chain = 'liquor_centre'
            )
            DELETE FROM stores
            WHERE id IN (
                SELECT id FROM canonical_stores WHERE rn > 1
            )
        """))

        print(f'  ✅ Deleted {delete:,} duplicate stores')

        # Count after
        result = await conn.execute(text("SELECT COUNT(*) FROM stores WHERE chain = 'liquor_centre'"))
        after_count = result.scalar()
        print(f'\n📊 After: {after_count:,} Liquor Centre stores')

        print('\n🔒 Adding unique constraint to prevent future duplicates...')

        # Add unique constraint on (chain, url)
        try:
            await conn.execute(text("""
                ALTER TABLE stores
                ADD CONSTRAINT stores_chain_url_unique UNIQUE (chain, url)
            """))
            print('  ✅ Unique constraint added: (chain, url)')
        except Exception as e:
            if 'already exists' in str(e):
                print('  ℹ️  Constraint already exists')
            else:
                print(f'  ⚠️  Could not add constraint: {e}')

        print('\n' + '='*80)
        print('✅ CLEANUP COMPLETE')
        print('='*80)
        print(f'\nRemoved {before_count - after_count:,} duplicate stores')
        print(f'Remaining: {after_count:,} unique stores')
        print('='*80 + '\n')

    await engine.dispose()

asyncio.run(cleanup())
