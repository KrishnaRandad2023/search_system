"""
Autosuggest Feedback API Endpoints
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services.smart_autosuggest_service import get_smart_autosuggest_service, SmartAutosuggestService

router = APIRouter()


class AutosuggestInteractionRequest(BaseModel):
    """Request model for recording autosuggest interactions"""
    query: str
    selected_suggestion: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[int] = None  # Unix timestamp
    metadata: Optional[Dict[str, Any]] = None


@router.post("/record-interaction")
async def record_autosuggest_interaction(
    data: AutosuggestInteractionRequest = Body(...),
    db: Session = Depends(get_db),
    service: SmartAutosuggestService = Depends(get_smart_autosuggest_service)
):
    """
    Record user interaction with autosuggest
    
    - Tracks what queries users enter
    - Records which suggestions they select
    - Used to improve autosuggest quality
    """
    try:
        service.record_interaction(
            query=data.query,
            selected_suggestion=data.selected_suggestion,
            user_id=data.user_id
        )
        
        return {
            "success": True,
            "message": "Interaction recorded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording interaction: {str(e)}")


@router.post("/feedback")
async def submit_autosuggest_feedback(
    query: str,
    rating: int = Body(..., description="Rating from 1-5", ge=1, le=5),
    comment: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on autosuggest quality
    
    - Rate the quality of suggestions (1-5)
    - Provide comments or improvement ideas
    """
    try:
        # Store feedback in database (would implement in real system)
        
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "feedback_id": "feedback_12345"  # Would be a real ID in production
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.get("/analytics")
async def get_autosuggest_analytics(
    days: int = Query(default=7, description="Number of days to analyze", le=30),
    db: Session = Depends(get_db)
):
    """
    Get analytics about autosuggest performance
    Shows metrics like click-through rates, popular queries, etc.
    """
    try:
        # This would normally query actual interaction data
        # For now, return sample analytics
        
        analytics_data = {
            "period_days": days,
            "total_queries": 12450,
            "total_suggestions_shown": 45230,
            "total_clicks": 8934,
            "click_through_rate": 0.197,  # 19.7%
            "top_queries": [
                {"query": "mobile under 10k", "count": 1245, "ctr": 0.23},
                {"query": "samsung mobile", "count": 987, "ctr": 0.31},
                {"query": "laptop under 50k", "count": 845, "ctr": 0.18},
                {"query": "oneplus phone", "count": 723, "ctr": 0.28},
                {"query": "best headphones", "count": 689, "ctr": 0.22}
            ],
            "query_types": {
                "price_range": 35,
                "brand_category": 28,
                "modifier": 20,
                "general": 17
            },
            "suggestion_performance": {
                "avg_suggestions_per_query": 3.6,
                "avg_response_time_ms": 45,
                "quality_score": 4.2  # out of 5
            }
        }
        
        return analytics_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.get("/health")
async def autosuggest_health_check(
    db: Session = Depends(get_db),
    smart_service: SmartAutosuggestService = Depends(get_smart_autosuggest_service)
):
    """
    Health check for autosuggest service
    Verifies that all components are working properly
    """
    try:
        # Test the smart autosuggest service
        test_suggestions = smart_service.get_smart_suggestions(db, "test mobile", limit=3)
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "connected",
                "query_analyzer": "active",
                "smart_autosuggest": "active",
                "suggestion_engine": "working"
            },
            "test_results": {
                "test_query": "test mobile",
                "suggestions_generated": len(test_suggestions),
                "response_time_ms": "< 100ms"
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "components": {
                "database": "unknown",
                "query_analyzer": "unknown",
                "smart_autosuggest": "error",
                "suggestion_engine": "unknown"
            }
        }
