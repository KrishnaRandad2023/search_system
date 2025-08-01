"""
Schema definitions for the Flipkart Search API
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from uuid import UUID, uuid4

class ProductBase(BaseModel):
    """Base schema for product data"""
    product_id: str = Field(..., description="Unique identifier for the product")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    brand: str = Field(..., description="Product brand")
    price: float = Field(..., description="Product price")
    rating: float = Field(..., description="Product rating (0-5)")
    image_url: Optional[str] = Field(None, description="Product image URL")

class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass

class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class Product(ProductBase):
    """Schema for retrieving a product"""
    id: int = Field(..., description="Internal database ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True

class SearchResult(BaseModel):
    """Schema for a single search result"""
    id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    brand: str = Field(..., description="Product brand")
    price: float = Field(..., description="Product price")
    rating: float = Field(..., description="Product rating")
    image_url: Optional[str] = Field(None, description="Product image URL")
    position: int = Field(..., description="Position in search results")
    relevance_score: float = Field(..., description="Relevance score")
    
class SearchRequest(BaseModel):
    """Schema for search request"""
    query: str = Field(..., description="The search query")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Offset for pagination")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters to apply")
    session_id: Optional[str] = Field(None, description="Session ID for user tracking")
    use_ml_ranking: bool = Field(True, description="Whether to apply ML ranking")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str = Field(..., description="The search query")
    total_results: int = Field(..., description="Total number of results found")
    time_ms: float = Field(..., description="Search time in milliseconds")
    results: List[SearchResult] = Field(..., description="Search results")
    session_id: str = Field(..., description="Session ID for tracking")
    filters: Dict[str, List[str]] = Field(..., description="Available filters")
    search_id: str = Field(..., description="Unique search ID")

class AutocompleteRequest(BaseModel):
    """Schema for autocomplete request"""
    prefix: str = Field(..., description="The prefix to autocomplete")
    limit: int = Field(10, description="Maximum number of suggestions")
    session_id: Optional[str] = Field(None, description="Session ID for user tracking")
    
    @validator('prefix')
    def prefix_not_empty(cls, v):
        if v is None:
            return ""
        return v.strip()

class AutocompleteResponse(BaseModel):
    """Schema for autocomplete response"""
    prefix: str = Field(..., description="The prefix to autocomplete")
    suggestions: List[str] = Field(..., description="Autocomplete suggestions")
    time_ms: float = Field(..., description="Processing time in milliseconds")
    session_id: str = Field(..., description="Session ID for tracking")

class FeedbackRequest(BaseModel):
    """Schema for user feedback"""
    session_id: str = Field(..., description="Session ID")
    search_id: str = Field(..., description="Search ID")
    product_id: str = Field(..., description="Product ID")
    action: str = Field(..., description="User action (click, purchase, add_to_cart, etc.)")
    position: Optional[int] = Field(None, description="Position in search results")
    query: Optional[str] = Field(None, description="Search query")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the action")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now()

class SearchMetricsResponse(BaseModel):
    """Schema for search metrics"""
    total_searches: int = Field(..., description="Total number of searches")
    avg_latency: float = Field(..., description="Average search latency in milliseconds")
    success_rate: float = Field(..., description="Success rate (percentage)")
    top_queries: Dict[str, int] = Field(..., description="Top queries and counts")
    zero_results: int = Field(..., description="Number of searches with zero results")
    active_sessions: int = Field(..., description="Number of active user sessions")

class ABTestConfig(BaseModel):
    """Schema for A/B test configuration"""
    experiment_id: str = Field(..., description="Experiment ID")
    description: str = Field(..., description="Experiment description")
    variants: List[str] = Field(..., description="Test variants")
    start_date: datetime = Field(..., description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    is_active: bool = Field(True, description="Whether the experiment is active")
    
class ABTestAssignment(BaseModel):
    """Schema for A/B test assignment"""
    experiment_id: str = Field(..., description="Experiment ID")
    variant: str = Field(..., description="Assigned variant")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Assignment timestamp")
