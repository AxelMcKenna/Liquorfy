"""
Capture network requests when loading Countdown stores.
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def capture_store_requests():
    """Intercept network requests to find store API."""

    api_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture all network requests
        async def handle_response(response):
            url = response.url
            # Look for API calls that might have store data
            if any(keyword in url.lower() for keyword in ['store', 'location', 'shop', 'api', 'fulfilment']):
                try:
                    if response.status == 200:
                        api_requests.append({
                            'url': url,
                            'status': response.status,
                            'method': response.request.method,
                            'type': response.request.resource_type
                        })
                        print(f"\n✓ Captured: {response.request.method} {url[:100]}...")

                        # Try to get response body if it's JSON
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            try:
                                body = await response.json()
                                print(f"  Response type: {type(body)}")
                                if isinstance(body, list):
                                    print(f"  Array with {len(body)} items")
                                    if body:
                                        print(f"  First item keys: {list(body[0].keys())[:10]}")
                                elif isinstance(body, dict):
                                    print(f"  Object keys: {list(body.keys())[:10]}")

                                # Save full response for inspection
                                api_requests[-1]['response'] = body
                            except:
                                pass
                except Exception as e:
                    print(f"Error handling response: {e}")

        page.on('response', handle_response)

        print("Loading store finder page...")
        await page.goto('https://www.woolworths.co.nz/store-finder', wait_until='domcontentloaded')
        await asyncio.sleep(3)

        print("\nPage loaded. Now triggering store search...")

        # Try to trigger the "Find stores near me" or search
        try:
            # Option 1: Click "Find stores near me" button
            near_me_button = page.locator('text=Find stores near me')
            if await near_me_button.count() > 0:
                print("Clicking 'Find stores near me'...")
                await near_me_button.click()
                await asyncio.sleep(5)
        except Exception as e:
            print(f"Near me button error: {e}")

        try:
            # Option 2: Search for a city
            search_input = page.locator('input[type="text"]').first
            if await search_input.count() > 0:
                print("\nSearching for 'Auckland'...")
                await search_input.fill("Auckland")
                await asyncio.sleep(2)

                # Press Enter or click search button
                await search_input.press('Enter')
                await asyncio.sleep(5)
        except Exception as e:
            print(f"Search error: {e}")

        print("\n" + "="*60)
        print(f"Captured {len(api_requests)} API requests")
        print("="*60)

        # Save captured requests
        if api_requests:
            output_file = '/Users/axelmckenna/Liquorfy/api/data/countdown_api_requests.json'
            with open(output_file, 'w') as f:
                json.dump(api_requests, f, indent=2)
            print(f"\nSaved API requests to: {output_file}")

            # Print summary
            print("\nAPI Endpoints found:")
            for i, req in enumerate(api_requests[:5], 1):
                print(f"\n{i}. {req['method']} {req['url'][:80]}...")
                if 'response' in req:
                    resp = req['response']
                    if isinstance(resp, list) and resp:
                        print(f"   → Array with {len(resp)} items")
                        print(f"   → Sample keys: {list(resp[0].keys())[:8]}")

        print("\n\nBrowser staying open for 30 seconds for inspection...")
        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_store_requests())
