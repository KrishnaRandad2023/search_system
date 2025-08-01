"""
Analytics API Endpoints
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import SearchLog, UserEvent

router = APIRouter()


class AnalyticsEvent(BaseModel):
    """Analytics event schema"""
    event_type: str
    query: Optional[str] = None
    product_id: Optional[str] = None
    category: Optional[str] = None
    session_id: Optional[str] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None


@router.post("/event")
async def log_analytics_event(
    event: AnalyticsEvent,
    db: Session = Depends(get_db)
):
    """Log analytics event"""
    try:
        user_event = UserEvent(
            session_id=event.session_id,
            event_type=event.event_type,
            query=event.query,
            product_id=event.product_id,
            category=event.category,
            page_url=event.page_url,
            user_agent=event.user_agent
        )
        
        db.add(user_event)
        db.commit()
        
        return {"status": "success", "message": "Event logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging event: {str(e)}")


@router.get("/search-stats", response_model=Dict[str, Any])
async def get_search_statistics(
    days: int = Query(default=7, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get search analytics statistics"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total searches
        total_searches = db.query(SearchLog).filter(
            SearchLog.created_at >= cutoff_date
        ).count()
        
        # Average response time
        avg_response_time = db.query(func.avg(SearchLog.response_time_ms)).filter(
            SearchLog.created_at >= cutoff_date
        ).scalar() or 0
        
        # Top queries
        top_queries = db.query(
            SearchLog.query,
            func.count(SearchLog.query).label('count')
        ).filter(
            SearchLog.created_at >= cutoff_date
        ).group_by(SearchLog.query).order_by(desc('count')).limit(10).all()
        
        # Zero result queries
        zero_result_queries = db.query(SearchLog).filter(
            SearchLog.created_at >= cutoff_date,
            SearchLog.results_count == 0
        ).count()
        
        # Click-through rate (if we have click data)
        clicked_searches = db.query(SearchLog).filter(
            SearchLog.created_at >= cutoff_date,
            SearchLog.clicked_product_id.isnot(None)
        ).count()
        
        ctr = (clicked_searches / total_searches * 100) if total_searches > 0 else 0
        
        return {
            "period_days": days,
            "total_searches": total_searches,
            "average_response_time_ms": round(avg_response_time, 2),
            "zero_result_queries": zero_result_queries,
            "zero_result_rate_percent": round((zero_result_queries / total_searches * 100) if total_searches > 0 else 0, 2),
            "click_through_rate_percent": round(ctr, 2),
            "top_queries": [
                {"query": query, "count": count} 
                for query, count in top_queries
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search statistics: {str(e)}")


@router.get("/popular-products", response_model=List[Dict[str, Any]])
async def get_popular_products(
    days: int = Query(default=7, description="Number of days to analyze", ge=1, le=365),
    limit: int = Query(default=20, description="Number of products to return", le=100),
    db: Session = Depends(get_db)
):
    """Get most popular products based on search clicks"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with most clicks
        popular_products = db.query(
            SearchLog.clicked_product_id,
            func.count(SearchLog.clicked_product_id).label('click_count')
        ).filter(
            SearchLog.created_at >= cutoff_date,
            SearchLog.clicked_product_id.isnot(None)
        ).group_by(SearchLog.clicked_product_id).order_by(desc('click_count')).limit(limit).all()
        
        return [
            {"product_id": product_id, "click_count": count}
            for product_id, count in popular_products
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting popular products: {str(e)}")


@router.get("/trends", response_model=Dict[str, Any])
async def get_search_trends(
    days: int = Query(default=30, description="Number of days to analyze", ge=7, le=365),
    db: Session = Depends(get_db)
):
    """Get search trends over time"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily search counts
        daily_searches = db.query(
            func.date(SearchLog.created_at).label('date'),
            func.count(SearchLog.id).label('count')
        ).filter(
            SearchLog.created_at >= cutoff_date
        ).group_by(func.date(SearchLog.created_at)).order_by('date').all()
        
        # Trending queries (queries with increasing frequency)
        trending_queries = db.query(
            SearchLog.query,
            func.count(SearchLog.query).label('count')
        ).filter(
            SearchLog.created_at >= cutoff_date
        ).group_by(SearchLog.query).having(func.count(SearchLog.query) > 5).order_by(desc('count')).limit(10).all()
        
        return {
            "period_days": days,
            "daily_searches": [
                {"date": str(date), "count": count}
                for date, count in daily_searches
            ],
            "trending_queries": [
                {"query": query, "count": count}
                for query, count in trending_queries
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search trends: {str(e)}")
