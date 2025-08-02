"""
Search Insights API Endpoints
Provides analysis of user search queries and analytics information
"""

from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.query_analyzer_service import get_query_analyzer, QueryAnalyzerService

router = APIRouter()


@router.get("/analyze")
async def analyze_search_query(
    q: str = Query(..., description="Search query to analyze"),
    db: Session = Depends(get_db),
    analyzer: QueryAnalyzerService = Depends(get_query_analyzer)
):
    """
    Analyze a search query and return insights
    Useful for debugging and understanding how the query analyzer works
    """
    try:
        # Analyze the query
        analysis = analyzer.analyze_query(q)
        
        # Convert to a dictionary for the API response
        result = {
            "query": analysis.original_query,
            "normalized_query": analysis.normalized_query,
            "query_type": analysis.query_type,
            "entities": analysis.entities,
            "confidence": analysis.confidence,
            "sentiment": analysis.sentiment,
        }
        
        # Add specific analyses
        if analysis.price_range:
            min_price, max_price = analysis.price_range
            result["price_range"] = {
                "min": min_price,
                "max": max_price,
                "formatted": f"₹{min_price if min_price else 0} - ₹{max_price if max_price else 'any'}"
            }
        
        if analysis.brands:
            result["brands"] = analysis.brands
            
        if analysis.categories:
            result["categories"] = analysis.categories
            
        if analysis.modifiers:
            result["modifiers"] = analysis.modifiers
        
        # Generate sample suggestions
        suggestions = analyzer.generate_suggestions(q, max_suggestions=5)
        result["suggested_queries"] = [s["text"] for s in suggestions]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing query: {str(e)}")


@router.get("/popular-patterns")
async def get_popular_search_patterns(
    limit: int = Query(default=10, description="Maximum number of patterns to return", le=50),
    db: Session = Depends(get_db)
):
    """
    Get popular search patterns based on user queries
    Shows common search patterns and what users are looking for
    """
    try:
        # Get QueryAnalyzerService instance
        analyzer = get_query_analyzer()
        analyzer.db = db  # Set the database after creation
        
        # Analyze actual queries from database to find real patterns
        patterns = []
        
        try:
            # Query the autosuggest table to analyze real user queries
            from app.db.models import AutosuggestQuery
            
            # Get top queries from database
            top_queries = db.query(AutosuggestQuery.query, AutosuggestQuery.popularity).order_by(
                AutosuggestQuery.popularity.desc()
            ).limit(50).all()
            
            # Analyze each query to categorize patterns
            pattern_stats = {
                "price_range": {"count": 0, "examples": []},
                "brand_category": {"count": 0, "examples": []},
                "modifier": {"count": 0, "examples": []},
                "feature_specific": {"count": 0, "examples": []},
                "general": {"count": 0, "examples": []}
            }
            
            total_queries = len(top_queries)
            
            for query_text, popularity in top_queries:
                if not query_text:
                    continue
                    
                # Analyze each query
                analysis = analyzer.analyze_query(query_text)
                
                # Categorize based on analysis
                if analysis.price_range:
                    pattern_stats["price_range"]["count"] += 1
                    if len(pattern_stats["price_range"]["examples"]) < 3:
                        pattern_stats["price_range"]["examples"].append(query_text)
                        
                elif analysis.query_type == "brand_category":
                    pattern_stats["brand_category"]["count"] += 1
                    if len(pattern_stats["brand_category"]["examples"]) < 3:
                        pattern_stats["brand_category"]["examples"].append(query_text)
                        
                elif analysis.modifiers:
                    pattern_stats["modifier"]["count"] += 1
                    if len(pattern_stats["modifier"]["examples"]) < 3:
                        pattern_stats["modifier"]["examples"].append(query_text)
                        
                elif any(feature in query_text.lower() for feature in ['5g', 'ram', 'storage', 'camera', 'battery']):
                    pattern_stats["feature_specific"]["count"] += 1
                    if len(pattern_stats["feature_specific"]["examples"]) < 3:
                        pattern_stats["feature_specific"]["examples"].append(query_text)
                        
                else:
                    pattern_stats["general"]["count"] += 1
                    if len(pattern_stats["general"]["examples"]) < 3:
                        pattern_stats["general"]["examples"].append(query_text)
            
            # Convert to API response format
            if total_queries > 0:
                patterns = [
                    {
                        "name": "Price Range Queries",
                        "description": "Queries that look for products in specific price ranges",
                        "examples": pattern_stats["price_range"]["examples"][:3],
                        "user_percentage": round((pattern_stats["price_range"]["count"] / total_queries) * 100, 1),
                        "query_count": pattern_stats["price_range"]["count"]
                    },
                    {
                        "name": "Brand + Category Queries", 
                        "description": "Queries that specify both brand and product category",
                        "examples": pattern_stats["brand_category"]["examples"][:3],
                        "user_percentage": round((pattern_stats["brand_category"]["count"] / total_queries) * 100, 1),
                        "query_count": pattern_stats["brand_category"]["count"]
                    },
                    {
                        "name": "Quality Modifier Queries",
                        "description": "Queries that include quality modifiers like 'best'",
                        "examples": pattern_stats["modifier"]["examples"][:3],
                        "user_percentage": round((pattern_stats["modifier"]["count"] / total_queries) * 100, 1),
                        "query_count": pattern_stats["modifier"]["count"]
                    },
                    {
                        "name": "Feature-specific Queries",
                        "description": "Queries that look for specific product features",
                        "examples": pattern_stats["feature_specific"]["examples"][:3],
                        "user_percentage": round((pattern_stats["feature_specific"]["count"] / total_queries) * 100, 1),
                        "query_count": pattern_stats["feature_specific"]["count"]
                    }
                ]
                
                # Sort by query count
                patterns.sort(key=lambda x: x["query_count"], reverse=True)
            
        except Exception as db_error:
            # Fallback to sample patterns if database query fails
            patterns = [
                {
                    "name": "Price Range Queries",
                    "description": "Queries that look for products in specific price ranges",
                    "examples": ["mobile under 10k", "laptop under 50k", "headphones under 2000"],
                    "user_percentage": 35,
                    "query_count": 0,
                    "note": f"Using sample data - DB error: {str(db_error)}"
                },
                {
                    "name": "Brand + Category Queries",
                    "description": "Queries that specify both brand and product category", 
                    "examples": ["samsung mobile", "apple iphone", "oneplus phone"],
                    "user_percentage": 28,
                    "query_count": 0,
                    "note": "Using sample data - DB error"
                }
            ]
        
        return {
            "total_patterns": len(patterns),
            "patterns": patterns[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting popular patterns: {str(e)}")
