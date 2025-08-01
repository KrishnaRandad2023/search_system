"""
Search API Endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.db.database import get_db
from app.db.models import Product, SearchLog
from app.schemas.product import ProductResponse, SearchResponse
from app.schemas.query import SearchFilters
from app.config.settings import get_settings
from app.utils.spell_checker import check_spelling

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., description="Search query", min_length=1),
    page: int = Query(default=1, description="Page number", ge=1),
    limit: int = Query(default=20, description="Results per page", le=100),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    min_price: Optional[float] = Query(default=None, description="Minimum price filter"),
    max_price: Optional[float] = Query(default=None, description="Maximum price filter"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating filter"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    sort_by: str = Query(default="relevance", description="Sort by: relevance, price_low, price_high, rating, popularity"),
    in_stock: bool = Query(default=True, description="Show only in-stock products"),
    db: Session = Depends(get_db)
):
    """
    Search for products with filters and sorting
    
    Features:
    - Full-text search across title, description, brand
    - Category, price, rating, brand filters
    - Multiple sorting options
    - Pagination support
    - Stock availability filtering
    """
    try:
        start_time = datetime.utcnow()
        
        # Apply spell correction to the query
        corrected_query, has_typo_correction = check_spelling(q)
        query_to_search = corrected_query if has_typo_correction else q
        query_lower = query_to_search.lower().strip()
        
        # Build base query
        base_query = db.query(Product).filter(Product.is_active == True)
        
        # Add stock filter
        if in_stock:
            base_query = base_query.filter(Product.stock > 0)
        
        # Text search
        search_conditions = [
            Product.title.ilike(f"%{query_lower}%"),
            Product.description.ilike(f"%{query_lower}%"),
            Product.brand.ilike(f"%{query_lower}%"),
            Product.category.ilike(f"%{query_lower}%"),
            Product.subcategory.ilike(f"%{query_lower}%"),
            Product.product_type.ilike(f"%{query_lower}%")
        ]
        
        # Apply text search
        search_query = base_query.filter(or_(*search_conditions))
        
        # Apply filters
        if category:
            search_query = search_query.filter(
                Product.category.ilike(f"%{category}%")
            )
        
        if brand:
            search_query = search_query.filter(
                Product.brand.ilike(f"%{brand}%")
            )
        
        if min_price is not None:
            search_query = search_query.filter(Product.price >= min_price)
        
        if max_price is not None:
            search_query = search_query.filter(Product.price <= max_price)
        
        if min_rating is not None:
            search_query = search_query.filter(Product.rating >= min_rating)
        
        # Apply sorting
        if sort_by == "price_low":
            search_query = search_query.order_by(Product.price.asc())
        elif sort_by == "price_high":
            search_query = search_query.order_by(Product.price.desc())
        elif sort_by == "rating":
            search_query = search_query.order_by(Product.rating.desc(), Product.num_ratings.desc())
        elif sort_by == "popularity":
            search_query = search_query.order_by(Product.num_ratings.desc(), Product.rating.desc())
        else:  # relevance
            # Simple relevance scoring based on title match priority
            search_query = search_query.order_by(
                Product.is_bestseller.desc(),
                Product.rating.desc(),
                Product.num_ratings.desc()
            )
        
        # Get total count for pagination
        total_count = search_query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        products = search_query.offset(offset).limit(limit).all()
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Log search query
        try:
            search_log = SearchLog(
                query=q,
                results_count=total_count,
                response_time_ms=response_time_ms
            )
            db.add(search_log)
            db.commit()
        except Exception as log_error:
            print(f"Warning: Could not log search query: {log_error}")
        
        # Convert to response format
        product_responses = [
            ProductResponse(
                product_id=product.product_id,
                title=product.title,
                description=product.description,
                category=product.category,
                subcategory=product.subcategory,
                brand=product.brand,
                price=product.price,
                original_price=product.original_price,
                discount_percentage=product.discount_percentage,
                rating=product.rating,
                num_ratings=product.num_ratings,
                num_reviews=product.num_reviews,
                stock=product.stock,
                is_bestseller=product.is_bestseller,
                is_new_arrival=product.is_new_arrival,
                image_url=product.image_url
            )
            for product in products
        ]
        
        return SearchResponse(
            query=q,  # Original query
            products=product_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=(total_count + limit - 1) // limit,
            response_time_ms=response_time_ms,
            has_typo_correction=has_typo_correction,
            corrected_query=corrected_query if has_typo_correction else None,
            filters_applied={
                "category": category,
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "sort_by": sort_by,
                "in_stock": in_stock
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")


@router.get("/similar/{product_id}", response_model=List[ProductResponse])
async def get_similar_products(
    product_id: str,
    limit: int = Query(default=10, description="Number of similar products", le=50),
    db: Session = Depends(get_db)
):
    """Get products similar to a given product"""
    try:
        # Get the source product
        source_product = db.query(Product).filter(
            Product.product_id == product_id,
            Product.is_active == True
        ).first()
        
        if not source_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Find similar products based on category, brand, and price range
        price_range = source_product.price * 0.3  # 30% price range
        
        similar_query = db.query(Product).filter(
            and_(
                Product.product_id != product_id,
                Product.is_active == True,
                Product.stock > 0,
                or_(
                    Product.category == source_product.category,
                    Product.brand == source_product.brand,
                    and_(
                        Product.price >= source_product.price - price_range,
                        Product.price <= source_product.price + price_range
                    )
                )
            )
        ).order_by(
            Product.rating.desc(),
            Product.num_ratings.desc()
        ).limit(limit)
        
        similar_products = similar_query.all()
        
        return [
            ProductResponse(
                product_id=product.product_id,
                title=product.title,
                description=product.description,
                category=product.category,
                subcategory=product.subcategory,
                brand=product.brand,
                price=product.price,
                original_price=product.original_price,
                discount_percentage=product.discount_percentage,
                rating=product.rating,
                num_ratings=product.num_ratings,
                num_reviews=product.num_reviews,
                stock=product.stock,
                is_bestseller=product.is_bestseller,
                is_new_arrival=product.is_new_arrival,
                image_url=product.image_url
            )
            for product in similar_products
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar products: {str(e)}")


@router.get("/filters", response_model=Dict[str, Any])
async def get_search_filters(
    q: Optional[str] = Query(default=None, description="Search query for context"),
    db: Session = Depends(get_db)
):
    """Get available filters for search results"""
    try:
        base_query = db.query(Product).filter(Product.is_active == True)
        
        # If query provided, filter based on it
        if q:
            # Apply spell correction to the filter query too
            corrected_q, _ = check_spelling(q)
            query_lower = corrected_q.lower().strip()
            search_conditions = [
                Product.title.ilike(f"%{query_lower}%"),
                Product.description.ilike(f"%{query_lower}%"),
                Product.brand.ilike(f"%{query_lower}%"),
                Product.category.ilike(f"%{query_lower}%")
            ]
            base_query = base_query.filter(or_(*search_conditions))
        
        # Get unique categories
        categories = db.query(Product.category).filter(
            Product.is_active == True
        ).distinct().all()
        
        # Get unique brands  
        brands = db.query(Product.brand).filter(
            Product.is_active == True
        ).distinct().all()
        
        # Get price range
        price_stats = db.query(
            func.min(Product.price),
            func.max(Product.price)
        ).filter(Product.is_active == True).first()
        
        # Get rating range
        rating_stats = db.query(
            func.min(Product.rating),
            func.max(Product.rating)
        ).filter(Product.is_active == True).first()
        
        return {
            "categories": [cat[0] for cat in categories if cat[0]],
            "brands": [brand[0] for brand in brands if brand[0]],
            "price_range": {
                "min": price_stats[0] if price_stats[0] else 0,
                "max": price_stats[1] if price_stats[1] else 100000
            },
            "rating_range": {
                "min": rating_stats[0] if rating_stats[0] else 0,
                "max": rating_stats[1] if rating_stats[1] else 5
            },
            "sort_options": [
                {"value": "relevance", "label": "Relevance"},
                {"value": "price_low", "label": "Price: Low to High"},
                {"value": "price_high", "label": "Price: High to Low"},
                {"value": "rating", "label": "Customer Rating"},
                {"value": "popularity", "label": "Popularity"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search filters: {str(e)}")
