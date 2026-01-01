"""
Script to investigate store locator APIs by intercepting network requests.
This will help us find the actual API endpoints each chain uses.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CHAINS_TO_INVESTIGATE = [
    {
        "name": "Super Liquor",
        "url": "https://www.superliquor.co.nz/storelocations",
        "expected_api_keywords": ["store", "location", "shop"]
    },
    {
        "name": "Liquorland",
        "url": "https://www.liquorland.co.nz/store-locations",
        "expected_api_keywords": ["store", "location", "shop"]
    },
    {
        "name": "Bottle O",
        "url": "https://www.thebottleo.co.nz/store-locator",
        "expected_api_keywords": ["store", "location", "shop"]
    },
    {
        "name": "Thirsty Liquor",
        "url": "https://thirstyliquor.co.nz/pages/store-locator",
        "expected_api_keywords": ["store", "location", "shop"]
    },
    {
        "name": "Black Bull",
        "url": "https://blackbullliquor.co.nz/Store-locator",
        "expected_api_keywords": ["store", "location", "shop"]
    },
]


async def investigate_chain(chain_config: dict):
    """Investigate a chain's store locator to find API endpoints."""
    name = chain_config["name"]
    url = chain_config["url"]

    logger.info(f"\n{'='*60}")
    logger.info(f"Investigating: {name}")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*60}")

    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept network requests
        def handle_request(request):
            # Look for API calls
            if any(keyword in request.url.lower() for keyword in chain_config["expected_api_keywords"]):
                if request.resource_type in ["xhr", "fetch"]:
                    logger.info(f"  API Request: {request.method} {request.url}")
                    api_calls.append({
                        "method": request.method,
                        "url": request.url,
                        "type": request.resource_type
                    })

        def handle_response(response):
            # Look for JSON responses with store data
            if response.request.resource_type in ["xhr", "fetch"]:
                if any(keyword in response.url.lower() for keyword in chain_config["expected_api_keywords"]):
                    logger.info(f"  API Response: {response.status} {response.url}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            # Navigate to page
            logger.info(f"Loading page...")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for any lazy-loaded content
            await page.wait_for_timeout(3000)

            # Try to trigger store loading (scroll, click buttons, etc.)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            # Look for store data in page content
            store_data = await page.evaluate("""() => {
                // Check common global variables
                const possibleVars = [
                    'storeData', 'stores', 'locations', 'storeLocations',
                    'allStores', 'storeList', 'storeInfo', 'shopData'
                ];

                for (const varName of possibleVars) {
                    if (window[varName]) {
                        return {
                            source: 'window.' + varName,
                            data: window[varName],
                            count: Array.isArray(window[varName]) ? window[varName].length :
                                   (typeof window[varName] === 'object' ? Object.keys(window[varName]).length : 1)
                        };
                    }
                }

                return null;
            }""")

            if store_data:
                logger.info(f"✓ Found store data in {store_data['source']}")
                logger.info(f"  Count: {store_data['count']} stores")

            logger.info(f"\nSummary for {name}:")
            logger.info(f"  API calls intercepted: {len(api_calls)}")
            if api_calls:
                logger.info(f"  Endpoints found:")
                for call in api_calls:
                    logger.info(f"    - {call['method']} {call['url']}")

        except Exception as e:
            logger.error(f"Error investigating {name}: {e}")

        finally:
            await browser.close()

    return {
        "chain": name,
        "url": url,
        "api_calls": api_calls,
        "store_data_found": store_data is not None
    }


async def main():
    """Investigate all chains."""
    logger.info("Starting store API investigation...")

    results = []

    for chain_config in CHAINS_TO_INVESTIGATE:
        result = await investigate_chain(chain_config)
        results.append(result)
        await asyncio.sleep(2)  # Rate limiting

    # Save results
    output_file = Path(__file__).parent.parent / "data" / "store_api_investigation.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"Investigation complete. Results saved to:")
    logger.info(f"  {output_file}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)
