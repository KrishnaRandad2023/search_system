"""
Tests for the Flipkart Search API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.api.search_api import app

client = TestClient(app)

# Mock the search engine and ML ranker
@pytest.fixture(autouse=True)
def mock_dependencies():
    # Create mock search results
    mock_results = [
        {
            'id': 'P001',
            'title': 'Red T-shirt',
            'description': 'Cotton red t-shirt with logo',
            'category': 'Fashion',
            'brand': 'BrandA',
            'price': 499.0,
            'rating': 4.2,
            'semantic_score': 0.85,
            'lexical_score': 0.75,
            'combined_score': 0.82,
            'position': 1,
            'match_type': 'hybrid'
        },
        {
            'id': 'P002',
            'title': 'Blue Jeans',
            'description': 'Classic blue denim jeans',
            'category': 'Fashion',
            'brand': 'BrandB',
            'price': 1299.0,
            'rating': 4.5,
            'semantic_score': 0.65,
            'lexical_score': 0.90,
            'combined_score': 0.73,
            'position': 2,
            'match_type': 'lexical'
        }
    ]
    
    # Mock search engine
    with patch('app.api.search_api.search_engine') as mock_search:
        mock_search.search.return_value = mock_results
        
        # Mock ML ranker
        with patch('app.api.search_api.ml_ranker') as mock_ml:
            mock_ml.is_trained = True
            mock_ml.rerank.return_value = mock_results
            
            # Mock autocomplete
            with patch('app.api.search_api.autocomplete') as mock_autocomplete:
                mock_autocomplete.search.return_value = ["red shirt", "red t-shirt"]
                
                yield

class TestSearchAPI:
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Flipkart Search API" in response.json()["name"]
    
    def test_search_endpoint(self):
        # Test basic search
        response = client.post(
            "/search",
            json={"query": "red shirt", "limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["query"] == "red shirt"
        assert "total_results" in data
        assert "results" in data
        assert len(data["results"]) > 0
        assert "session_id" in data
        assert "filters" in data
        assert "search_id" in data
        
        # Check result structure
        result = data["results"][0]
        assert "id" in result
        assert "title" in result
        assert "position" in result
        assert "relevance_score" in result
    
    def test_search_with_filters(self):
        # Test search with filters
        response = client.post(
            "/search",
            json={
                "query": "shirt",
                "limit": 10,
                "offset": 0,
                "filters": {
                    "brand": "BrandA",
                    "price_range": {"min": 100, "max": 1000}
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that filtering was applied
        assert len(data["results"]) > 0
    
    def test_empty_query(self):
        # Test empty query
        response = client.post(
            "/search",
            json={"query": "", "limit": 10, "offset": 0}
        )
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_autocomplete_endpoint(self):
        # Test autocomplete
        response = client.post(
            "/autocomplete",
            json={"prefix": "red", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["prefix"] == "red"
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        assert "time_ms" in data
        assert "session_id" in data
    
    def test_empty_prefix_autocomplete(self):
        # Test empty prefix
        response = client.post(
            "/autocomplete",
            json={"prefix": "", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty suggestions
        assert data["prefix"] == ""
        assert len(data["suggestions"]) == 0
    
    def test_metrics_endpoint(self):
        # Test metrics endpoint
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metrics structure
        assert "total_searches" in data
        assert "avg_latency" in data
        assert "success_rate" in data
        assert "top_queries" in data
        assert "zero_results" in data
        assert "active_sessions" in data
    
    def test_health_check(self):
        # Test health check endpoint
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check health data
        assert data["status"] == "healthy"
        assert "components" in data
        assert "timestamp" in data
