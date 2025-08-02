#!/usr/bin/env python3
"""Test frontend API price search"""

import requests

def test_frontend_price_search():
    print("Testing Frontend API with Price Query...")
    response = requests.get('http://localhost:8000/api/v2/search?q=mobile under 40k&per_page=5')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Search Type: {data['search_metadata']['search_type']}")
        print(f"Total Results: {data['total_results']}")
        print("\nProducts found:")
        
        for i, product in enumerate(data['products'][:5], 1):
            price = product['current_price']
            price_status = "✅ UNDER 40k" if price <= 40000 else "❌ OVER 40k"
            print(f"  {i}. {product['title']}")
            print(f"     Price: ₹{price} {price_status}")
            print(f"     Category: {product['subcategory']}")
            print()
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_frontend_price_search()
