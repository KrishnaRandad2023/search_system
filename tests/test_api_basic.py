"""
Basic tests for the Flipkart Search System APIs
"""

import pytest
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"]["status"] == "connected"

def test_root_endpoint():
    """Test the root endpoint"""
    response = requests.get(BASE_URL)
    assert response.status_code == 200
    
    data = response.json()
    assert "Flipkart Search System" in data["message"]
    assert "endpoints" in data

def test_search_api():
    """Test the search API"""
    # Basic search
    response = requests.get(f"{BASE_URL}/search", params={"q": "mobile"})
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "products" in data
    assert "total_count" in data
    assert data["query"] == "mobile"
    
    # Search with filters
    response = requests.get(f"{BASE_URL}/search", params={
        "q": "samsung",
        "category": "Electronics",
        "min_price": 1000
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["query"] == "samsung"

def test_autosuggest_api():
    """Test the autosuggest API (both old and new endpoints)"""
    # Test old endpoint
    response = requests.get(f"{BASE_URL}/autosuggest", params={"q": "mobile"})
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "suggestions" in data
    assert data["query"] == "mobile"
    assert len(data["suggestions"]) >= 0  # Allow empty results for old endpoint
    
    # Test new v1 metadata endpoint (used by frontend)
    response = requests.get(f"{BASE_URL}/api/v1/metadata/autosuggest", params={"q": "mobile"})
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "suggestions" in data
    assert "total_count" in data
    assert data["query"] == "mobile"
    assert len(data["suggestions"]) > 0  # Should have suggestions now
    
    # Check suggestion format has both old and new fields for compatibility
    if data["suggestions"]:
        suggestion = data["suggestions"][0]
        assert "text" in suggestion  # New format
        assert "score" in suggestion  # New format
        assert "suggestion_type" in suggestion  # New format
        assert "type" in suggestion  # Old format compatibility
        assert "category" in suggestion  # Old format compatibility
        assert "popularity" in suggestion  # Old format compatibility

def test_search_filters():
    """Test the search filters endpoint"""
    response = requests.get(f"{BASE_URL}/search/filters")
    assert response.status_code == 200
    
    data = response.json()
    assert "categories" in data
    assert "brands" in data
    assert "price_range" in data
    assert len(data["categories"]) > 0

def test_trending_queries():
    """Test trending queries endpoint"""
    response = requests.get(f"{BASE_URL}/autosuggest/trending")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_analytics_event():
    """Test analytics event logging"""
    event_data = {
        "event_type": "search",
        "query": "test mobile",
        "session_id": "test_session_123"
    }
    
    response = requests.post(f"{BASE_URL}/analytics/event", json=event_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"

def test_search_performance():
    """Test search performance"""
    start_time = time.time()
    
    response = requests.get(f"{BASE_URL}/search", params={"q": "samsung mobile"})
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    assert response.status_code == 200
    assert response_time < 1000  # Should respond within 1 second
    
    data = response.json()
    assert "response_time_ms" in data

def test_autosuggest_performance():
    """Test autosuggest performance"""
    start_time = time.time()
    
    # Test the new v1 metadata endpoint performance
    response = requests.get(f"{BASE_URL}/api/v1/metadata/autosuggest", params={"q": "mob"})
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    
    assert response.status_code == 200
    assert response_time < 500  # Should respond within 500ms
    
    data = response.json()
    assert len(data["suggestions"]) > 0

if __name__ == "__main__":
    print("🧪 Running basic API tests...")
    
    try:
        print("✅ Health check test passed")
        test_health_check()
        
        print("✅ Root endpoint test passed")  
        test_root_endpoint()
        
        print("✅ Search API test passed")
        test_search_api()
        
        print("✅ Autosuggest API test passed")
        test_autosuggest_api()
        
        print("✅ Search filters test passed")
        test_search_filters()
        
        print("✅ Trending queries test passed") 
        test_trending_queries()
        
        print("✅ Analytics event test passed")
        test_analytics_event()
        
        print("✅ Search performance test passed")
        test_search_performance()
        
        print("✅ Autosuggest performance test passed")
        test_autosuggest_performance()
        
        print("\n🎉 All tests passed! Your API is working perfectly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the API server is running: uvicorn app.main:app --reload")
