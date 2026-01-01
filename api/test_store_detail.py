"""Test if CDX API has a detail endpoint for individual stores."""
import asyncio
import httpx
import json

async def test_detail_api():
    """Try to get detailed store info."""
    
    # Try different endpoints with store ID
    store_id = "9011"  # Paeroa Woolworths
    
    urls = [
        f"https://api.cdx.nz/site-location/api/v1/sites/{store_id}",
        f"https://api.cdx.nz/site-location/api/v1/stores/{store_id}",
        f"https://www.woolworths.co.nz/api/v1/stores/{store_id}",
        f"https://www.woolworths.co.nz/api/v1/fulfilment/stores/{store_id}",
    ]
    
    headers = {"accept": "application/json"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            print(f"\nTrying: {url}")
            try:
                response = await client.get(url, headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print("✓ Success!")
                    print(json.dumps(data, indent=2)[:800])
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(test_detail_api())
