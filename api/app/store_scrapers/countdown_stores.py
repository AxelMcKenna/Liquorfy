"""
Scrape Countdown/Woolworths store locations from their store locator.
"""
import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


async def scrape_countdown_stores():
    """
    Scrape all Countdown store locations from their store locator page.

    Returns:
        List of store dicts with name, address, lat, lng
    """
    stores = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            logger.info("Loading Countdown store locator...")

            # Try different URLs
            urls_to_try = [
                'https://www.woolworths.co.nz/store-locator',
                'https://www.countdown.co.nz/store-locator',
                'https://www.woolworths.co.nz/stores',
            ]

            loaded = False
            for url in urls_to_try:
                try:
                    logger.info(f"Trying {url}...")
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(3)

                    # Check if page loaded successfully
                    title = await page.title()
                    logger.info(f"Page loaded: {title}")
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {url}: {e}")
                    continue

            if not loaded:
                logger.error("Could not load store locator page")
                return stores

            # Wait for page to fully load
            await asyncio.sleep(5)

            # Try to find store data in page JavaScript/JSON
            # Option 1: Check for JSON in script tags
            store_data = await page.evaluate('''() => {
                // Look for store data in window object
                if (window.__STORE_DATA__) return window.__STORE_DATA__;
                if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
                if (window.stores) return window.stores;

                // Look for JSON in script tags
                const scripts = Array.from(document.querySelectorAll('script'));
                for (const script of scripts) {
                    const text = script.textContent;
                    if (text.includes('stores') || text.includes('location')) {
                        try {
                            // Try to extract JSON
                            const match = text.match(/(\[.*?\])/s) || text.match(/(\{.*?\})/s);
                            if (match) {
                                return JSON.parse(match[1]);
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                }

                return null;
            }''')

            if store_data:
                logger.info(f"Found store data in page JavaScript: {type(store_data)}")
                print("Store data keys:", list(store_data.keys()) if isinstance(store_data, dict) else "list")
                print("Sample:", json.dumps(store_data if isinstance(store_data, dict) else store_data[0] if store_data else {}, indent=2)[:500])

            # Option 2: Try to interact with store locator UI
            # Look for search input
            search_input = page.locator('input[type="text"], input[placeholder*="suburb"], input[placeholder*="location"]').first
            if await search_input.count() > 0:
                logger.info("Found search input, trying to trigger store list...")
                await search_input.fill("Auckland")
                await asyncio.sleep(2)

                # Try to extract stores from results
                stores_on_page = await page.evaluate('''() => {
                    const storeElements = document.querySelectorAll('[class*="store"], [class*="location"], [data-store]');
                    return Array.from(storeElements).map(el => ({
                        html: el.innerHTML,
                        text: el.textContent,
                        classes: el.className
                    })).slice(0, 5); // Just first 5 for inspection
                }''')

                print("\nStore elements found:", len(stores_on_page))
                if stores_on_page:
                    print("Sample store element:", stores_on_page[0])

            # Option 3: Check network requests for API calls
            logger.info("Checking network requests...")
            await page.reload(wait_until='networkidle')

            # Get all XHR/Fetch requests
            requests = []
            page.on('response', lambda response: requests.append({
                'url': response.url,
                'status': response.status
            }) if 'api' in response.url.lower() or 'store' in response.url.lower() else None)

            await asyncio.sleep(3)

            print("\nAPI requests found:")
            for req in requests[-10:]:  # Last 10
                print(f"  {req['status']} - {req['url']}")

            # Keep browser open for manual inspection
            logger.info("\nBrowser will stay open for 30 seconds for manual inspection...")
            logger.info("Check the page to see how stores are loaded")
            await asyncio.sleep(30)

        finally:
            await browser.close()

    return stores


async def main():
    """Run the store scraper."""
    logging.basicConfig(level=logging.INFO)

    stores = await scrape_countdown_stores()

    if stores:
        # Save to JSON
        output_path = Path(__file__).parent.parent / "data" / "countdown_stores.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(stores, f, indent=2)

        logger.info(f"Saved {len(stores)} stores to {output_path}")
    else:
        logger.warning("No stores found")


if __name__ == "__main__":
    asyncio.run(main())
