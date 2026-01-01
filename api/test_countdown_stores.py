"""
Test script to inspect Countdown API responses for store data.
"""
import asyncio
import httpx
from urllib.parse import quote

async def test_countdown_api():
    """Fetch a sample product response to inspect for store data."""
    
    # Try the products API
    api_url = "https://www.woolworths.co.nz/api/v1/products"
    
    filters = [
        "Department;;beer-cider-wine;false",
        "Aisle;;beer;false",
    ]
    
    # Build URL
    url = api_url + "?"
    for f in filters:
        url += f"dasFilter={quote(f)}&"
    url += "target=browse&inStockProductsOnly=false&size=5"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-NZ",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    print("Testing products API...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Print structure
            print("\n=== API Response Structure ===")
            print(f"Top-level keys: {list(data.keys())}")
            
            if "products" in data:
                products = data["products"]
                print(f"\nProducts keys: {list(products.keys())}")
                
                items = products.get("items", [])
                if items:
                    print(f"\nFirst product keys: {list(items[0].keys())}")
                    
                    # Look for store-related fields
                    product = items[0]
                    for key in product.keys():
                        if any(s in key.lower() for s in ['store', 'location', 'stock', 'fulfil', 'availability']):
                            print(f"\n*** Store-related field found: {key} ***")
                            print(f"Value: {product[key]}")
            
            # Also try the stores API endpoint
            print("\n\n=== Testing Stores API ===")
            stores_url = "https://www.woolworths.co.nz/api/v1/fulfilment/stores"
            response = await client.get(stores_url, headers=headers)
            response.raise_for_status()
            stores_data = response.json()
            
            print(f"Stores API response keys: {list(stores_data.keys()) if isinstance(stores_data, dict) else 'List response'}")
            if isinstance(stores_data, list) and stores_data:
                print(f"First store keys: {list(stores_data[0].keys())}")
                print(f"\nFirst store sample:")
                import json
                print(json.dumps(stores_data[0], indent=2))
            elif isinstance(stores_data, dict):
                import json
                print(json.dumps(stores_data, indent=2))
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_countdown_api())
