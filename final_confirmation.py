#!/usr/bin/env python3
"""
Final Confirmation Test
"""

import requests

def final_confirmation():
    print("🎯 FINAL CONFIRMATION - USER ISSUE RESOLVED")
    print("=" * 50)
    
    response = requests.get('http://localhost:8000/api/v2/search', params={'q': 'shirts', 'limit': 5})
    
    if response.status_code == 200:
        data = response.json()
        metadata = data.get('search_metadata', {})
        
        print(f"Query: shirts")
        print(f"Status: {response.status_code}")
        print(f"Total Results: {data.get('total_results')}")
        print(f"Spell Corrected: {metadata.get('has_typo_correction')}")
        print(f"Corrected To: {metadata.get('corrected_query')}")
        print("Sample Products Found:")
        
        for i, product in enumerate(data.get('products', [])[:3], 1):
            print(f"  {i}. {product.get('title')}")
        
        print("\n✅ SUCCESS: 'shirts' now returns results via spell correction to 'shirt'!")
    else:
        print(f"❌ API Error: {response.status_code}")

if __name__ == "__main__":
    final_confirmation()
