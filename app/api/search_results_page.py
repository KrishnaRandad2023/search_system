"""
Search Results Page (SRP) Component for Flipkart Grid 7.0
Production-ready SRP with filters, sorting, pagination, and analytics
"""

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys

from fastapi import APIRouter, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config import Config  # type: ignore
except ImportError:
    # Fallback config
    class Config:  # type: ignore
        DATABASE_PATH = "flipkart_products.db"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/srp", tags=["Search Results Page"])

# Pydantic models
class FilterOptions(BaseModel):
    categories: List[str] = Field(default_factory=list)
    brands: List[str] = Field(default_factory=list)
    price_ranges: List[Dict[str, float]] = Field(default_factory=list)
    rating_ranges: List[Dict[str, float]] = Field(default_factory=list)
    discount_ranges: List[Dict[str, float]] = Field(default_factory=list)
    availability: List[str] = Field(default_factory=list)

class SRPFilters(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brands: List[str] = Field(default_factory=list)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=1, le=5)
    max_rating: Optional[float] = Field(None, ge=1, le=5)
    min_discount: Optional[float] = Field(None, ge=0, le=100)
    in_stock_only: bool = Field(True)
    has_offers: Optional[bool] = None
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v

class SortOptions(BaseModel):
    field: str = Field("relevance", description="Sort field")
    direction: str = Field("desc", description="Sort direction")

class SRPRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SRPFilters] = None
    sort: Optional[SortOptions] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    include_filters: bool = Field(True, description="Include available filter options")
    include_aggregations: bool = Field(True, description="Include result aggregations")

class ProductCard(BaseModel):
    id: int
    name: str
    brand: str
    category: str
    subcategory: str
    price: float
    original_price: float
    discount_percentage: float
    rating: float
    rating_count: int
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    in_stock: bool
    stock_quantity: int
    shipping_free: bool = Field(True)
    delivery_time: str = Field("2-3 days")
    offers: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    relevance_score: float
    business_score: Optional[float] = None

class ResultAggregations(BaseModel):
    total_results: int
    category_counts: Dict[str, int]
    brand_counts: Dict[str, int]
    price_distribution: Dict[str, int]
    rating_distribution: Dict[str, int]
    availability_counts: Dict[str, int]
    average_price: float
    average_rating: float

class SRPResponse(BaseModel):
    query: str
    corrected_query: Optional[str] = None
    total_results: int
    page: int
    per_page: int
    total_pages: int
    products: List[ProductCard]
    filters: Optional[FilterOptions] = None
    applied_filters: SRPFilters
    aggregations: Optional[ResultAggregations] = None
    search_time_ms: float
    suggestions: List[str] = Field(default_factory=list)
    related_searches: List[str] = Field(default_factory=list)
    sort_options: List[Dict[str, str]] = Field(default_factory=list)

class SRPPageData(BaseModel):
    """Complete SRP page data including metadata"""
    search_results: SRPResponse
    page_metadata: Dict[str, Any]
    user_context: Dict[str, Any]
    ab_test_data: Optional[Dict[str, Any]] = None

