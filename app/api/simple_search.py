"""
Simple Search API - Bypasses complex logic for testing
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.database import get_db
from app.db.models import Product

router = APIRouter()

@router.get("/simple-search")
async def simple_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, le=100, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Simple search that just works - for debugging"""
    try:
        # Simple text search across title, brand, category, description
        search_filter = or_(
            func.lower(Product.title).contains(func.lower(q)),
            func.lower(Product.brand).contains(func.lower(q)),
            func.lower(Product.category).contains(func.lower(q)),
            func.lower(Product.description).contains(func.lower(q))
        )
        
        # Get products
        products = (
            db.query(Product)
            .filter(search_filter)
            .filter(Product.is_in_stock == True)
            .order_by(Product.rating.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Get total count
        total = (
            db.query(Product)
            .filter(search_filter)  
            .filter(Product.is_in_stock == True)
            .count()
        )
        
        # Format results
        results = []
        for product in products:
            results.append({
                "id": product.id,
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "price": float(product.price) if product.price else 0.0,
                "original_price": float(product.original_price) if product.original_price else None,
                "rating": float(product.rating) if product.rating else 0.0,
                "review_count": product.review_count or 0,
                "description": product.description or "",
                "image_urls": product.image_urls or "[]",
                "seller_name": product.seller_name or "",
                "is_flipkart_assured": bool(product.is_flipkart_assured),
                "delivery_days": product.delivery_days or 5,
                "stock_quantity": product.stock_quantity or 0,
                "discount_percentage": product.discount_percentage or 0
            })
        
        return {
            "query": q,
            "products": results,
            "total": total,
            "page": (offset // limit) + 1,
            "per_page": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        return {
            "query": q,
            "products": [],
            "total": 0,
            "error": str(e)
        }
