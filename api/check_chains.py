import asyncio
from sqlalchemy import select, func
from app.db.models import Store, Product
from app.db.session import async_transaction

async def check():
    async with async_transaction() as session:
        # Get chains with products but no stores
        result = await session.execute(
            select(Product.chain, func.count(Product.id.distinct()))
            .group_by(Product.chain)
        )
        products_by_chain = {chain: count for chain, count in result.all()}
        
        result = await session.execute(
            select(Store.chain, func.count(Store.id))
            .group_by(Store.chain)
        )
        stores_by_chain = {chain: count for chain, count in result.all()}
        
        print("\nChain Status:")
        print(f"{'Chain':<20} {'Products':<12} {'Stores':<12} Status")
        print("-" * 60)
        
        all_chains = set(products_by_chain.keys()) | set(stores_by_chain.keys())
        
        for chain in sorted(all_chains):
            prod_count = products_by_chain.get(chain, 0)
            store_count = stores_by_chain.get(chain, 0)
            
            if store_count == 0 and prod_count > 0:
                status = "⚠️  NEEDS STORES"
            elif store_count > 0 and prod_count == 0:
                status = "⚠️  Has stores, no products"
            elif store_count > 0 and prod_count > 0:
                status = "✓ Complete"
            else:
                status = "?"
                
            print(f"{chain:<20} {prod_count:<12} {store_count:<12} {status}")

asyncio.run(check())
