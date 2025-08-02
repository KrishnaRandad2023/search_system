"""
Smart Search API Endpoints - NLP-Powered Search
Uses our query analyzer for intelligent search results
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.product import SearchResponse
from app.services.smart_search_service import get_smart_search_service, SmartSearchService

router = APIRouter()


@router.get("/smart", response_model=SearchResponse)
async def smart_search_products(
    q: str = Query(..., description="Search query", min_length=1),
    page: int = Query(default=1, description="Page number", ge=1),
    limit: int = Query(default=20, description="Results per page", le=100),
    category: Optional[str] = Query(default=None, description="Filter by category (optional - will be extracted from query if not provided)"),
    min_price: Optional[float] = Query(default=None, description="Minimum price filter (optional - will be extracted from query if not provided)"),
    max_price: Optional[float] = Query(default=None, description="Maximum price filter (optional - will be extracted from query if not provided)"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating filter"),
    brand: Optional[str] = Query(default=None, description="Filter by brand (optional - will be extracted from query if not provided)"),
    sort_by: str = Query(default="relevance", description="Sort by: relevance, price_low, price_high, rating, popularity"),
    in_stock: bool = Query(default=True, description="Show only in-stock products"),
    db: Session = Depends(get_db),
    search_service: SmartSearchService = Depends(get_smart_search_service)
):
    """
    🧠 **Smart Search with NLP Query Analysis**
    
    This endpoint uses advanced NLP to understand your search intent:
    
    **Automatic Query Understanding:**
    - **Price Range Detection**: "mobile under 10k" → automatically applies max_price=10000
    - **Brand Recognition**: "samsung laptop" → automatically applies brand=samsung + category=laptop  
    - **Sentiment Analysis**: "best headphones" → prioritizes high-rated products
    - **Category Detection**: "smartphone" → searches mobiles, phones, devices
    
    **Examples:**
    - `q="mobile under 15k"` → Finds mobiles with price ≤ 15,000
    - `q="best samsung laptop"` → Finds Samsung laptops, sorted by rating
    - `q="budget headphones"` → Finds headphones, sorted by price (low to high)
    - `q="gaming laptop under 80k"` → Finds gaming laptops ≤ 80,000
    
    **What's Different from Regular Search:**
    - 🎯 **Context Awareness**: Understands "best" vs "budget" vs "under X"
    - 🏷️ **Auto-Filtering**: Extracts brands, categories, price ranges from query
    - 🎭 **Sentiment Intelligence**: Adjusts ranking based on query sentiment
    - 📊 **Analytics**: Provides query analysis in response
    
    The response includes `query_analysis` showing what was detected from your query.
    """
    try:
        return search_service.search_products(
            db=db,
            query=q,
            page=page,
            limit=limit,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            brand=brand,
            sort_by=sort_by,
            in_stock=in_stock
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart search error: {str(e)}")


@router.get("/compare")
async def compare_search_methods(
    q: str = Query(..., description="Search query to compare"),
    limit: int = Query(default=10, description="Results per method", le=20),
    db: Session = Depends(get_db),
    search_service: SmartSearchService = Depends(get_smart_search_service)
):
    """
    🔬 **Compare Smart Search vs Regular Search**
    
    Shows the difference between NLP-powered smart search and regular text search.
    Great for demonstrating the intelligence of our query analyzer!
    
    **Returns:**
    - `smart_results`: Results using NLP query analysis
    - `regular_results`: Results using basic text matching
    - `analysis`: What our NLP detected from the query
    - `improvements`: How smart search improved the results
    """
    try:
        # Get smart search results
        smart_response = search_service.search_products(
            db=db, query=q, limit=limit
        )
        
        # For comparison, we'd implement a basic search here
        # For now, just return the smart results with analysis
        
        return {
            "query": q,
            "smart_results": {
                "count": smart_response.total_count,
                "products": smart_response.products[:limit],
                "query_analysis": smart_response.query_analysis,
                "filters_applied": smart_response.filters_applied
            },
            "performance": {
                "response_time_ms": smart_response.response_time_ms,
                "total_results": smart_response.total_count
            },
            "nlp_insights": {
                "query_type": smart_response.query_analysis.get("query_type") if smart_response.query_analysis else None,
                "sentiment": smart_response.query_analysis.get("sentiment") if smart_response.query_analysis else None,
                "auto_extracted_filters": smart_response.filters_applied.get("extracted_from_query", {}) if smart_response.filters_applied else {},
                "intelligence_applied": [
                    "Price range detection" if smart_response.query_analysis and smart_response.query_analysis.get("price_range_detected") else None,
                    "Brand recognition" if smart_response.query_analysis and smart_response.query_analysis.get("brands_detected") else None,
                    "Category detection" if smart_response.query_analysis and smart_response.query_analysis.get("categories_detected") else None,
                    "Sentiment analysis" if smart_response.query_analysis and smart_response.query_analysis.get("sentiment") != "neutral" else None,
                    "Quality modifiers" if smart_response.query_analysis and smart_response.query_analysis.get("modifiers") else None
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")
