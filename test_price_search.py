#!/usr/bin/env python3
"""Test price-based searches"""

import requests

def test_price_searches():
    queries = ["40k", "under 40k", "mobile under 40k", "40000", "price 40k"]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print('='*60)
        
        response = requests.get(f'http://localhost:8000/api/v2/search?q={query}&per_page=3')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['total_results']}")
            print(f"Search Type: {data['search_metadata']['search_type']}")
            
            if data['products']:
                print("\nTop 3 Products:")
                for i, product in enumerate(data['products'], 1):
                    print(f"  {i}. {product['title']}")
                    print(f"     Price: ₹{product['current_price']}")
                    print(f"     Category: {product['subcategory']}")
                    print()
            else:
                print("No products found!")
        else:
            print(f"Error: {response.text}")

    # Test the smart search endpoint too
    print(f"\n{'='*60}")
    print("Testing Smart Search Endpoint:")
    print('='*60)
    
    response = requests.get('http://localhost:8000/search/smart?q=mobile under 40k&limit=5')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Total Count: {data['total_count']}")
        print(f"Analysis: {data.get('query_analysis', {})}")
        
        if data['products']:
            print("\nSmart Search Results:")
            for i, product in enumerate(data['products'], 1):
                print(f"  {i}. {product['title']} - ₹{product['price']}")
        else:
            print("No products found!")

if __name__ == "__main__":
    test_price_searches()
