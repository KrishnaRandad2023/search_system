#!/usr/bin/env python3
"""
Test autosuggest service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.autosuggest_service import get_trie_autosuggest

def test_autosuggest():
    print("Testing autosuggest service...")
    
    # Create service
    service = get_trie_autosuggest()
    print(f"Service created: {service}")
    
    # Test different queries
    test_queries = ['mobile', 'phone', 'samsung', 'apple', 'electronics', 'laptop']
    
    for query in test_queries:
        try:
            results = service.get_suggestions(query, 5)
            print(f'Query "{query}": {len(results)} suggestions')
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result}")
        except Exception as e:
            print(f'Error for "{query}": {e}')
    
    # Check if Trie has any data
    print(f"\nTrie root children: {len(service.root.children)}")
    if service.root.children:
        print("First few letters in Trie:", list(service.root.children.keys())[:10])

if __name__ == "__main__":
    test_autosuggest()
