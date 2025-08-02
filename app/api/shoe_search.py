"""
Enhanced shoe search implementation to fix the shoes search issue
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text

from app.db.database import get_db
from app.db.models import Product
from app.schemas.product import ProductResponse, SearchResponse
import time

router = APIRouter()

@router.get("/shoes", response_model=SearchResponse)
async def search_shoes(
    q: Optional[str] = Query(None, description="Search query for shoes"),
    page: int = Query(default=1, description="Page number", ge=1),
    limit: int = Query(default=20, description="Results per page", le=100),
    min_price: Optional[float] = Query(default=None, description="Minimum price filter"),
    max_price: Optional[float] = Query(default=None, description="Maximum price filter"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating filter"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    sort_by: str = Query(default="relevance", description="Sort by: relevance, price_low, price_high, rating"),
    db: Session = Depends(get_db)
):
    """
    Specialized endpoint for searching shoes and footwear products
    """
    start_time = time.time()
    
    try:
        # Base query to get all footwear products
        base_query = db.query(Product).filter(
            or_(
                Product.category.ilike("%footwear%"),
                Product.subcategory.ilike("%shoe%"),
                Product.title.ilike("%shoe%"),
                Product.description.ilike("%footwear%")
            )
        )
        
        # Apply search term if provided
        if q:
            q_lower = q.lower().strip()
            
            # Define search terms for better results
            search_terms = [q_lower]
            
            # Add common shoe related terms
            if q_lower in ["shoe", "shoes"]:
                search_terms.extend(["footwear", "sneaker", "loafer", "boot"])
            elif q_lower == "sneakers":
                search_terms.extend(["casual shoes", "sports shoes", "running shoes"])
            elif q_lower == "loafers":
                search_terms.extend(["formal shoes", "casual shoes"])
            elif q_lower == "boots":
                search_terms.extend(["winter boots", "leather boots", "casual boots"])
            
            # Create search conditions
            search_conditions = []
            for term in search_terms:
                search_conditions.extend([
                    Product.title.ilike(f"%{term}%"),
                    Product.description.ilike(f"%{term}%"),
                    Product.subcategory.ilike(f"%{term}%"),
                    Product.brand.ilike(f"%{term}%")
                ])
            
            # Apply search filter
            base_query = base_query.filter(or_(*search_conditions))
        
        # Apply additional filters
        if brand:
            base_query = base_query.filter(Product.brand.ilike(f"%{brand}%"))
        
        if min_price is not None:
            base_query = base_query.filter(Product.current_price >= min_price)
        
        if max_price is not None:
            base_query = base_query.filter(Product.current_price <= max_price)
        
        if min_rating is not None:
            base_query = base_query.filter(Product.rating >= min_rating)
        
        # Apply sorting
        if sort_by == "price_low":
            base_query = base_query.order_by(Product.current_price.asc())
        elif sort_by == "price_high":
            base_query = base_query.order_by(Product.current_price.desc())
        elif sort_by == "rating":
            base_query = base_query.order_by(Product.rating.desc(), Product.num_ratings.desc())
        else:  # relevance - default sorting
            base_query = base_query.order_by(
                Product.is_bestseller.desc(),
                Product.is_featured.desc(),
                Product.rating.desc(),
                Product.num_ratings.desc()
            )
        
        # Get total count and paginate
        total_count = base_query.count()
        offset = (page - 1) * limit
        products = base_query.offset(offset).limit(limit).all()
        
        # Convert to response format
        product_responses = [
            ProductResponse(
                product_id=product.product_id,
                title=product.title,
                description=product.description,
                category=product.category,
                subcategory=product.subcategory,
                brand=product.brand,
                price=product.current_price,
                original_price=product.original_price,
                discount_percentage=product.discount_percent,
                rating=product.rating,
                num_ratings=product.num_ratings,
                num_reviews=product.num_ratings,  # Use same as ratings
                stock=product.stock_quantity,
                is_bestseller=product.is_bestseller,
                is_new_arrival=product.is_featured,
                image_url=product.images
            )
            for product in products
        ]
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=q or "shoes",
            products=product_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=(total_count + limit - 1) // limit,
            response_time_ms=response_time_ms,
            has_typo_correction=False,
            corrected_query=None,
            filters_applied={
                "category": "Footwear",
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "sort_by": sort_by
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching shoes: {str(e)}")
