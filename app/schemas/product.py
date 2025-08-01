"""
Product Pydantic Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product schema"""
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    brand: str = Field(..., description="Product brand")


class ProductResponse(ProductBase):
    """Product response schema"""
    price: float = Field(..., description="Current price")
    original_price: Optional[float] = Field(None, description="Original price before discount")
    discount_percentage: Optional[int] = Field(None, description="Discount percentage")
    rating: Optional[float] = Field(None, description="Average rating")
    num_ratings: int = Field(0, description="Number of ratings")
    num_reviews: int = Field(0, description="Number of reviews")
    stock: int = Field(0, description="Available stock")
    is_bestseller: bool = Field(False, description="Is bestseller product")
    is_new_arrival: bool = Field(False, description="Is new arrival")
    image_url: Optional[str] = Field(None, description="Product image URL")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "product_id": "FLP12345678",
                "title": "Samsung Galaxy S23 Ultra (12GB RAM, 256GB)",
                "description": "Latest Samsung flagship with advanced camera and performance",
                "category": "Electronics",
                "subcategory": "Mobile Phones", 
                "brand": "Samsung",
                "price": 89999.0,
                "original_price": 124999.0,
                "discount_percentage": 28,
                "rating": 4.5,
                "num_ratings": 1247,
                "num_reviews": 312,
                "stock": 45,
                "is_bestseller": True,
                "is_new_arrival": False,
                "image_url": "https://example.com/images/flp12345678.jpg"
            }
        }


class SearchResponse(BaseModel):
    """Search API response schema"""
    query: str = Field(..., description="Original search query")
    products: List[ProductResponse] = Field(default_factory=list, description="List of matching products")
    total_count: int = Field(0, description="Total number of matching products")
    page: int = Field(1, description="Current page number")
    limit: int = Field(20, description="Results per page")
    total_pages: int = Field(0, description="Total number of pages")
    response_time_ms: float = Field(0, description="Response time in milliseconds")
    has_typo_correction: bool = Field(False, description="Whether spelling correction was applied")
    corrected_query: Optional[str] = Field(None, description="Spell-corrected query if correction was applied")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "samsung mobile",
                "products": [
                    {
                        "product_id": "FLP12345678",
                        "title": "Samsung Galaxy S23 Ultra (12GB RAM, 256GB)",
                        "category": "Electronics",
                        "brand": "Samsung",
                        "price": 89999.0,
                        "rating": 4.5,
                        "stock": 45
                    }
                ],
                "total_count": 156,
                "page": 1,
                "limit": 20,
                "total_pages": 8,
                "response_time_ms": 123.45,
                "filters_applied": {
                    "category": "Electronics",
                    "brand": "Samsung"
                }
            }
        }
