"""Test if product detail pages have store data."""
import asyncio
import httpx
import json

async def test_product_detail():
    """Fetch a product detail to see if it has store availability."""
    
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0",
    }
    
    # Try product detail API
    urls = [
        "https://www.woolworths.co.nz/api/v1/products/5000213104101",  # Random SKU
        "https://www.woolworths.co.nz/api/v1/fulfilment/orders/products/5000213104101/stock",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            print(f"\nTrying: {url}")
            try:
                response = await client.get(url, headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(json.dumps(data, indent=2)[:1000])
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(test_product_detail())
