"""
Scrape all Countdown/Woolworths stores using the CDX API.
"""
import asyncio
import json
import logging
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


async def scrape_all_stores():
    """
    Scrape all Countdown/Woolworths stores from CDX API.

    Returns:
        List of store dicts
    """
    base_url = "https://api.cdx.nz/site-location/api/v1/sites/search"

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    all_stores = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try different approaches to get all stores

        # Approach 1: Empty or wildcard query
        for query in ["", " ", "*", "New Zealand", "NZ"]:
            try:
                logger.info(f"Trying query: '{query}'")
                response = await client.get(base_url, params={"q": query}, headers=headers)
                response.raise_for_status()
                data = response.json()
                items = data.get("items", [])

                logger.info(f"  → Got {len(items)} stores")

                for store in items:
                    store_id = store.get("id")
                    if store_id and store_id not in seen_ids:
                        all_stores.append(store)
                        seen_ids.add(store_id)

                # If we got results, check if this is all stores
                if len(items) > 100:
                    logger.info(f"✓ Found {len(items)} stores with query '{query}' - likely all stores!")
                    break

            except Exception as e:
                logger.warning(f"  Error with query '{query}': {e}")

        # Approach 2: If we don't have many stores yet, search by major regions
        if len(all_stores) < 50:
            logger.info("\nApproach 1 didn't get many stores. Trying region-based search...")

            regions = [
                "Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga",
                "Dunedin", "Palmerston North", "Napier", "Nelson", "Rotorua",
                "New Plymouth", "Whangarei", "Invercargill", "Whanganui", "Gisborne",
                "Hastings", "Porirua", "Upper Hutt", "Lower Hutt", "Kapiti",
                "Taupo", "Queenstown", "Timaru", "Oamaru", "Ashburton",
                "Blenheim", "Levin", "Masterton", "Tokoroa", "Cambridge",
                "Thames", "Whakatane", "Pukekohe", "Paraparaumu", "Waikanae",
                "Northland", "Bay of Plenty", "Waikato", "Hawke's Bay", "Taranaki",
                "Manawatu", "Wairarapa", "Canterbury", "Otago", "Southland",
                "West Coast"
            ]

            for region in regions:
                try:
                    logger.info(f"Searching: {region}")
                    response = await client.get(base_url, params={"q": region}, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    items = data.get("items", [])

                    new_stores = 0
                    for store in items:
                        store_id = store.get("id")
                        if store_id and store_id not in seen_ids:
                            all_stores.append(store)
                            seen_ids.add(store_id)
                            new_stores += 1

                    logger.info(f"  → {len(items)} results, {new_stores} new stores")
                    await asyncio.sleep(0.5)  # Be nice to the API

                except Exception as e:
                    logger.warning(f"  Error searching {region}: {e}")

    logger.info(f"\n✓ Total unique stores found: {len(all_stores)}")
    return all_stores


async def main():
    """Run the store scraper and save results."""
    logging.basicConfig(level=logging.INFO)

    stores = await scrape_all_stores()

    if stores:
        # Save to JSON
        output_path = Path(__file__).parent.parent / "data" / "countdown_stores.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(stores, f, indent=2)

        logger.info(f"\n✓ Saved {len(stores)} stores to {output_path}")

        # Print sample
        print("\nSample store:")
        print(json.dumps(stores[0], indent=2))

        # Print summary
        print(f"\nTotal stores: {len(stores)}")
        suburbs = set(s.get('suburb', '') for s in stores)
        print(f"Unique suburbs: {len(suburbs)}")

    else:
        logger.error("No stores found!")


if __name__ == "__main__":
    asyncio.run(main())
