import asyncio
import sys
import httpx

async def test_search_api():
    """Test the search API endpoint directly"""
    print("🔍 Testing Search API...")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test various search endpoints
    endpoints = [
        "/api/v2/search?q=smartphone",
        "/api/v2/search?q=laptop&category=Electronics",
        "/api/hybrid/search?q=headphones",
        "/api/v1/search?q=iphone"
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"\n📡 Testing endpoint: {url}")
                
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    
                    print(f"✅ Status: {response.status_code}, Found {len(products)} products")
                    
                    # Show a few results
                    for i, product in enumerate(products[:3], 1):
                        title = product.get("title", "Unknown")
                        price = product.get("price", product.get("current_price", "N/A"))
                        product_id = product.get("product_id", product.get("id", "N/A"))
                        print(f"  {i}. {title} (ID: {product_id}, Price: ₹{price})")
                else:
                    print(f"❌ Error: Status {response.status_code}")
                    print(f"  Response: {response.text}")
            
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
    
    print("\n🎉 API Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_search_api())
