"""
Test script for the new specialized shoe search endpoint
"""

import requests
import json

def test_specialized_shoe_search():
    """Test the specialized shoe search endpoint"""
    
    print("\n🔍 TESTING SPECIALIZED SHOE SEARCH ENDPOINT")
    print("=" * 80)
    
    # Base URL for the search API
    base_url = "http://localhost:8000"
    
    # Test search endpoint with different queries
    search_queries = [
        None,  # Test with no query (should return all shoes)
        "shoes",
        "shoe",
        "sneakers",
        "loafers",
        "boots",
        "running shoes",
        "casual shoes",
        "formal shoes"
    ]
    
    for query in search_queries:
        # Build URL with query if provided
        if query:
            url = f"{base_url}/search/shoes?q={query}&limit=5"
            print(f"\nQuery: '{query}'")
        else:
            url = f"{base_url}/search/shoes?limit=5"
            print("\nNo query (all shoes)")
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_count", 0)
                products = data.get("products", [])
                
                if total_count > 0 and products:
                    print(f"✅ Found {total_count} results")
                    print(f"   First result: {products[0].get('title', 'Unknown')}")
                    
                    # Show the first 3 products for detailed analysis
                    if len(products) > 0:
                        print("\n   Sample products:")
                        for i, product in enumerate(products[:3], 1):
                            print(f"   {i}. {product.get('title', 'Unknown')} - {product.get('category', 'Unknown')}/{product.get('subcategory', 'Unknown')}")
                else:
                    print(f"❌ No results found (0 products)")
            else:
                print(f"❌ API Error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_specialized_shoe_search()
