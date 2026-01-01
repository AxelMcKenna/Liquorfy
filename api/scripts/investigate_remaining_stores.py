"""Investigate store locator pages for remaining chains."""
import asyncio
import json
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


CHAINS_TO_INVESTIGATE = [
    {
        "name": "Bottle O",
        "url": "https://shop.thebottleo.co.nz/change",
        "expected_keywords": ["store", "location", "shop"],
    },
    {
        "name": "Black Bull",
        "url": "https://blackbullliquor.co.nz/store-locator",
        "expected_keywords": ["store", "location"],
    },
    {
        "name": "Thirsty Liquor",
        "url": "https://thirstyliquor.co.nz",
        "expected_keywords": ["store", "location"],
    },
    {
        "name": "Liquor Centre",
        "url": "https://www.liquorcentre.co.nz",
        "expected_keywords": ["store", "location"],
    },
]


async def investigate_chain(chain_config: dict):
    """Investigate a chain's store locator to find API endpoints and data sources."""
    name = chain_config["name"]
    url = chain_config["url"]

    logger.info(f"\n{'='*60}")
    logger.info(f"Investigating {name}")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*60}")

    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept network requests
        def handle_request(request):
            url_lower = request.url.lower()
            if any(keyword in url_lower for keyword in chain_config["expected_keywords"]):
                if request.resource_type in ["xhr", "fetch"]:
                    logger.info(f"  📡 API Request: {request.method} {request.url}")
                    api_calls.append({
                        "method": request.method,
                        "url": request.url,
                        "type": request.resource_type
                    })

        def handle_response(response):
            url_lower = response.url.lower()
            if any(keyword in url_lower for keyword in chain_config["expected_keywords"]):
                if response.request.resource_type in ["xhr", "fetch"]:
                    logger.info(f"  ✅ API Response: {response.status} {response.url}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            # Navigate to page
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for dynamic content
            await page.wait_for_timeout(3000)

            # Check for window variables with store data
            window_vars = await page.evaluate("""() => {
                const vars = {};
                for (const key in window) {
                    const lowerKey = key.toLowerCase();
                    if ((lowerKey.includes('store') || lowerKey.includes('location') || lowerKey.includes('shop'))
                        && typeof window[key] === 'object' && window[key] !== null) {
                        try {
                            // Check if it's an array or object with data
                            if (Array.isArray(window[key]) && window[key].length > 0) {
                                vars[key] = {
                                    type: 'array',
                                    length: window[key].length,
                                    sample: window[key][0]
                                };
                            } else if (typeof window[key] === 'object') {
                                const keys = Object.keys(window[key]);
                                if (keys.length > 0 && keys.length < 1000) {
                                    vars[key] = {
                                        type: 'object',
                                        keys: keys.length,
                                        firstKey: keys[0],
                                        sample: window[key][keys[0]]
                                    };
                                }
                            }
                        } catch (e) {
                            // Skip if we can't serialize
                        }
                    }
                }
                return vars;
            }""")

            if window_vars:
                logger.info(f"\n  📦 Window variables with store data:")
                for key, value in window_vars.items():
                    logger.info(f"    - window.{key}: {value['type']} with {value.get('length', value.get('keys', 0))} items")
                    if 'sample' in value:
                        logger.info(f"      Sample: {json.dumps(value['sample'], indent=8)[:200]}")

            # Check for JSON in script tags
            script_data = await page.evaluate("""() => {
                const scripts = document.querySelectorAll('script');
                const results = [];
                for (const script of scripts) {
                    if (script.textContent) {
                        const text = script.textContent;
                        // Look for store/location arrays or objects
                        const patterns = [
                            /(?:var|let|const)\\s+(\\w*stores?\\w*)\\s*=\\s*\\[/i,
                            /(?:var|let|const)\\s+(\\w*locations?\\w*)\\s*=\\s*\\[/i,
                            /(?:var|let|const)\\s+(\\w*shops?\\w*)\\s*=\\s*\\[/i,
                        ];

                        for (const pattern of patterns) {
                            const match = text.match(pattern);
                            if (match) {
                                results.push({
                                    varName: match[1],
                                    hasData: true
                                });
                            }
                        }
                    }
                }
                return results;
            }""")

            if script_data:
                logger.info(f"\n  📜 Store data in script tags:")
                for item in script_data:
                    logger.info(f"    - Variable: {item['varName']}")

            # Check for store elements in DOM
            store_count = await page.evaluate("""() => {
                const selectors = [
                    '[data-store]',
                    '[data-location]',
                    '.store-item',
                    '.store-card',
                    '.location-item',
                    '.store',
                    '.location'
                ];

                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        return {selector, count: elements.length};
                    }
                }
                return null;
            }""")

            if store_count:
                logger.info(f"\n  🏪 Store elements in DOM:")
                logger.info(f"    - Selector: {store_count['selector']}")
                logger.info(f"    - Count: {store_count['count']}")

            logger.info(f"\n  📊 Summary for {name}:")
            logger.info(f"    - API calls intercepted: {len(api_calls)}")
            logger.info(f"    - Window variables: {len(window_vars)}")
            logger.info(f"    - Script variables: {len(script_data)}")
            logger.info(f"    - DOM elements: {store_count['count'] if store_count else 0}")

        except Exception as e:
            logger.error(f"  ❌ Error investigating {name}: {e}")

        finally:
            await browser.close()

    return {
        "name": name,
        "api_calls": api_calls,
        "window_vars": list(window_vars.keys()) if window_vars else [],
        "script_vars": [item['varName'] for item in script_data] if script_data else [],
        "dom_count": store_count['count'] if store_count else 0,
    }


async def main():
    """Investigate all chains."""
    logger.info("="*60)
    logger.info("INVESTIGATING STORE LOCATOR PAGES")
    logger.info("="*60)

    results = []
    for chain_config in CHAINS_TO_INVESTIGATE:
        result = await investigate_chain(chain_config)
        results.append(result)

    # Summary
    logger.info(f"\n\n{'='*60}")
    logger.info("INVESTIGATION SUMMARY")
    logger.info(f"{'='*60}\n")

    for result in results:
        logger.info(f"{result['name']}:")
        logger.info(f"  API calls: {len(result['api_calls'])}")
        if result['api_calls']:
            for call in result['api_calls']:
                logger.info(f"    - {call['method']} {call['url']}")
        logger.info(f"  Window vars: {', '.join(result['window_vars']) if result['window_vars'] else 'None'}")
        logger.info(f"  Script vars: {', '.join(result['script_vars']) if result['script_vars'] else 'None'}")
        logger.info(f"  DOM elements: {result['dom_count']}")
        logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