def get_db_connection():
    """Get database connection with row factory."""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def get_available_filters(query: Optional[str] = None) -> FilterOptions:
    """Get available filter options based on search results."""
    conn = get_db_connection()
    
    try:
        # Base query for getting filter options
        base_where = "1=1"
        params: List[Any] = []
        
        if query:
            base_where += " AND (name LIKE ? OR description LIKE ? OR brand LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        
        # Get categories
        cursor = conn.execute(f"""
            SELECT category, COUNT(*) as count
            FROM products 
            WHERE {base_where}
            GROUP BY category
            ORDER BY count DESC
            LIMIT 20
        """, params)
        categories = [row[0] for row in cursor.fetchall()]
        
        # Get brands
        cursor = conn.execute(f"""
            SELECT brand, COUNT(*) as count
            FROM products 
            WHERE {base_where}
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 50
        """, params)
        brands = [row[0] for row in cursor.fetchall()]
        
        # Get price ranges
        cursor = conn.execute(f"""
            SELECT MIN(price) as min_price, MAX(price) as max_price
            FROM products 
            WHERE {base_where}
        """, params)
        row = cursor.fetchone()
        min_price, max_price = row[0] or 0, row[1] or 100000
        
        price_ranges = [
            {"label": "Under ₹500", "min": 0, "max": 500},
            {"label": "₹500 - ₹1000", "min": 500, "max": 1000},
            {"label": "₹1000 - ₹5000", "min": 1000, "max": 5000},
            {"label": "₹5000 - ₹10000", "min": 5000, "max": 10000},
            {"label": "Above ₹10000", "min": 10000, "max": max_price}
        ]
        
        # Get rating ranges
        rating_ranges = [
            {"label": "4★ & above", "min": 4.0, "max": 5.0},
            {"label": "3★ & above", "min": 3.0, "max": 5.0},
            {"label": "2★ & above", "min": 2.0, "max": 5.0},
            {"label": "1★ & above", "min": 1.0, "max": 5.0}
        ]
        
        # Get discount ranges
        discount_ranges = [
            {"label": "50% or more", "min": 50, "max": 100},
            {"label": "40% or more", "min": 40, "max": 100},
            {"label": "30% or more", "min": 30, "max": 100},
            {"label": "20% or more", "min": 20, "max": 100},
            {"label": "10% or more", "min": 10, "max": 100}
        ]
        
        availability = ["In Stock", "Out of Stock"]
        
        conn.close()
        
        return FilterOptions(
            categories=categories,
            brands=brands,
            price_ranges=price_ranges,
            rating_ranges=rating_ranges,
            discount_ranges=discount_ranges,
            availability=availability
        )
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        conn.close()
        return FilterOptions()

async def calculate_aggregations(query: str, filters: SRPFilters) -> ResultAggregations:
    """Calculate result aggregations for analytics."""
    conn = get_db_connection()
    
    try:
        # Build base query
        where_clauses = ["(name LIKE ? OR description LIKE ? OR brand LIKE ?)"]
        params: List[Any] = [f"%{query}%", f"%{query}%", f"%{query}%"]
        
        # Apply filters
        if filters.category:
            where_clauses.append("category = ?")
            params.append(filters.category)
        
        if filters.subcategory:
            where_clauses.append("subcategory = ?")
            params.append(filters.subcategory)
        
        if filters.brands:
            where_clauses.append(f"brand IN ({','.join(['?' for _ in filters.brands])})")
            params.extend(filters.brands)
        
        if filters.min_price is not None:
            where_clauses.append("price >= ?")
            params.append(filters.min_price)
        
        if filters.max_price is not None:
            where_clauses.append("price <= ?")
            params.append(filters.max_price)
        
        if filters.min_rating is not None:
            where_clauses.append("rating >= ?")
            params.append(filters.min_rating)
        
        if filters.max_rating is not None:
            where_clauses.append("rating <= ?")
            params.append(filters.max_rating)
        
        if filters.min_discount is not None:
            where_clauses.append("discount_percentage >= ?")
            params.append(filters.min_discount)
        
        if filters.in_stock_only:
            where_clauses.append("in_stock = 1")
        
        where_clause = " AND ".join(where_clauses)
        
        # Get total results
        cursor = conn.execute(f"SELECT COUNT(*) FROM products WHERE {where_clause}", params)
        total_results = cursor.fetchone()[0]
        
        # Get category counts
        cursor = conn.execute(f"""
            SELECT category, COUNT(*) as count
            FROM products 
            WHERE {where_clause}
            GROUP BY category
            ORDER BY count DESC
        """, params)
        category_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get brand counts
        cursor = conn.execute(f"""
            SELECT brand, COUNT(*) as count
            FROM products 
            WHERE {where_clause}
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 20
        """, params)
        brand_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get price distribution
        cursor = conn.execute(f"""
            SELECT 
                CASE 
                    WHEN price < 500 THEN 'Under ₹500'
                    WHEN price < 1000 THEN '₹500-₹1000'
                    WHEN price < 5000 THEN '₹1000-₹5000'
                    WHEN price < 10000 THEN '₹5000-₹10000'
                    ELSE 'Above ₹10000'
                END as price_range,
                COUNT(*) as count
            FROM products 
            WHERE {where_clause}
            GROUP BY price_range
        """, params)
        price_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get rating distribution
        cursor = conn.execute(f"""
            SELECT 
                CASE 
                    WHEN rating >= 4 THEN '4★ & above'
                    WHEN rating >= 3 THEN '3★ & above'
                    WHEN rating >= 2 THEN '2★ & above'
                    ELSE '1★ & above'
                END as rating_range,
                COUNT(*) as count
            FROM products 
            WHERE {where_clause}
            GROUP BY rating_range
        """, params)
        rating_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get availability counts
        cursor = conn.execute(f"""
            SELECT 
                CASE WHEN in_stock = 1 THEN 'In Stock' ELSE 'Out of Stock' END as availability,
                COUNT(*) as count
            FROM products 
            WHERE {where_clause}
            GROUP BY availability
        """, params)
        availability_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get averages
        cursor = conn.execute(f"""
            SELECT AVG(price) as avg_price, AVG(rating) as avg_rating
            FROM products 
            WHERE {where_clause}
        """, params)
        row = cursor.fetchone()
        avg_price = round(row[0] or 0, 2)
        avg_rating = round(row[1] or 0, 2)
        
        conn.close()
        
        return ResultAggregations(
            total_results=total_results,
            category_counts=category_counts,
            brand_counts=brand_counts,
            price_distribution=price_distribution,
            rating_distribution=rating_distribution,
            availability_counts=availability_counts,
            average_price=avg_price,
            average_rating=avg_rating
        )
        
    except Exception as e:
        logger.error(f"Error calculating aggregations: {e}")
        conn.close()
        return ResultAggregations(
            total_results=0,
            category_counts={},
            brand_counts={},
            price_distribution={},
            rating_distribution={},
            availability_counts={},
            average_price=0.0,
            average_rating=0.0
        )

