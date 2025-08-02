#!/usr/bin/env python3
"""Test corrected queries"""

import requests

def test_corrected_queries():
    queries = ["shirt", "samsung"]
    
    for query in queries:
        print(f"\nTesting '{query}' (corrected form):")
        print("-" * 40)
        
        response = requests.get(f'http://localhost:8000/api/v2/search?q={query}&per_page=5')
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['total_results']}")
            print(f"Search Type: {data['search_metadata']['search_type']}")
            
            if data['products']:
                print("Sample Products:")
                for i, product in enumerate(data['products'][:3], 1):
                    print(f"  {i}. {product['title']}")
            else:
                print("❌ NO RESULTS")
        else:
            print(f"❌ API Error: {response.status_code}")

if __name__ == "__main__":
    test_corrected_queries()
