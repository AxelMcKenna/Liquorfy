"""Debug script to investigate Thirsty Liquor store locator."""
import asyncio
import json
from playwright.async_api import async_playwright


async def main():
    """Debug Thirsty Liquor store locator."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # Navigate to store locator
        print("Navigating to store locator...")
        await page.goto("https://thirstyliquor.co.nz/pages/store-locator", wait_until="networkidle")

        # Wait a bit for any dynamic content
        await page.wait_for_timeout(5000)

        # Try to find window.storeData
        print("\nChecking for window.storeData...")
        store_data = await page.evaluate("() => window.storeData")
        if store_data:
            print(f"Found window.storeData: {len(store_data)} items")
            print(json.dumps(store_data, indent=2))
        else:
            print("window.storeData not found")

        # Check for any other potential data sources
        print("\nChecking for other data sources...")

        # Check for iframe with store locator
        iframes = page.frames
        print(f"Found {len(iframes)} frames")
        for i, frame in enumerate(iframes):
            print(f"Frame {i}: {frame.url}")

        # Check page content
        print("\nPage title:", await page.title())

        # Look for any elements with store information
        print("\nLooking for store-related elements...")
        store_elements = await page.query_selector_all('[class*="store"], [class*="location"], [id*="store"], [id*="location"]')
        print(f"Found {len(store_elements)} potential store elements")

        # Check for any maps or location widgets
        map_elements = await page.query_selector_all('[class*="map"], [id*="map"], iframe')
        print(f"Found {len(map_elements)} potential map elements")
        for elem in map_elements:
            tag = await elem.evaluate("el => el.tagName")
            if tag == "IFRAME":
                src = await elem.get_attribute("src")
                print(f"  iframe src: {src}")

        # Wait for user to inspect
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