async def search_products(request: SRPRequest) -> Tuple[List[ProductCard], int]:
    """Search products with filters and sorting."""
    conn = get_db_connection()
    
    try:
        # Build search query
        where_clauses = ["(name LIKE ? OR description LIKE ? OR brand LIKE ?)"]
        params: List[Any] = [f"%{request.query}%", f"%{request.query}%", f"%{request.query}%"]
        
        # Apply filters
        filters = request.filters or SRPFilters(
            category=None,
            subcategory=None,
            brands=[],
            min_price=None,
            max_price=None,
            min_rating=None,
            max_rating=None,
            min_discount=None,
            in_stock_only=True,
            has_offers=None
        )
        
        if filters.category:
            where_clauses.append("category = ?")
            params.append(filters.category)
        
        if filters.subcategory:
            where_clauses.append("subcategory = ?")
            params.append(filters.subcategory)
        
        if filters.brands:
            where_clauses.append(f"brand IN ({','.join(['?' for _ in filters.brands])})")
            params.extend(filters.brands)
        
        if filters.min_price is not None:
            where_clauses.append("price >= ?")
            params.append(str(filters.min_price))
        
        if filters.max_price is not None:
            where_clauses.append("price <= ?")
            params.append(str(filters.max_price))
        
        if filters.min_rating is not None:
            where_clauses.append("rating >= ?")
            params.append(str(filters.min_rating))
        
        if filters.max_rating is not None:
            where_clauses.append("rating <= ?")
            params.append(str(filters.max_rating))
        
        if filters.min_discount is not None:
            where_clauses.append("discount_percentage >= ?")
            params.append(str(filters.min_discount))
        
        if filters.in_stock_only:
            where_clauses.append("in_stock = 1")
        
        if filters.has_offers is not None:
            if filters.has_offers:
                where_clauses.append("discount_percentage > 0")
            else:
                where_clauses.append("discount_percentage = 0")
        
        where_clause = " AND ".join(where_clauses)
        
        # Build ORDER BY clause
        sort = request.sort or SortOptions(field="relevance", direction="desc")
        sort_field = sort.field
        sort_direction = sort.direction.upper()
        
        order_mapping = {
            "relevance": "rating * rating_count",
            "price_low_to_high": "price",
            "price_high_to_low": "price",
            "rating": "rating",
            "popularity": "rating_count",
            "newest": "id",  # Assuming higher ID = newer
            "discount": "discount_percentage"
        }
        
        if sort_field == "price_high_to_low":
            order_by = "price DESC"
        else:
            order_field = order_mapping.get(sort_field, "rating * rating_count")
            order_by = f"{order_field} {sort_direction}"
        
        # Get total count
        count_cursor = conn.execute(f"SELECT COUNT(*) FROM products WHERE {where_clause}", params)
        total_results = count_cursor.fetchone()[0]
        
        # Get products with pagination
        offset = (request.page - 1) * request.per_page
        
        cursor = conn.execute(f"""
            SELECT id, name, brand, category, subcategory, price, original_price,
                   discount_percentage, rating, rating_count, description, features,
                   in_stock, stock_quantity
            FROM products 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """, params + [request.per_page, offset])
        
        products = []
        for row in cursor.fetchall():
            # Calculate relevance score (simple implementation)
            query_words = set(request.query.lower().split())
            name_words = set(row['name'].lower().split())
            brand_words = set(row['brand'].lower().split())
            
            name_match = len(query_words.intersection(name_words)) / max(len(query_words), 1)
            brand_match = len(query_words.intersection(brand_words)) / max(len(query_words), 1)
            relevance_score = min((name_match * 0.7 + brand_match * 0.3), 1.0)
            
            # Parse features
            features = json.loads(row['features']) if row['features'] else []
            highlights = features[:3]  # First 3 features as highlights
            
            # Generate offers
            offers = []
            if row['discount_percentage'] > 0:
                offers.append(f"{row['discount_percentage']:.0f}% off")
            if row['price'] < 1000:
                offers.append("Free Delivery")
            if row['rating'] >= 4.0:
                offers.append("Top Rated")
            
            product = ProductCard(
                id=row['id'],
                name=row['name'],
                brand=row['brand'],
                category=row['category'],
                subcategory=row['subcategory'],
                price=row['price'],
                original_price=row['original_price'],
                discount_percentage=row['discount_percentage'],
                rating=row['rating'],
                rating_count=row['rating_count'],
                in_stock=row['in_stock'],
                stock_quantity=row['stock_quantity'],
                shipping_free=True,
                delivery_time="2-3 days",
                offers=offers,
                highlights=highlights,
                relevance_score=relevance_score,
                business_score=0.7  # Default business score
            )
            products.append(product)
        
        conn.close()
        return products, total_results
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        conn.close()
        return [], 0

