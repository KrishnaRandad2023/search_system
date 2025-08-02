"""
Comprehensive test script for all product categories and search queries
"""

import requests
import json
import time

def test_comprehensive_search():
    """Test search functionality across all product categories"""
    
    print("\n🔍 COMPREHENSIVE SEARCH TEST")
    print("=" * 80)
    
    # Define search terms to try across all major categories
    search_terms = [
        # Electronics
        "smartphone", "mobile", "laptop", "computer", "headphones", "camera",
        # Clothing
        "shirt", "t-shirt", "jeans", "dress", "jacket",
        # Footwear
        "shoes", "footwear", "sneakers", "boots",
        # Home & Kitchen
        "kitchen", "furniture", "sofa", "bed", "table", "chair",
        # Beauty & Personal Care
        "beauty", "perfume", "makeup", "skincare",
        # Sports
        "sports", "fitness", "gym", "exercise",
        # Toys
        "toys", "games", "board games",
        # Books
        "books", "novels", "textbooks",
        # Grocery
        "grocery", "food", "snacks"
    ]
    
    # Base URL for the search API
    base_url = "http://localhost:8000"
    
    # Search endpoints to test
    endpoints = [
        "/search",  # Standard search
        "/search/shoes",  # Specialized shoe search
    ]
    
    results = {
        endpoint: {"success": 0, "failed": 0, "terms": []} for endpoint in endpoints
    }
    
    # Test each endpoint with each search term
    for endpoint in endpoints:
        print(f"\n🔍 Testing endpoint: {endpoint}")
        
        for term in search_terms:
            url = f"{base_url}{endpoint}?q={term}&limit=3"
            
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    total_count = data.get("total_count", 0)
                    
                    if total_count > 0:
                        results[endpoint]["success"] += 1
                        results[endpoint]["terms"].append(term)
                        print(f"✅ '{term}': {total_count} results")
                    else:
                        results[endpoint]["failed"] += 1
                        print(f"❌ '{term}': No results found")
                else:
                    results[endpoint]["failed"] += 1
                    print(f"❌ '{term}': API Error {response.status_code}")
            
            except Exception as e:
                results[endpoint]["failed"] += 1
                print(f"❌ '{term}': Error: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 SEARCH TEST SUMMARY")
    print("=" * 80)
    
    for endpoint, data in results.items():
        success_rate = (data["success"] / (data["success"] + data["failed"])) * 100
        print(f"\n{endpoint}:")
        print(f"  ✅ Successful queries: {data['success']}")
        print(f"  ❌ Failed queries: {data['failed']}")
        print(f"  📊 Success rate: {success_rate:.1f}%")
        
        if data["success"] > 0:
            print(f"  🔍 Sample successful terms: {', '.join(data['terms'][:5])}")
    
if __name__ == "__main__":
    test_comprehensive_search()
