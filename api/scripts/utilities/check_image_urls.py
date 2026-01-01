"""Check image URL coverage and validity"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_images():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy')

    async with engine.begin() as conn:
        print('\n' + '='*80)
        print('IMAGE URL ANALYSIS')
        print('='*80)

        # Check image URL coverage by chain
        result = await conn.execute(text("""
            SELECT
                chain,
                COUNT(*) as total_products,
                COUNT(image_url) as products_with_images,
                COUNT(*) - COUNT(image_url) as products_without_images,
                ROUND(100.0 * COUNT(image_url) / COUNT(*), 2) as coverage_percent
            FROM products
            GROUP BY chain
            ORDER BY chain
        """))

        print('\n📊 Image Coverage by Chain:')
        print(f"{'Chain':<20} {'Total':<10} {'With Images':<15} {'Missing':<10} {'Coverage':<10}")
        print('-'*80)

        for chain, total, with_img, without_img, coverage in result.fetchall():
            print(f"{chain:<20} {total:<10} {with_img:<15} {without_img:<10} {coverage}%")

        # Sample Liquor Centre products with and without images
        print('\n' + '='*80)
        print('LIQUOR CENTRE - PRODUCTS WITHOUT IMAGES (Sample 10)')
        print('='*80)

        result = await conn.execute(text("""
            SELECT id, name, product_url, image_url
            FROM products
            WHERE chain = 'liquor_centre' AND image_url IS NULL
            LIMIT 10
        """))

        for id, name, product_url, image_url in result.fetchall():
            print(f'\n• {name}')
            print(f'  ID: {id}')
            print(f'  Product URL: {product_url}')
            print(f'  Image URL: {image_url or "❌ NULL"}')

        print('\n' + '='*80)
        print('LIQUOR CENTRE - PRODUCTS WITH IMAGES (Sample 5)')
        print('='*80)

        result = await conn.execute(text("""
            SELECT id, name, image_url
            FROM products
            WHERE chain = 'liquor_centre' AND image_url IS NOT NULL
            LIMIT 5
        """))

        for id, name, image_url in result.fetchall():
            print(f'\n• {name}')
            print(f'  ID: {id}')
            print(f'  Image URL: {image_url}')

        # Check image URL patterns
        print('\n' + '='*80)
        print('IMAGE URL PATTERNS')
        print('='*80)

        result = await conn.execute(text("""
            SELECT
                CASE
                    WHEN image_url LIKE 'http%' THEN 'Valid HTTP/HTTPS'
                    WHEN image_url LIKE '//%' THEN 'Protocol-relative'
                    WHEN image_url LIKE '/%' THEN 'Relative path'
                    WHEN image_url IS NULL THEN 'NULL'
                    ELSE 'Other'
                END as url_pattern,
                COUNT(*) as count
            FROM products
            WHERE chain = 'liquor_centre'
            GROUP BY url_pattern
            ORDER BY count DESC
        """))

        for pattern, count in result.fetchall():
            print(f"  • {pattern:<25} {count:>6} products")

    await engine.dispose()

asyncio.run(check_images())