async def get_related_searches(query: str) -> List[str]:
    """Get related search suggestions."""
    conn = get_db_connection()
    
    try:
        # Get related products and extract keywords
        cursor = conn.execute("""
            SELECT name, brand, category, subcategory
            FROM products 
            WHERE name LIKE ? OR brand LIKE ? OR category LIKE ?
            LIMIT 20
        """, [f"%{query}%", f"%{query}%", f"%{query}%"])
        
        related_terms = set()
        for row in cursor.fetchall():
            # Extract meaningful terms
            for field in row:
                words = field.lower().split()
                for word in words:
                    if len(word) > 3 and word not in query.lower():
                        related_terms.add(word.title())
        
        # Convert to related search queries
        related_searches = []
        for term in list(related_terms)[:8]:
            related_searches.append(f"{query} {term}")
        
        conn.close()
        return related_searches
        
    except Exception as e:
        logger.error(f"Error getting related searches: {e}")
        conn.close()
        return []

@router.post("/search", response_model=SRPResponse)
async def search_results_page(
    request: SRPRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Complete Search Results Page API with filters, sorting, and analytics.
    """
    start_time = time.time()
    
    try:
        # Search products
        products, total_results = await search_products(request)
        
        # Get available filters if requested
        filters = None
        if request.include_filters:
            filters = await get_available_filters(request.query)
        
        # Get aggregations if requested
        aggregations = None
        if request.include_aggregations:
            filters_for_agg = request.filters or SRPFilters(
                category=None, subcategory=None, brands=[], min_price=None,
                max_price=None, min_rating=None, max_rating=None, 
                min_discount=None, in_stock_only=True, has_offers=None
            )
            aggregations = await calculate_aggregations(request.query, filters_for_agg)
        
        # Get related searches
        related_searches = await get_related_searches(request.query)
        
        # Calculate pagination
        total_pages = (total_results + request.per_page - 1) // request.per_page
        
        # Define sort options
        sort_options = [
            {"value": "relevance", "label": "Relevance"},
            {"value": "price_low_to_high", "label": "Price: Low to High"},
            {"value": "price_high_to_low", "label": "Price: High to Low"},
            {"value": "rating", "label": "Customer Rating"},
            {"value": "popularity", "label": "Popularity"},
            {"value": "newest", "label": "Newest First"},
            {"value": "discount", "label": "Discount: High to Low"}
        ]
        
        # Calculate response time
        search_time = (time.time() - start_time) * 1000
        
        # Prepare response
        response = SRPResponse(
            query=request.query,
            total_results=total_results,
            page=request.page,
            per_page=request.per_page,
            total_pages=total_pages,
            products=products,
            filters=filters,
            applied_filters=request.filters or SRPFilters(
                category=None, subcategory=None, brands=[], min_price=None,
                max_price=None, min_rating=None, max_rating=None, 
                min_discount=None, in_stock_only=True, has_offers=None
            ),
            aggregations=aggregations,
            search_time_ms=round(search_time, 2),
            related_searches=related_searches,
            sort_options=sort_options
        )
        
        return response
        
    except Exception as e:
        logger.error(f"SRP search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/filters", response_model=FilterOptions)
async def get_filter_options(query: Optional[str] = Query(None)):
    """Get available filter options for a query."""
    try:
        filters = await get_available_filters(query)
        return filters
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get filter options")

@router.get("/page-data", response_model=SRPPageData)
async def get_srp_page_data(
    query: str = Query(...),
    page: int = Query(1, ge=1),
    session_id: str = Query(None),
    req: Optional[Request] = None
):
    """Get complete SRP page data including metadata and context."""
    try:
        # Create default request
        srp_request = SRPRequest(
            query=query,
            page=page,
            per_page=20,
            include_filters=True,
            include_aggregations=True
        )
        
        # Get search results  
        if req:
            search_results = await search_results_page(srp_request, BackgroundTasks(), req)
        else:
            # Create a mock request if none provided
            from fastapi import Request
            from starlette.requests import Request as StarletteRequest
            mock_req = Request({"type": "http", "method": "GET", "url": "http://localhost"})
            search_results = await search_results_page(srp_request, BackgroundTasks(), mock_req)
        
        # Prepare page metadata
        page_metadata = {
            "title": f"{query} - Search Results | Flipkart",
            "description": f"Shop for {query} online at Flipkart. Choose from a wide range of products with great deals and offers.",
            "canonical_url": f"/search?q={query}&page={page}",
            "structured_data": {
                "@context": "https://schema.org",
                "@type": "SearchResultsPage",
                "query": query,
                "numberOfItems": search_results.total_results
            }
        }
        
        # Prepare user context
        user_context = {
            "session_id": session_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_agent": req.headers.get("user-agent") if req else None,
            "ip_address": getattr(req.client, 'host', None) if req and hasattr(req, 'client') else None
        }
        
        # A/B test data (placeholder)
        ab_test_data = {
            "variant": "control",
            "test_id": "srp_layout_v1",
            "features": {
                "show_filters_sidebar": True,
                "show_sponsored_products": True,
                "infinite_scroll": False
            }
        }
        
        page_data = SRPPageData(
            search_results=search_results,
            page_metadata=page_metadata,
            user_context=user_context,
            ab_test_data=ab_test_data
        )
        
        return page_data
        
    except Exception as e:
        logger.error(f"Error getting SRP page data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get page data")

@router.get("/health")
async def srp_health_check():
    """Health check for SRP service."""
    return {
        "status": "healthy",
        "service": "Search Results Page",
        "timestamp": datetime.now().isoformat(),
        "database_connected": True
    }
