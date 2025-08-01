"""
Direct Search API - Working search endpoint
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/direct", tags=["Direct Search"])

class DirectSearchProduct(BaseModel):
    """Direct search product response"""
    id: int
    product_id: str
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    current_price: float
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    rating: Optional[float] = None
    num_ratings: int = 0
    stock_quantity: int = 0
    is_available: bool = True
    is_bestseller: bool = False
    is_featured: bool = False
    images: Optional[str] = None

class DirectSearchResponse(BaseModel):
    """Direct search response"""
    products: List[DirectSearchProduct]
    total_count: int
    page_size: int
    offset: int
    query: str
    response_time_ms: float

@router.get("/search", response_model=DirectSearchResponse)
async def direct_search(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(default=20, description="Number of results", le=100, ge=1),
    page: int = Query(default=1, description="Page number", ge=1),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_rating: Optional[float] = Query(None, description="Minimum rating", ge=0, le=5),
    max_price: Optional[float] = Query(None, description="Maximum price", ge=0),
    in_stock: bool = Query(False, description="Only show in-stock items")
):
    """Direct search in database - bypasses SQLAlchemy issues"""
    
    try:
        start_time = datetime.utcnow()
        
        # Import the service
        from app.services.direct_search_service import get_direct_search_service
        search_service = get_direct_search_service()
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Perform search
        results = search_service.search_products(
            query=q,
            limit=limit,
            offset=offset,
            category=category,
            min_rating=min_rating,
            max_price=max_price,
            in_stock=in_stock
        )
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Convert products to response models
        products = [DirectSearchProduct(**product) for product in results["products"]]
        
        return DirectSearchResponse(
            products=products,
            total_count=results["total_count"],
            page_size=limit,
            offset=offset,
            query=q,
            response_time_ms=round(response_time_ms, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/search/categories")
async def get_categories() -> Dict[str, Any]:
    """Get available product categories"""
    
    try:
        from app.services.direct_search_service import get_direct_search_service
        search_service = get_direct_search_service()
        
        import sqlite3
        conn = sqlite3.connect(search_service.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM products 
            WHERE is_available = 1
            GROUP BY category
            ORDER BY count DESC
        """)
        
        categories = dict(cursor.fetchall())
        conn.close()
        
        return {
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Categories error: {str(e)}")

@router.get("/search/brands")
async def get_brands() -> Dict[str, Any]:
    """Get available product brands"""
    
    try:
        from app.services.direct_search_service import get_direct_search_service
        search_service = get_direct_search_service()
        
        import sqlite3
        conn = sqlite3.connect(search_service.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT brand, COUNT(*) as count
            FROM products 
            WHERE is_available = 1 AND brand IS NOT NULL
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 50
        """)
        
        brands = dict(cursor.fetchall())
        conn.close()
        
        return {
            "brands": brands,
            "total_brands": len(brands)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brands error: {str(e)}")
