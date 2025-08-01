"""
Autosuggest Pydantic Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AutosuggestItem(BaseModel):
    """Individual autosuggest suggestion item"""
    text: str = Field(..., description="Suggestion text")
    type: str = Field(..., description="Type of suggestion (query, brand, category, product)")
    category: Optional[str] = Field(None, description="Associated category")
    popularity: int = Field(0, description="Popularity score")


class AutosuggestResponse(BaseModel):
    """Autosuggest API response"""
    query: str = Field(..., description="Original query")
    suggestions: List[AutosuggestItem] = Field(default_factory=list, description="List of suggestions")
    total_count: int = Field(0, description="Total number of suggestions")
    response_time_ms: float = Field(0, description="Response time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "mobile",
                "suggestions": [
                    {
                        "text": "mobile phones",
                        "type": "query",
                        "category": "electronics",
                        "popularity": 5000
                    },
                    {
                        "text": "mobile charger",
                        "type": "query", 
                        "category": "electronics",
                        "popularity": 3000
                    }
                ],
                "total_count": 2,
                "response_time_ms": 45.2
            }
        }
