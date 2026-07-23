"""Check Liquor Centre scraping results"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_results():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy")

    async with engine.begin() as conn:
        # Total products
        result = await conn.execute(
            text("SELECT COUNT(*) FROM products WHERE chain = 'liquor_centre'")
        )
        total_products = result.scalar()

        # Total stores
        result = await conn.execute(
            text("SELECT COUNT(DISTINCT id) FROM stores WHERE chain = 'liquor_centre'")
        )
        total_stores = result.scalar()

        # Total prices
        result = await conn.execute(
            text("""
            SELECT COUNT(*)
            FROM prices p
            JOIN stores s ON p.store_id = s.id
            WHERE s.chain = 'liquor_centre'
        """)
        )
        total_prices = result.scalar()

        # Sample products
        result = await conn.execute(
            text("""
            SELECT name, category, brand
            FROM products
            WHERE chain = 'liquor_centre'
            LIMIT 5
        """)
        )
        sample_products = result.fetchall()

        # Products by category
        result = await conn.execute(
            text("""
            SELECT category, COUNT(*)
            FROM products
            WHERE chain = 'liquor_centre'
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        )
        categories = result.fetchall()

        print("\n" + "=" * 80)
        print("🍺 LIQUOR CENTRE SCRAPER - DATABASE RESULTS")
        print("=" * 80)
        print(f"\n📦 Total Products: {total_products:,}")
        print(f"🏪 Total Stores: {total_stores:,}")
        print(f"💰 Total Prices: {total_prices:,}")

        print("\n📊 Products by Category:")
        for cat, count in categories:
            print(f"  • {cat}: {count:,}")

        print("\n🔍 Sample Products:")
        for name, cat, brand in sample_products:
            print(f"  • {name}")
            print(f"    Brand: {brand}, Category: {cat}")

        print("=" * 80)

    await engine.dispose()


asyncio.run(check_results())
