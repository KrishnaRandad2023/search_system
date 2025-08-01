"""
API Client for Frontend
Provides a unified interface for connecting to backend APIs
"""

from typing import Dict, List, Any, Optional
import httpx
import json
import asyncio
from fastapi import HTTPException

class ApiClient:
    """API Client for making requests to backend services"""
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        
    async def close(self):
        """Close the API client session"""
        await self.client.aclose()
        
    async def make_request(self, method: str, path: str, params: Dict = None, data: Dict = None):
        """Make an HTTP request to the API"""
        try:
            if method.lower() == "get":
                response = await self.client.get(path, params=params)
            elif method.lower() == "post":
                response = await self.client.post(path, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = {}
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
                
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"API Client Error: {str(e)}")
    
    # API Methods
    
    # Search API (v2)
    async def search(self, query: str, **kwargs):
        """Search products using the v2 search API"""
        params = {"q": query, **kwargs}
        return await self.make_request("get", "/api/v2/search", params=params)
        
    # Autosuggest API
    async def get_autosuggest(self, query: str, limit: int = 8):
        """Get autosuggest suggestions"""
        params = {"q": query, "limit": limit}
        return await self.make_request("get", "/autosuggest/", params=params)
        
    # Track click (v1 compatibility)
    async def track_click(self, query: str, product_id: str, position: int):
        """Track product click for analytics"""
        data = {"query": query, "product_id": product_id, "position": position, "timestamp": None}
        return await self.make_request("post", "/api/v1/track-click", data=data)
        
    # Popular queries API
    async def get_popular_queries(self, limit: int = 6):
        """Get popular search queries"""
        params = {"limit": limit}
        return await self.make_request("get", "/api/v1/metadata/popular-queries", params=params)
        
    # Trending categories API
    async def get_trending_categories(self, limit: int = 8):
        """Get trending categories"""
        params = {"limit": limit}
        return await self.make_request("get", "/api/v1/metadata/trending-categories", params=params)
        
    # Categories API
    async def get_categories(self):
        """Get all available categories"""
        return await self.make_request("get", "/api/v1/metadata/categories")
        
# Create a singleton instance
api_client = ApiClient()

# Cleanup function for application shutdown
async def close_api_client():
    await api_client.close()
