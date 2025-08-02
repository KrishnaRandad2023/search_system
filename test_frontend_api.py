#!/usr/bin/env python3
"""Test the frontend API endpoint"""

import requests

def test_frontend_api():
    print("Testing Frontend API...")
    response = requests.get('http://localhost:8000/api/v2/search?q=mobile&per_page=3')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Results: {data['total_results']}")
        print(f"Search Type: {data['search_metadata']['search_type']}")
        print("\nProducts found:")
        
        for i, product in enumerate(data['products'], 1):
            print(f"  {i}. {product['title']}")
            print(f"     Category: {product['subcategory']}")
            print(f"     Price: ₹{product['current_price']}")
            print(f"     Rating: {product['rating']}/5")
            print()
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_frontend_api()
