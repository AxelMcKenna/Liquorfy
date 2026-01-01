"""Scrape Liquor Centre stores from shop.liquor-centre.co.nz."""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def main():
    """Scrape all Liquor Centre stores."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to Liquor Centre store list...")
        await page.goto("https://shop.liquor-centre.co.nz/change", wait_until="networkidle")

        # Wait for store list to load
        await page.wait_for_timeout(3000)

        # Extract all store elements
        print("Extracting store data...")

        # Look for store links or elements
        stores = []

        # Try to find store elements - they might be in a list or grid
        store_elements = await page.query_selector_all('a[href*="/"], .store, [class*="store"]')

        print(f"Found {len(store_elements)} potential store elements")

        # Extract store data from links
        for elem in store_elements:
            try:
                href = await elem.get_attribute("href")
                text = await elem.inner_text()

                if href and text and len(text.strip()) > 0:
                    # Check if this looks like a store
                    if any(keyword in text.lower() for keyword in ['liquor', 'store', 'open', 'am', 'pm']) or \
                       (href and 'shop.liquor-centre.co.nz' in href):
                        stores.append({
                            "href": href,
                            "text": text.strip()
                        })
            except Exception as e:
                pass

        # Also try to get the page HTML and parse it
        html = await page.content()

        # Save raw data for inspection
        with open("/Users/axelmckenna/Liquorfy/api/data/liquor_centre_raw.html", "w") as f:
            f.write(html)

        print(f"\nExtracted {len(stores)} stores")
        print(f"Raw HTML saved to data/liquor_centre_raw.html")

        # Print first few stores
        for i, store in enumerate(stores[:10]):
            print(f"\n{i+1}. {store['text'][:100]}...")
            print(f"   URL: {store['href']}")

        # Save to JSON
        output_file = "/Users/axelmckenna/Liquorfy/api/data/liquor_centre_stores_scraped.json"
        with open(output_file, "w") as f:
            json.dump(stores, f, indent=2)

        print(f"\nStores saved to {output_file}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
