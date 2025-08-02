#!/usr/bin/env python3
"""Debug the smart search API"""

import requests
import json

def test_smart_search():
    base_url = "http://localhost:8000"
    
    # Test mobile search
    print("Testing mobile search...")
    response = requests.get(f"{base_url}/search/smart?q=mobile&limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Total count: {data['total_count']}")
        print(f"Response time: {data['response_time_ms']}ms")
        print(f"Query analysis: {data['query_analysis']}")
        
        if data['products']:
            print("Products found:")
            for i, product in enumerate(data['products'], 1):
                print(f"  {i}. Product data: {json.dumps(product, indent=2)}")
        else:
            print("No products found")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test smartphone search
    print("Testing smartphone search...")
    response = requests.get(f"{base_url}/search/smart?q=smartphone&limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Total count: {data['total_count']}")
        print(f"Response time: {data['response_time_ms']}ms")
        print(f"Query analysis: {data['query_analysis']}")
        
        if data['products']:
            print("Products found:")
            for i, product in enumerate(data['products'], 1):
                print(f"  {i}. Product data: {json.dumps(product, indent=2)}")
        else:
            print("No products found")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_smart_search()
