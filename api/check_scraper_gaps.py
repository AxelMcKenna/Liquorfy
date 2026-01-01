import asyncio
import os
from pathlib import Path
from sqlalchemy import select, func
from app.db.models import Store
from app.db.session import async_transaction

async def check_gaps():
    # Get all store scraper files
    scraper_dir = Path("app/store_scrapers")
    scraper_files = [f.stem for f in scraper_dir.glob("*.py") 
                     if not f.stem.startswith("_") 
                     and f.stem not in ["base", "generic", "countdown_stores", "countdown_stores_simple", "countdown_stores_network", "countdown_stores_final"]]
    
    print("Store Scrapers Found:")
    print("-" * 60)
    for scraper in sorted(scraper_files):
        print(f"  • {scraper}")
    
    # Get chains in database
    async with async_transaction() as session:
        result = await session.execute(
            select(Store.chain, func.count(Store.id))
            .group_by(Store.chain)
        )
        db_chains = {chain: count for chain, count in result.all()}
    
    print("\n\nChains in Database:")
    print("-" * 60)
    for chain, count in sorted(db_chains.items()):
        print(f"  • {chain}: {count} stores")
    
    # Map scrapers to expected chain names
    scraper_to_chain = {
        "black_bull": "black_bull",
        "bottle_o": "bottle_o",
        "countdown": "countdown",
        "glengarry": "glengarry",
        "liquorland": "liquorland",
        "super_liquor": "super_liquor",
        "thirsty_liquor": "thirsty_liquor",
    }
    
    print("\n\nGap Analysis:")
    print("-" * 60)
    
    # Scrapers that haven't been run
    print("\n✗ Scrapers with NO stores in database:")
    for scraper, chain in scraper_to_chain.items():
        if chain not in db_chains or db_chains[chain] == 0:
            print(f"  • {scraper} → {chain}")
    
    # Chains with stores but no scraper
    print("\n⚠️  Chains with stores but no scraper file:")
    for chain in db_chains:
        if chain not in scraper_to_chain.values():
            print(f"  • {chain}: {db_chains[chain]} stores")

asyncio.run(check_gaps())
