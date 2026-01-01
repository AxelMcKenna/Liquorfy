"""Analyze current database state - products by chain and full schema"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def analyze():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy')

    async with engine.begin() as conn:
        print('\n' + '='*80)
        print('DATABASE STATE ANALYSIS')
        print('='*80)

        # Get all chains
        result = await conn.execute(text("""
            SELECT DISTINCT chain
            FROM products
            ORDER BY chain
        """))
        chains = [row[0] for row in result.fetchall()]

        print(f'\n📊 CHAINS IN DATABASE: {len(chains)}')
        print('-'*80)

        total_products = 0
        total_stores = 0
        total_prices = 0

        for chain in chains:
            # Products count
            result = await conn.execute(text(f"""
                SELECT COUNT(*) FROM products WHERE chain = '{chain}'
            """))
            product_count = result.scalar()

            # Stores count
            result = await conn.execute(text(f"""
                SELECT COUNT(*) FROM stores WHERE chain = '{chain}'
            """))
            store_count = result.scalar()

            # Prices count
            result = await conn.execute(text(f"""
                SELECT COUNT(*)
                FROM prices p
                JOIN stores s ON p.store_id = s.id
                WHERE s.chain = '{chain}'
            """))
            price_count = result.scalar()

            # Category breakdown (top 5)
            result = await conn.execute(text(f"""
                SELECT category, COUNT(*) as count
                FROM products
                WHERE chain = '{chain}'
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            """))
            categories = result.fetchall()

            total_products += product_count
            total_stores += store_count
            total_prices += price_count

            print(f'\n🏪 {chain.upper()}')
            print(f'  Products: {product_count:,}')
            print(f'  Stores:   {store_count:,}')
            print(f'  Prices:   {price_count:,}')
            if categories:
                print(f'  Top Categories:')
                for cat, count in categories[:3]:
                    cat_name = cat if cat else "None"
                    print(f'    • {cat_name}: {count:,}')

        print('\n' + '='*80)
        print(f'TOTALS ACROSS ALL CHAINS')
        print('='*80)
        print(f'  Total Products: {total_products:,}')
        print(f'  Total Stores:   {total_stores:,}')
        print(f'  Total Prices:   {total_prices:,}')

        # ===== DATABASE SCHEMA =====
        print('\n\n' + '='*80)
        print('DATABASE SCHEMA')
        print('='*80)

        # Get all tables
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]

        for table in tables:
            print(f'\n📋 TABLE: {table}')
            print('-'*80)

            # Get columns
            result = await conn.execute(text(f"""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()

            for col_name, data_type, max_len, nullable, default in columns:
                type_str = data_type
                if max_len:
                    type_str = f"{data_type}({max_len})"

                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""

                print(f'  {col_name:<30} {type_str:<25} {null_str}{default_str}')

            # Get constraints
            result = await conn.execute(text(f"""
                SELECT
                    constraint_name,
                    constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = '{table}'
                ORDER BY constraint_type, constraint_name
            """))

            constraints = result.fetchall()

            if constraints:
                print(f'\n  Constraints:')
                for const_name, const_type in constraints:
                    print(f'    • {const_type}: {const_name}')

            # Get indexes
            result = await conn.execute(text(f"""
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = '{table}'
                ORDER BY indexname
            """))

            indexes = result.fetchall()

            if indexes:
                print(f'\n  Indexes:')
                for idx_name, idx_def in indexes:
                    # Simplify the index definition for readability
                    if 'UNIQUE' in idx_def:
                        idx_type = 'UNIQUE'
                    elif 'btree' in idx_def:
                        idx_type = 'BTREE'
                    else:
                        idx_type = 'INDEX'
                    print(f'    • {idx_type}: {idx_name}')

        print('\n' + '='*80)

    await engine.dispose()

asyncio.run(analyze())
