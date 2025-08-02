#!/usr/bin/env python3
"""
Final Spell Correction Validation
"""

import requests

def final_validation():
    print("=== FINAL SPELL CORRECTION VALIDATION ===")
    
    test_cases = [
        ("iphone", None),      # Should not be corrected
        ("jeans", "jean"),     # Plural handling  
        ("watch", None),       # Should not be corrected
        ("watches", "watch"),  # Plural handling
        ("shoen", "shoe"),     # Typo correction
        ("laptops", "laptop"), # Plural handling
    ]
    
    for query, expected in test_cases:
        try:
            response = requests.get('http://localhost:8000/api/v2/search', params={'q': query, 'limit': 2})
            if response.status_code == 200:
                data = response.json()
                corrected = data.get('search_metadata', {}).get('corrected_query')
                actual = corrected or "No correction"
                expected_display = expected or "No correction"
                
                status = "✅" if actual == expected_display else "❌"
                print(f"{status} {query:12} -> {actual:15} (Expected: {expected_display})")
            else:
                print(f"❌ {query:12} -> API Error: {response.status_code}")
        except Exception as e:
            print(f"❌ {query:12} -> Error: {e}")

if __name__ == "__main__":
    final_validation()
