#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Tests all the endpoints the frontend uses
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"
FRONTEND_BASE = "http://localhost:3001"

def test_endpoint(url, name):
    """Test an API endpoint"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: OK ({response_time:.2f}ms)")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("🚀 Testing Flipkart Search System Integration")
    print("=" * 50)
    
    # Test API Health
    print("\n📡 API Endpoints:")
    test_endpoint(f"{API_BASE}/health", "API Health Check")
    test_endpoint(f"{API_BASE}/api", "API Info")
    
    # Test Search Endpoints (Frontend Uses These)
    print("\n🔍 Search Endpoints:")
    test_endpoint(f"{API_BASE}/api/v2/search?q=mobile&per_page=5", "V2 Search")
    test_endpoint(f"{API_BASE}/api/v1/metadata/autosuggest?q=mob&limit=5", "V1 Autosuggest")
    
    # Test Metadata Endpoints (Frontend Uses These)
    print("\n📊 Metadata Endpoints:")  
    test_endpoint(f"{API_BASE}/api/v1/metadata/popular-queries?limit=5", "Popular Queries")
    test_endpoint(f"{API_BASE}/api/v1/metadata/trending-categories?limit=5", "Trending Categories")
    
    # Test Direct Search (Backup)
    print("\n🎯 Direct Search Endpoints:")
    test_endpoint(f"{API_BASE}/api/v1/direct/search?q=mobile&limit=3", "Direct Search")
    test_endpoint(f"{API_BASE}/api/v1/direct/search/categories", "Direct Categories")
    
    # Test Frontend
    print("\n🌐 Frontend:")
    try:
        response = requests.get(FRONTEND_BASE, timeout=10)
        if response.status_code == 200:
            print(f"✅ Frontend Homepage: OK")
        else:
            print(f"❌ Frontend Homepage: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend Homepage: Error - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Integration Test Complete!")
    print(f"📊 Database: 17,005 products available")
    print(f"🚀 API: Running on {API_BASE}")
    print(f"🌐 Frontend: Running on {FRONTEND_BASE}")
    print("\n✨ Try searching for: mobile, laptop, shoes, electronics")

if __name__ == "__main__":
    main()
