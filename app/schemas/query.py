"""
Query and Search Filter Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Search filters schema"""
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand") 
    min_price: Optional[float] = Field(None, description="Minimum price", ge=0)
    max_price: Optional[float] = Field(None, description="Maximum price", ge=0)
    min_rating: Optional[float] = Field(None, description="Minimum rating", ge=0, le=5)
    max_rating: Optional[float] = Field(None, description="Maximum rating", ge=0, le=5)
    in_stock: bool = Field(True, description="Show only in-stock products")
    is_bestseller: Optional[bool] = Field(None, description="Filter bestsellers")
    is_new_arrival: Optional[bool] = Field(None, description="Filter new arrivals")


class SearchQuery(BaseModel):
    """Search query schema"""
    query: str = Field(..., description="Search query text", min_length=1)
    filters: Optional[SearchFilters] = Field(None, description="Search filters")
    sort_by: str = Field(default="relevance", description="Sort by option")
    page: int = Field(default=1, description="Page number", ge=1)
    limit: int = Field(default=20, description="Results per page", ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "wireless headphones",
                "filters": {
                    "category": "Electronics",
                    "min_price": 1000,
                    "max_price": 10000,
                    "min_rating": 4.0,
                    "in_stock": True
                },
                "sort_by": "rating",
                "page": 1,
                "limit": 20
            }
        }


class AutosuggestQuery(BaseModel):
    """Autosuggest query schema"""
    query: str = Field(..., description="Query prefix", min_length=1)
    limit: int = Field(default=10, description="Max suggestions", ge=1, le=50)
    category: Optional[str] = Field(None, description="Filter by category")


class SimilarProductsQuery(BaseModel):
    """Similar products query schema"""
    product_id: str = Field(..., description="Source product ID")
    limit: int = Field(default=10, description="Max similar products", ge=1, le=50)
    include_same_brand: bool = Field(True, description="Include same brand products")
    include_same_category: bool = Field(True, description="Include same category products")
