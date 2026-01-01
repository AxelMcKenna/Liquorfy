"""Debug script to inspect Bottle O page structure."""
import asyncio
from playwright.async_api import async_playwright


async def debug_bottle_o():
    """Inspect the Bottle O page to find correct selectors."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Loading Bottle O store finder...")
        await page.goto('https://shop.thebottleo.co.nz/change', wait_until='domcontentloaded')
        await asyncio.sleep(3)

        # Scroll down to trigger lazy loading
        print("Scrolling to load stores...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)

        # Get the page structure
        print("\n=== Inspecting Page Structure ===\n")

        # Try different selectors
        selectors_to_try = [
            'button',
            'a',
            '[role="button"]',
            'div[class*="store"]',
            'div[class*="Store"]',
            'li',
            'article',
        ]

        for selector in selectors_to_try:
            count = await page.locator(selector).count()
            print(f"{selector}: {count} elements")

        # Get a sample of the first few buttons/links
        print("\n=== Sample Store Elements ===\n")

        # Check buttons specifically (often used for store cards)
        buttons = await page.locator('button').all()
        print(f"\nFound {len(buttons)} buttons. Inspecting first 5...")

        for i, button in enumerate(buttons[:5]):
            try:
                text = await button.inner_text()
                html = await button.inner_html()
                print(f"\nButton {i+1}:")
                print(f"  Text (first 200 chars): {text[:200]}")
                print(f"  HTML (first 300 chars): {html[:300]}")
            except:
                continue

        # Try to extract store data using JavaScript
        print("\n=== Trying JavaScript Extraction ===\n")

        store_data = await page.evaluate("""() => {
            // Look for store elements in <a> tags
            const links = Array.from(document.querySelectorAll('a'));
            const stores = [];

            console.log('Total links:', links.length);

            // Sample the first 5 links to see structure
            const samples = links.slice(0, 5).map(l => ({
                text: (l.innerText || '').substring(0, 100),
                href: l.getAttribute('href'),
                classes: l.className
            }));

            console.log('Sample links:', samples);

            for (const link of links) {
                const text = link.innerText || '';

                // Look for store-like patterns (more lenient)
                if (text.includes('Open') || text.includes('Closed') ||
                    text.includes(' am') || text.includes(' pm') ||
                    (text.includes('Shop Now') && text.length > 30)) {
                    // Try to parse the text
                    const lines = text.split('\\n').filter(l => l.trim());

                    stores.push({
                        rawText: text.substring(0, 300),
                        lines: lines.slice(0, 10),
                        href: link.getAttribute('href'),
                        classes: link.className
                    });
                }
            }

            return {stores, samples};
        }""")

        print("\n=== Sample Links ===")
        import json
        print(json.dumps(store_data['samples'], indent=2))

        stores = store_data['stores']
        print(f"\nFound {len(stores)} potential store elements")

        if stores:
            print("\n=== First Store Element ===")
            print(json.dumps(stores[0], indent=2))

            if len(stores) > 1:
                print("\n=== Second Store Element ===")
                print(json.dumps(stores[1], indent=2))

        print("\n\nKeeping browser open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_bottle_o())
