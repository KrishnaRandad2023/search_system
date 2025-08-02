#!/usr/bin/env python3
"""
Test Enhanced Universal Search Logic
"""

import requests

def test_universal_search():
    print("🧠 TESTING ENHANCED UNIVERSAL SEARCH LOGIC")
    print("=" * 60)
    
    test_cases = [
        "jeins for men",      # Typo + descriptive phrase
        "jeans for men",      # Correct + descriptive phrase  
        "samung phone",       # Brand typo + category
        "samsung mobile",     # Correct + category
        "shoen for women",    # Typo + gender
        "laptop computer",    # Category overlap
        "tshirts for kids",   # Product + demographic
        "moblie under 30000", # Typo + price constraint
    ]
    
    api_url = "http://localhost:8000/api/v2/search"
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 40)
        
        try:
            response = requests.get(api_url, params={"q": query, "limit": 5}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get('search_metadata', {})
                
                total_results = data.get('total_results', 0)
                has_typo_correction = metadata.get('has_typo_correction', False)
                corrected_query = metadata.get('corrected_query')
                
                print(f"  Results: {total_results}")
                print(f"  Spell Corrected: {has_typo_correction}")
                if corrected_query:
                    print(f"  Corrected To: '{corrected_query}'")
                
                if total_results > 0:
                    print(f"  ✅ SUCCESS - Found products!")
                    products = data.get('products', [])
                    for j, product in enumerate(products[:2], 1):
                        title = product.get('title', 'No title')
                        print(f"    {j}. {title}")
                else:
                    print(f"  ❌ FAILURE - No products found")
                    
            else:
                print(f"  ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("UNIVERSAL SEARCH TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_universal_search()
