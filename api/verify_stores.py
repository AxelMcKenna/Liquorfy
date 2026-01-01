import asyncio
from sqlalchemy import select, func
from app.db.models import Store
from app.db.session import async_transaction

async def verify():
    async with async_transaction() as session:
        # Count by chain
        result = await session.execute(
            select(Store.chain, func.count(Store.id)).group_by(Store.chain)
        )
        print("\nStores by chain:")
        for chain, count in result.all():
            print(f"  {chain}: {count}")
        
        # Sample Countdown stores
        result = await session.execute(
            select(Store).where(Store.chain == "countdown").limit(5)
        )
        print("\nSample Countdown stores:")
        for store in result.scalars():
            print(f"  {store.name} - {store.address}")

asyncio.run(verify())
