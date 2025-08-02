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


def get_smart_suggestions(query: str) -> List[AutosuggestItem]:
    """Generate smart contextual suggestions based on query patterns"""
    suggestions = []
    query_lower = query.lower().strip()
    
    # Price-range suggestions for mobiles
    if any(word in query_lower for word in ['mobile', 'phone', 'smartphone']):
        price_patterns = [
            ("mobile under 10k", 5000),
            ("mobile under 15k", 4500), 
            ("mobile under 20k", 4000),
            ("mobile under 30k", 3500),
            ("best mobile under 10k", 3000),
            ("4g mobile under 10k", 2500)
        ]
        for pattern, popularity in price_patterns:
            if query_lower in pattern or pattern.startswith(query_lower):
                suggestions.append(AutosuggestItem(
                    text=pattern,
                    type="price_range",
                    category="electronics",
                    popularity=popularity
                ))
    
    # Laptop suggestions  
    if any(word in query_lower for word in ['laptop', 'computer']):
        laptop_patterns = [
            ("laptop under 50k", 4000),
            ("gaming laptop under 80k", 3500),
            ("laptop under 30k", 3000),
            ("best laptop under 50k", 2500),
            ("dell laptop under 40k", 2000)
        ]
        for pattern, popularity in laptop_patterns:
            if query_lower in pattern or pattern.startswith(query_lower):
                suggestions.append(AutosuggestItem(
                    text=pattern,
                    type="price_range", 
                    category="electronics",
                    popularity=popularity
                ))
    
    # Brand + category combinations
    if len(query_lower) >= 2:
        brand_category_patterns = [
            ("samsung mobile", 4000), ("apple iphone", 3800), 
            ("oneplus mobile", 3500), ("xiaomi mobile", 3200),
            ("hp laptop", 3000), ("dell laptop", 2800),
            ("lenovo laptop", 2600), ("asus laptop", 2400)
        ]
        for pattern, popularity in brand_category_patterns:
            if query_lower in pattern or pattern.startswith(query_lower):
                suggestions.append(AutosuggestItem(
                    text=pattern,
                    type="brand_category",
                    category="electronics", 
                    popularity=popularity
                ))
    
    return suggestions[:5]  # Return top 5 smart suggestions


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
    - Price-range aware suggestions (e.g., "mobile under 10k", "laptop under 50000")
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

        # Add smart contextual suggestions first (highest priority)
        smart_suggestions = get_smart_suggestions(q)
        suggestions.extend(smart_suggestions)

        # Enhanced: Add price-range suggestions for common queries
        price_suggestions = []
        if any(word in query_lower for word in ['mobile', 'phone', 'smartphone']):
            price_ranges = [
                "mobile under 10k", "mobile under 15k", "mobile under 20k", 
                "mobile under 30k", "mobile under 50k"
            ]
            for price_query in price_ranges:
                if query_lower in price_query and price_query not in [s.text.lower() for s in suggestions]:
                    price_suggestions.append(AutosuggestItem(
                        text=price_query,
                        type="price_range",
                        category="electronics",
                        popularity=5000
                    ))
        
        if any(word in query_lower for word in ['laptop', 'computer']):
            price_ranges = [
                "laptop under 30k", "laptop under 50k", "laptop under 70k", 
                "laptop under 1 lakh", "gaming laptop under 80k"
            ]
            for price_query in price_ranges:
                if query_lower in price_query and price_query not in [s.text.lower() for s in suggestions]:
                    price_suggestions.append(AutosuggestItem(
                        text=price_query,
                        type="price_range", 
                        category="electronics",
                        popularity=4000
                    ))

        # Add price suggestions to main suggestions
        suggestions.extend(price_suggestions[:2])  # Limit to top 2 price suggestions
        
        # Method 1: Search in autosuggest queries table (SAFE: only select existing columns)
        autosuggest_query = db.query(
            AutosuggestQuery.id,
            AutosuggestQuery.query, 
            AutosuggestQuery.popularity,
            AutosuggestQuery.category
        ).filter(
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
                # Get actual values from SQLAlchemy model
                brand_val = getattr(product, 'brand', None)
                category_val = getattr(product, 'category', None)
                title_val = getattr(product, 'title', None)
                num_ratings_val = getattr(product, 'num_ratings', 0)
                price_val = getattr(product, 'price', None)
                
                # Add brand suggestions
                if (brand_val and brand_val.lower() not in seen_suggestions and 
                    query_lower in brand_val.lower()):
                    suggestions.append(AutosuggestItem(
                        text=brand_val,
                        type="brand",
                        category=category_val.lower() if category_val else "general",
                        popularity=num_ratings_val or 0
                    ))
                    seen_suggestions.add(brand_val.lower())
                
                # Add category suggestions
                if (category_val and category_val.lower() not in seen_suggestions and
                    query_lower in category_val.lower()):
                    suggestions.append(AutosuggestItem(
                        text=category_val,
                        type="category", 
                        category=category_val.lower(),
                        popularity=1000  # Default category popularity
                    ))
                    seen_suggestions.add(category_val.lower())
                
                # Add enhanced product-based query suggestions with price context
                if title_val:
                    title_words = title_val.lower().split()
                    for i in range(len(title_words)):
                        for j in range(i + 1, min(i + 4, len(title_words) + 1)):
                            phrase = " ".join(title_words[i:j])
                            if (len(phrase) > len(query_lower) and 
                                query_lower in phrase and 
                                phrase not in seen_suggestions):
                                
                                # Enhanced: Add price context to popular categories
                                enhanced_phrase = phrase
                                if price_val and category_val:
                                    if any(cat in category_val.lower() for cat in ['mobile', 'phone']):
                                        if price_val < 10000:
                                            enhanced_phrase = f"{phrase} under 10k"
                                        elif price_val < 20000:
                                            enhanced_phrase = f"{phrase} under 20k"
                                    elif any(cat in category_val.lower() for cat in ['laptop', 'computer']):
                                        if price_val < 50000:
                                            enhanced_phrase = f"{phrase} under 50k"
                                
                                suggestions.append(AutosuggestItem(
                                    text=enhanced_phrase,
                                    type="product",
                                    category=category_val.lower() if category_val else "general",
                                    popularity=num_ratings_val or 0
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
        query = db.query(
            AutosuggestQuery.id,
            AutosuggestQuery.query,
            AutosuggestQuery.popularity, 
            AutosuggestQuery.category
        )
        
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
