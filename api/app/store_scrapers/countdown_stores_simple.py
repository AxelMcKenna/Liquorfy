"""
Simple scraper to inspect Countdown store locator page structure.
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def inspect_page():
    """Load the page and dump what we find."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Loading page...")
        await page.goto('https://www.woolworths.co.nz/store-finder', timeout=30000)

        await asyncio.sleep(5)

        print("\n" + "="*60)
        print("PAGE TITLE:", await page.title())
        print("PAGE URL:", page.url)
        print("="*60)

        # Get page HTML to inspect
        html = await page.content()
        print(f"\nPage HTML length: {len(html)} chars")

        # Look for store-related data
        print("\nSearching for store data...")

        # Check window object
        window_data = await page.evaluate('''() => {
            const keys = Object.keys(window).filter(k =>
                k.toLowerCase().includes('store') ||
                k.toLowerCase().includes('location') ||
                k.toLowerCase().includes('__')
            );
            return keys;
        }''')
        print(f"\nWindow keys with 'store/location/__': {window_data}")

        # Check for Next.js data
        next_data = await page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            if (el) return JSON.parse(el.textContent);
            return null;
        }''')

        if next_data:
            print("\n✓ Found __NEXT_DATA__!")
            print("Keys:", list(next_data.keys()) if isinstance(next_data, dict) else type(next_data))
            print(json.dumps(next_data, indent=2)[:1000])

        # Look for React/API data in scripts
        script_data = await page.evaluate('''() => {
            const scripts = Array.from(document.querySelectorAll('script'));
            const results = [];
            for (const script of scripts) {
                const text = script.textContent || '';
                if (text.includes('"stores"') || text.includes('"locations"') ||
                    text.includes('storeLocator') || text.includes('"address"')) {
                    results.push({
                        src: script.src || 'inline',
                        preview: text.substring(0, 200)
                    });
                }
            }
            return results;
        }''')

        if script_data:
            print(f"\n✓ Found {len(script_data)} scripts with store-related content:")
            for i, script in enumerate(script_data[:3]):
                print(f"\n  Script {i+1}:")
                print(f"    Src: {script['src']}")
                print(f"    Preview: {script['preview'][:150]}...")

        # Check page structure
        print("\nChecking page structure for store UI elements...")
        structure = await page.evaluate('''() => {
            return {
                hasInput: !!document.querySelector('input[type="text"], input[placeholder*="ubur"], input[placeholder*="ocation"]'),
                hasMap: !!document.querySelector('[class*="map"], #map, canvas'),
                hasStoreList: !!document.querySelector('[class*="store"], [class*="location"]'),
                bodyClasses: document.body.className,
                mainContent: document.body.textContent.substring(0, 500)
            };
        }''')

        print(json.dumps(structure, indent=2))

        # Keep browser open for manual inspection
        print("\n" + "="*60)
        print("Browser will stay open for 60 seconds.")
        print("Manually inspect the page to see how stores are loaded.")
        print("="*60)

        await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_page())
