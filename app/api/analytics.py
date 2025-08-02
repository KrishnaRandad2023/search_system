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
from app.services.metrics_counter import metrics_counter

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


@router.get("/user-metrics", response_model=Dict[str, Any])
async def get_user_metrics(
    days: int = Query(default=7, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get user activity metrics"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Active users (unique session IDs)
        active_users = db.query(func.count(func.distinct(SearchLog.session_id))).filter(
            SearchLog.created_at >= cutoff_date
        ).scalar() or 0
        
        # Total API requests (search logs + user events)
        total_searches = db.query(SearchLog).filter(
            SearchLog.created_at >= cutoff_date
        ).count()
        
        total_events = db.query(UserEvent).filter(
            UserEvent.created_at >= cutoff_date
        ).count()
        
        total_api_requests = total_searches + total_events
        
        # Daily active users
        daily_active_users = db.query(
            func.date(SearchLog.created_at).label('date'),
            func.count(func.distinct(SearchLog.session_id)).label('unique_users')
        ).filter(
            SearchLog.created_at >= cutoff_date
        ).group_by(func.date(SearchLog.created_at)).order_by('date').all()
        
        # Event types breakdown
        event_types = db.query(
            UserEvent.event_type,
            func.count(UserEvent.event_type).label('count')
        ).filter(
            UserEvent.created_at >= cutoff_date
        ).group_by(UserEvent.event_type).order_by(desc('count')).all()
        
        return {
            "period_days": days,
            "active_users": active_users,
            "total_api_requests": total_api_requests,
            "total_searches": total_searches,
            "total_events": total_events,
            "daily_active_users": [
                {"date": str(date), "users": users}
                for date, users in daily_active_users
            ],
            "event_types": [
                {"type": event_type, "count": count}
                for event_type, count in event_types
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user metrics: {str(e)}")


@router.get("/system-metrics", response_model=Dict[str, Any])
async def get_system_metrics(db: Session = Depends(get_db)):
    """Get system-wide metrics"""
    try:
        # Total products count
        from app.db.models import Product
        total_products = db.query(Product).count()
        
        # Available products
        available_products = db.query(Product).filter(Product.is_available == True).count()
        
        # Categories count
        categories_count = db.query(func.count(func.distinct(Product.category))).scalar() or 0
        
        # Brands count
        brands_count = db.query(func.count(func.distinct(Product.brand))).scalar() or 0
        
        return {
            "total_products": total_products,
            "available_products": available_products,
            "categories_count": categories_count,
            "brands_count": brands_count,
            "database_size_mb": 0,  # Would need OS-level query to get actual DB size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system metrics: {str(e)}")


@router.get("/realtime-metrics", response_model=Dict[str, Any])
async def get_realtime_metrics():
    """Get real-time API call and feature usage metrics"""
    try:
        # Get current metrics from counter
        live_metrics = metrics_counter.get_metrics()
        
        return {
            # Basic metrics
            "live_api_calls": live_metrics["total_api_calls"],
            "live_search_calls": live_metrics["total_search_calls"],
            "today_searches": live_metrics["daily_search_count"],
            "uptime_seconds": live_metrics["uptime_seconds"],
            "server_start_time": live_metrics["start_time"],
            "daily_breakdown": live_metrics["all_daily_counts"],
            
            # Feature usage metrics
            "feature_usage": {
                "autosuggest_calls": live_metrics["autosuggest_calls"],
                "hybrid_search_calls": live_metrics["hybrid_search_calls"],
                "semantic_search_calls": live_metrics["semantic_search_calls"],
                "feedback_submissions": live_metrics["feedback_submissions"],
                "product_clicks": live_metrics["product_clicks"],
                "filter_usage": live_metrics["filter_usage"],
                "ml_ranking_calls": live_metrics["ml_ranking_calls"],
                "typo_corrections": live_metrics["typo_corrections"],
                "zero_result_queries": live_metrics["zero_result_queries"],
            },
            
            # Category breakdown
            "category_searches": live_metrics["category_searches"],
            
            # Performance metrics
            "performance": {
                "average_response_time_ms": live_metrics["average_response_time_ms"],
                "total_measurements": live_metrics["total_response_measurements"],
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting realtime metrics: {str(e)}")


@router.post("/reset-counters")
async def reset_counters():
    """Reset live counters (for testing)"""
    try:
        metrics_counter.reset_counters()
        return {"status": "success", "message": "Counters reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting counters: {str(e)}")
