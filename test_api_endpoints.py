#!/usr/bin/env python3
"""
Quick API Endpoint Test Script
Tests all the key endpoints that the frontend uses
"""

import requests
import json
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_endpoint(url, description):
    """Test a single endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"   URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - {response.status_code} ({response_time:.1f}ms)")
            
            # Print first few items for verification
            if isinstance(data, dict):
                if 'suggestions' in data:
                    print(f"   📝 Found {len(data['suggestions'])} suggestions")
                elif 'queries' in data:
                    print(f"   📝 Found {len(data['queries'])} queries: {[q['query'] for q in data['queries'][:3]]}")
                elif 'categories' in data:
                    print(f"   📝 Found {len(data['categories'])} categories: {[c['category'] for c in data['categories'][:3]]}")
                elif 'products' in data:
                    print(f"   📝 Found {len(data['products'])} products")
            
            return True
        else:
            print(f"   ❌ FAILED - {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   💥 ERROR - {str(e)}")
        return False

def main():
    print("🚀 Starting API Endpoint Tests for Flipkart Search System")
    print("=" * 60)
    
    # List of endpoints to test
    endpoints = [
        # Core functionality
        (f"{BASE_URL}/", "Health Check - Root"),
        (f"{BASE_URL}/health/", "Health Check - Detailed"),
        
        # Autosuggest endpoints
        (f"{BASE_URL}/api/v1/metadata/autosuggest?q=phone&limit=5", "Autosuggest - phone"),
        (f"{BASE_URL}/api/v1/metadata/autosuggest?q=laptop&limit=5", "Autosuggest - laptop"),
        
        # Popular queries
        (f"{BASE_URL}/api/v1/metadata/popular-queries?limit=6", "Popular Queries"),
        (f"{BASE_URL}/api/v1/metadata/trending-categories?limit=8", "Trending Categories"),
        
        # Search endpoints
        (f"{BASE_URL}/api/v2/search?q=smartphone&page=1&per_page=20", "Search v2 - smartphone"),
        (f"{BASE_URL}/api/v2/search?q=laptop&page=1&per_page=10&sort_by=relevance", "Search v2 - laptop with sorting"),
        
        # Other important endpoints
        (f"{BASE_URL}/search/?q=mobile", "Legacy Search - mobile"),
        (f"{BASE_URL}/autosuggest/?query=shoes", "Legacy Autosuggest - shoes"),
    ]
    
    # Run tests
    passed = 0
    total = len(endpoints)
    
    for url, description in endpoints:
        if test_endpoint(url, description):
            passed += 1
        time.sleep(0.1)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Frontend should work perfectly.")
    else:
        print(f"⚠️  {total - passed} endpoints failed. Check backend configuration.")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
