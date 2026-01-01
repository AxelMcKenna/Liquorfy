"""Test Countdown/Woolworths stores API."""
import asyncio
import httpx
import json

async def test_stores_api():
    """Try different stores API endpoints."""
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-NZ",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    endpoints = [
        "https://www.woolworths.co.nz/api/v1/fulfilment/stores",
        "https://www.woolworths.co.nz/api/v1/stores",
        "https://www.countdown.co.nz/api/v1/stores",
        "https://www.countdown.co.nz/api/stores",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in endpoints:
            print(f"\n{'='*60}")
            print(f"Testing: {url}")
            print('='*60)
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list):
                    print(f"✓ Got list with {len(data)} stores")
                    if data:
                        print(f"\nFirst store:")
                        print(json.dumps(data[0], indent=2))
                elif isinstance(data, dict):
                    print(f"✓ Got dict with keys: {list(data.keys())}")
                    print(json.dumps(data, indent=2)[:500])
                    
                return  # Success!
                
            except httpx.HTTPStatusError as e:
                print(f"✗ HTTP {e.response.status_code}")
            except Exception as e:
                print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_stores_api())
