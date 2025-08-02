#!/usr/bin/env python3
"""Test spell correction and plural handling"""

import requests

def test_spell_correction():
    queries = [
        # Plural tests
        ("shirts", "should find t-shirts"),
        ("shirt", "singular form"),
        ("phones", "should find phone products"), 
        ("phone", "singular form"),
        ("laptops", "should find laptop products"),
        ("laptop", "singular form"),
        
        # Typo tests
        ("mobil", "typo for mobile"),
        ("mobile", "correct spelling"),
        ("samung", "typo for samsung"),
        ("samsung", "correct spelling"),
    ]
    
    print("="*80)
    print("SPELL CORRECTION & PLURAL HANDLING TEST")
    print("="*80)
    
    for query, description in queries:
        print(f"\nTesting: '{query}' ({description})")
        print("-" * 60)
        
        response = requests.get(f'http://localhost:8000/api/v2/search?q={query}&per_page=3')
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['total_results']}")
            print(f"Search Type: {data['search_metadata']['search_type']}")
            print(f"Has Typo Correction: {data['search_metadata'].get('has_typo_correction', False)}")
            print(f"Corrected Query: {data['search_metadata'].get('corrected_query', 'None')}")
            
            if data['products']:
                print("Sample Results:")
                for i, product in enumerate(data['products'][:2], 1):
                    print(f"  {i}. {product['title']}")
            else:
                print("❌ NO RESULTS FOUND")
        else:
            print(f"❌ API Error: {response.status_code}")

if __name__ == "__main__":
    test_spell_correction()
