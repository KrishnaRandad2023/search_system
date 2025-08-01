"""
Complete Autosuggest and Analytics API
Provides all endpoints needed for the frontend
"""

from typing import List, Optional, Dict, Any
import time
import json
import os
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Response Models
class AutosuggestItem(BaseModel):
    text: str
    category: Optional[str] = None
    popularity_score: Optional[float] = None
    is_trending: Optional[bool] = False

class AutosuggestResponse(BaseModel):
    suggestions: List[AutosuggestItem]
    total_count: int
    response_time_ms: float

class PopularQueriesResponse(BaseModel):
    queries: List[str]

class TrendingCategoriesResponse(BaseModel):
    categories: List[Dict[str, Any]]

# Create router
router = APIRouter(prefix="/api/v1", tags=["autosuggest"])

# Mock data for demonstration
POPULAR_QUERIES = [
    "smartphone", "laptop", "headphones", "watch", "shoes", 
    "iphone", "samsung", "nike", "books", "tablet",
    "bluetooth headphones", "gaming laptop", "wireless mouse"
]

TRENDING_CATEGORIES = [
    {"category": "Electronics", "trend_score": 0.9},
    {"category": "Fashion", "trend_score": 0.8},
    {"category": "Home & Kitchen", "trend_score": 0.7},
    {"category": "Books", "trend_score": 0.6},
    {"category": "Sports", "trend_score": 0.85},
    {"category": "Beauty", "trend_score": 0.75},
    {"category": "Automotive", "trend_score": 0.5},
    {"category": "Grocery", "trend_score": 0.65},
]

# Load product data for suggestions
def load_product_data():
    """Load product data from JSON file"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "products.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading product data: {e}")
    return []

# Cache product data
PRODUCTS_DATA = load_product_data()

def get_suggestions_from_products(query: str, limit: int = 10) -> List[AutosuggestItem]:
    """Get suggestions from product data"""
    query_lower = query.lower().strip()
    suggestions = []
    
    # Search in product titles and categories
    for product in PRODUCTS_DATA:
        if len(suggestions) >= limit:
            break
            
        title = product.get('title', '').lower()
        category = product.get('category', '')
        brand = product.get('brand', '')
        
        # Check if query matches title, category, or brand
        if (query_lower in title or 
            query_lower in category.lower() or 
            query_lower in brand.lower()):
            
            # Extract meaningful suggestion
            suggestion_text = product.get('title', '')[:50]  # Limit length
            
            suggestions.append(AutosuggestItem(
                text=suggestion_text,
                category=category,
                popularity_score=product.get('rating', 0) * 0.2,  # Convert rating to score
                is_trending=product.get('rating', 0) > 4.0
            ))
    
    # Add query-based suggestions
    query_suggestions = [
        f"{query} online",
        f"{query} price",
        f"{query} review",
        f"best {query}",
        f"{query} buy"
    ]
    
    for suggestion in query_suggestions:
        if len(suggestions) >= limit:
            break
        suggestions.append(AutosuggestItem(
            text=suggestion,
            category="Search Suggestions",
            popularity_score=0.5,
            is_trending=False
        ))
    
    return suggestions[:limit]

@router.get("/autosuggest", response_model=AutosuggestResponse)
async def get_autosuggest(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(default=10, description="Number of suggestions", le=50)
) -> AutosuggestResponse:
    """
    Get autosuggest suggestions for a query
    """
    start_time = time.time()
    
    try:
        # Get suggestions from product data
        suggestions = get_suggestions_from_products(q, limit)
        
        # Add popular query matches
        query_lower = q.lower()
        for popular_query in POPULAR_QUERIES:
            if len(suggestions) >= limit:
                break
            if query_lower in popular_query.lower():
                suggestions.append(AutosuggestItem(
                    text=popular_query,
                    category="Popular",
                    popularity_score=0.8,
                    is_trending=True
                ))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.text.lower() not in seen:
                seen.add(suggestion.text.lower())
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= limit:
                    break
        
        response_time = (time.time() - start_time) * 1000
        
        return AutosuggestResponse(
            suggestions=unique_suggestions,
            total_count=len(unique_suggestions),
            response_time_ms=round(response_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.get("/popular-queries", response_model=PopularQueriesResponse)
async def get_popular_queries(
    limit: int = Query(default=10, description="Number of popular queries", le=50)
) -> PopularQueriesResponse:
    """
    Get popular search queries
    """
    try:
        return PopularQueriesResponse(
            queries=POPULAR_QUERIES[:limit]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting popular queries: {str(e)}")

@router.get("/trending-categories", response_model=TrendingCategoriesResponse)
async def get_trending_categories(
    limit: int = Query(default=10, description="Number of trending categories", le=50)
) -> TrendingCategoriesResponse:
    """
    Get trending product categories
    """
    try:
        return TrendingCategoriesResponse(
            categories=TRENDING_CATEGORIES[:limit]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending categories: {str(e)}")
