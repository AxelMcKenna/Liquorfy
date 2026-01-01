"""Quick script to get store counts from database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from app.db.models import Store
from app.db.session import async_transaction


async def main():
    async with async_transaction() as session:
        result = await session.execute(
            select(Store.chain, func.count()).group_by(Store.chain).order_by(Store.chain)
        )
        counts = result.all()

    print('\nCurrent store counts in database:')
    print('-' * 40)
    total = 0
    for chain, count in counts:
        print(f'{chain:20} {count:>5}')
        total += count
    print('-' * 40)
    print(f'{"TOTAL":20} {total:>5}')


if __name__ == "__main__":
    asyncio.run(main())
