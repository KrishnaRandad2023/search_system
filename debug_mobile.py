#!/usr/bin/env python3
"""
Debug mobile suggestions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.autosuggest_service import get_trie_autosuggest
import json

def debug_mobile_suggestions():
    print("Debugging mobile suggestions...")
    
    service = get_trie_autosuggest()
    
    # Check if 'mobile' starts are in the Trie
    test_queries = [
        'mobile', 'mob', 'mo', 'm',
        'Mobile', 'MOBILE',
        'phone', 'smartphone', 'cell'
    ]
    
    for query in test_queries:
        results = service.get_suggestions(query, 10)
        print(f'"{query}": {len(results)} suggestions')
        for result in results[:3]:
            print(f"  - {result.text} (score: {result.score}, type: {result.suggestion_type})")
    
    # Check the products data to see if there are mobile-related products
    print("\nChecking products data...")
    products_file = "data/raw/products.json"
    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        mobile_products = []
        for product in products[:100]:  # Check first 100 products
            title = product.get('name', '') or product.get('title', '') or product.get('product_name', '')
            if title and 'mobile' in title.lower():
                mobile_products.append(title)
        
        print(f"Found {len(mobile_products)} products with 'mobile' in title (first 100 checked)")
        for title in mobile_products[:5]:
            print(f"  - {title}")
            
    except Exception as e:
        print(f"Error reading products: {e}")

if __name__ == "__main__":
    debug_mobile_suggestions()
