"""Investigate New World store locator to understand data structure."""
import asyncio
import json
from playwright.async_api import async_playwright

async def investigate_new_world():
    """Investigate New World store locator page."""
    print("=" * 80)
    print("Investigating New World Store Locator")
    print("=" * 80)
    print()

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Intercept network requests to find API calls
        api_calls = []

        async def handle_request(request):
            if 'api' in request.url.lower() or 'store' in request.url.lower():
                api_calls.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type
                })

        page.on('request', handle_request)

        print("Loading store locator page...")
        try:
            await page.goto('https://www.newworld.co.nz/shop/stores', timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for content to load

            print("✅ Page loaded")
            print()

            # Check for API calls
            if api_calls:
                print(f"Found {len(api_calls)} API/store-related requests:")
                for call in api_calls[:10]:  # Show first 10
                    print(f"  - {call['method']} {call['url']}")
                print()

            # Look for store data in page
            print("Checking page structure...")

            # Check for store list/dropdown
            store_selectors = await page.query_selector_all('[data-testid*="store"], .store-item, .store-list li')
            print(f"Found {len(store_selectors)} elements with store-related selectors")

            # Check for embedded JSON
            scripts = await page.query_selector_all('script')
            json_data_found = False
            for script in scripts:
                content = await script.inner_text()
                if 'store' in content.lower() and ('{' in content or '[' in content):
                    print("Found script with potential store data")
                    json_data_found = True
                    # Save first 500 chars for analysis
                    print(f"Sample: {content[:500]}...")
                    break

            if not json_data_found:
                print("No embedded JSON store data found in scripts")

            print()
            print("Page title:", await page.title())
            print()

            # Get page HTML to analyze structure
            html = await page.content()

            # Save for manual inspection
            with open('/Users/axelmckenna/Liquorfy/api/data/new_world_stores_page.html', 'w') as f:
                f.write(html)
            print("Saved page HTML to: data/new_world_stores_page.html")

            print()
            print("Waiting 10 seconds for you to inspect the page...")
            print("(Browser window will stay open)")
            await page.wait_for_timeout(10000)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            await browser.close()

    print()
    print("=" * 80)
    print("Investigation Summary")
    print("=" * 80)
    if api_calls:
        print(f"✅ Found {len(api_calls)} API calls - likely has API endpoint")
        print("Most promising endpoints:")
        for call in api_calls[:5]:
            print(f"  {call['url']}")
    else:
        print("⚠️  No obvious API calls detected")
        print("May need to scrape HTML directly or find hidden API")

if __name__ == "__main__":
    asyncio.run(investigate_new_world())
