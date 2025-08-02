#!/usr/bin/env python3
"""
Frontend API Spell Correction Test
Tests spell correction functionality through the frontend API endpoint
"""

import requests
import json

def test_frontend_spell_correction():
    print("=" * 80)
    print("FRONTEND API SPELL CORRECTION TEST")
    print("=" * 80)
    
    api_url = "http://localhost:8000/api/v2/search"
    
    test_cases = [
        {"query": "shirts", "expected_correction": "shirt"},
        {"query": "samung", "expected_correction": "samsung"},
        {"query": "mobile", "expected_correction": None},  # Should not be corrected
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected_correction"]
        
        print(f"\n{i}. Testing '{query}':")
        print("-" * 40)
        
        try:
            response = requests.get(api_url, params={"q": query, "limit": 3}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_results", 0)
                
                # Extract spell correction info from nested search_metadata
                search_metadata = data.get("search_metadata", {})
                has_typo_correction = search_metadata.get("has_typo_correction", False)
                corrected_query = search_metadata.get("corrected_query")
                
                print(f"  Status: ✅ {response.status_code}")
                print(f"  Total Results: {total_count}")
                print(f"  Has Typo Correction: {has_typo_correction}")
                print(f"  Corrected Query: {corrected_query}")
                
                if expected:
                    if has_typo_correction and corrected_query == expected:
                        print(f"  ✅ PASS: Correctly corrected '{query}' → '{corrected_query}'")
                    else:
                        print(f"  ❌ FAIL: Expected '{expected}', got '{corrected_query}'")
                else:
                    if not has_typo_correction:
                        print(f"  ✅ PASS: No correction needed for '{query}'")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Got correction '{corrected_query}' for '{query}'")
                
                # Show sample products
                products = data.get("products", [])
                if products:
                    print(f"  Sample Products:")
                    for j, product in enumerate(products[:2], 1):
                        title = product.get("title", "No title")
                        print(f"    {j}. {title}")
                else:
                    print(f"  ❌ No products found")
                    
            else:
                print(f"  ❌ API Error: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_frontend_spell_correction()
