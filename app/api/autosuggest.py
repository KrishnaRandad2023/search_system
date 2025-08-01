"""
Autosuggest API Endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.database import get_db
from app.db.models import AutosuggestQuery, Product
from app.schemas.autosuggest import AutosuggestResponse, AutosuggestItem
from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=AutosuggestResponse)
async def get_autosuggest(
    q: str = Query(..., description="Search query prefix", min_length=1),
    limit: int = Query(default=10, description="Maximum number of suggestions", le=50),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Get autosuggest suggestions for a given query prefix
    
    Features:
    - Prefix matching on popular queries
    - Category filtering
    - Popularity-based ranking
    - Product title suggestions
    """
    try:
        suggestions = []
        query_lower = q.lower().strip()
        
        if len(query_lower) < 1:
            return AutosuggestResponse(
                query=q,
                suggestions=[],
                total_count=0,
                response_time_ms=0
            )
        
        # Method 1: Search in autosuggest queries table
        autosuggest_query = db.query(AutosuggestQuery).filter(
            AutosuggestQuery.query.ilike(f"%{query_lower}%")
        )
        
        if category:
            autosuggest_query = autosuggest_query.filter(
                AutosuggestQuery.category.ilike(f"%{category.lower()}%")
            )
        
        autosuggest_results = autosuggest_query.order_by(
            AutosuggestQuery.popularity.desc()
        ).limit(limit).all()
        
        # Convert to suggestions
        for result in autosuggest_results:
            suggestions.append(AutosuggestItem(
                text=result.query,
                type="query",
                category=result.category,
                popularity=result.popularity
            ))
        
        # Method 2: If we need more suggestions, search in product titles
        if len(suggestions) < limit:
            remaining_limit = limit - len(suggestions)
            
            # Search product titles for additional suggestions - Enhanced with correct schema
            product_query = db.query(Product).filter(
                or_(
                    Product.title.ilike(f"%{query_lower}%"),
                    Product.brand.ilike(f"%{query_lower}%"),
                    Product.category.ilike(f"%{query_lower}%")
                ),
                Product.is_available == True  # Enhanced: use correct column
            )
            
            if category:
                product_query = product_query.filter(
                    Product.category.ilike(f"%{category}%")
                )
            
            product_results = product_query.order_by(
                Product.rating.desc(),
                Product.num_ratings.desc()
            ).limit(remaining_limit).all()
            
            # Extract unique suggestions from product data
            seen_suggestions = {s.text.lower() for s in suggestions}
            
            for product in product_results:
                # Add brand suggestions
                if (product.brand.lower() not in seen_suggestions and 
                    query_lower in product.brand.lower()):
                    suggestions.append(AutosuggestItem(
                        text=product.brand,
                        type="brand",
                        category=product.category.lower(),
                        popularity=product.num_ratings
                    ))
                    seen_suggestions.add(product.brand.lower())
                
                # Add category suggestions
                if (product.category.lower() not in seen_suggestions and
                    query_lower in product.category.lower()):
                    suggestions.append(AutosuggestItem(
                        text=product.category,
                        type="category", 
                        category=product.category.lower(),
                        popularity=1000  # Default category popularity
                    ))
                    seen_suggestions.add(product.category.lower())
                
                # Add product-based query suggestions
                title_words = product.title.lower().split()
                for i in range(len(title_words)):
                    for j in range(i + 1, min(i + 4, len(title_words) + 1)):
                        phrase = " ".join(title_words[i:j])
                        if (len(phrase) > len(query_lower) and 
                            query_lower in phrase and 
                            phrase not in seen_suggestions):
                            suggestions.append(AutosuggestItem(
                                text=phrase,
                                type="product",
                                category=product.category.lower(),
                                popularity=product.num_ratings
                            ))
                            seen_suggestions.add(phrase)
                            break
                
                if len(suggestions) >= limit:
                    break
        
        # Sort by popularity and limit results
        suggestions.sort(key=lambda x: x.popularity, reverse=True)
        suggestions = suggestions[:limit]
        
        return AutosuggestResponse(
            query=q,
            suggestions=suggestions,
            total_count=len(suggestions),
            response_time_ms=0  # TODO: Add actual timing
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing autosuggest: {str(e)}")


@router.get("/trending", response_model=List[AutosuggestItem])
async def get_trending_queries(
    limit: int = Query(default=20, description="Number of trending queries", le=100),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get trending/popular search queries"""
    try:
        query = db.query(AutosuggestQuery)
        
        if category:
            query = query.filter(AutosuggestQuery.category.ilike(f"%{category.lower()}%"))
        
        trending = query.order_by(AutosuggestQuery.popularity.desc()).limit(limit).all()
        
        return [
            AutosuggestItem(
                text=item.query,
                type="trending",
                category=item.category,
                popularity=item.popularity
            )
            for item in trending
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending queries: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Get available categories for filtering"""
    try:
        categories = db.query(Product.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")
