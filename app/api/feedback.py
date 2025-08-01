"""
Feedback API Endpoints
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.database import get_db

router = APIRouter()


class SearchFeedback(BaseModel):
    """Search feedback schema"""
    query: str = Field(..., description="Search query")
    was_helpful: bool = Field(..., description="Was the search result helpful")
    relevance_score: Optional[int] = Field(None, description="Relevance score 1-5", ge=1, le=5)
    comments: Optional[str] = Field(None, description="Additional feedback comments")
    session_id: Optional[str] = Field(None, description="User session ID")


class ProductFeedback(BaseModel):
    """Product feedback schema"""
    product_id: str = Field(..., description="Product ID")
    query: Optional[str] = Field(None, description="Search query that led to this product")
    was_relevant: bool = Field(..., description="Was product relevant to search")
    relevance_score: Optional[int] = Field(None, description="Relevance score 1-5", ge=1, le=5)
    comments: Optional[str] = Field(None, description="Additional feedback comments")
    session_id: Optional[str] = Field(None, description="User session ID")


class UserSuggestion(BaseModel):
    """User suggestion schema"""
    suggestion: str = Field(..., description="User suggestion for improvement")
    category: Optional[str] = Field(None, description="Suggestion category")
    session_id: Optional[str] = Field(None, description="User session ID")


@router.post("/search")
async def submit_search_feedback(
    feedback: SearchFeedback,
    db: Session = Depends(get_db)
):
    """Submit feedback about search results"""
    try:
        # Here you would typically save to a feedback table
        # For now, we'll just log it (in a real app, create a Feedback model)
        
        print(f"Search Feedback: {feedback.dict()}")
        
        # TODO: Save to database
        # feedback_record = SearchFeedbackRecord(
        #     query=feedback.query,
        #     was_helpful=feedback.was_helpful,
        #     relevance_score=feedback.relevance_score,
        #     comments=feedback.comments,
        #     session_id=feedback.session_id
        # )
        # db.add(feedback_record)
        # db.commit()
        
        return {
            "status": "success",
            "message": "Thank you for your feedback! We'll use it to improve search results.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.post("/product")
async def submit_product_feedback(
    feedback: ProductFeedback,
    db: Session = Depends(get_db)
):
    """Submit feedback about product relevance"""
    try:
        # Log the feedback (in a real app, save to database)
        print(f"Product Feedback: {feedback.dict()}")
        
        # TODO: Save to database
        # feedback_record = ProductFeedbackRecord(
        #     product_id=feedback.product_id,
        #     query=feedback.query,
        #     was_relevant=feedback.was_relevant,
        #     relevance_score=feedback.relevance_score,
        #     comments=feedback.comments,
        #     session_id=feedback.session_id
        # )
        # db.add(feedback_record)
        # db.commit()
        
        return {
            "status": "success", 
            "message": "Thank you for your feedback! We'll use it to improve product recommendations.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.post("/suggestion")
async def submit_suggestion(
    suggestion_data: UserSuggestion,
    db: Session = Depends(get_db)
):
    """Submit general suggestions for improvement"""
    try:
        # Log the suggestion
        print(f"User Suggestion: {suggestion_data.suggestion} (Category: {suggestion_data.category})")
        
        return {
            "status": "success",
            "message": "Thank you for your suggestion! We appreciate your feedback.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting suggestion: {str(e)}")
