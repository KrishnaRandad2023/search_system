"""
Enhanced Search API with ML ranking, business scoring, and analytics for Flipkart Grid 7.0
"""

import asyncio
import sqlite3
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import uuid
import time

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from app.utils.spell_checker import check_spelling

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/search", tags=["Enhanced Search"])

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    category: Optional[str] = Field(None, description="Product category filter")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    min_rating: Optional[float] = Field(None, ge=1, le=5, description="Minimum rating filter")
    sort_by: Optional[str] = Field("relevance", description="Sort criteria")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Results per page")
    use_ml_ranking: bool = Field(True, description="Use ML ranking")
    include_business_score: bool = Field(True, description="Include business scoring")

class SuggestionRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Partial query for suggestions")
    max_suggestions: int = Field(10, ge=1, le=20, description="Maximum number of suggestions")
    include_categories: bool = Field(True, description="Include category suggestions")
    include_trending: bool = Field(True, description="Include trending queries")

class ClickEvent(BaseModel):
    query: str = Field(..., description="Search query")
    product_id: int = Field(..., description="Clicked product ID")
    position: int = Field(..., ge=1, description="Position in search results")
    session_id: str = Field(..., description="User session ID")

class FeedbackEvent(BaseModel):
    query: str = Field(..., description="Search query")
    product_id: int = Field(..., description="Product ID")
    feedback_type: str = Field(..., description="Feedback type (like, dislike, purchase)")
    session_id: str = Field(..., description="User session ID")

class ProductResult(BaseModel):
    id: int
    name: str
    category: str
    subcategory: str
    brand: str
    price: float
    original_price: float
    discount_percentage: float
    rating: float
    rating_count: int
    description: str
    features: List[str]
    in_stock: bool
    stock_quantity: int
    relevance_score: float
    business_score: Optional[float] = None
    final_score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    total_results: int
    page: int
    per_page: int
    total_pages: int
    results: List[ProductResult]
    search_time_ms: float
    filters_applied: Dict[str, Any]
    suggestions: Optional[List[str]] = None
    has_typo_correction: bool = False
    corrected_query: Optional[str] = None

class SuggestionResult(BaseModel):
    text: str
    type: str  # "product", "category", "brand", "trending"
    score: float
    metadata: Optional[Dict[str, Any]] = None

class SuggestionResponse(BaseModel):
    query: str
    suggestions: List[SuggestionResult]
    response_time_ms: float

class AnalyticsResponse(BaseModel):
    total_searches: int
    total_clicks: int
    average_ctr: float
    top_queries: List[Dict[str, Any]]
    top_clicked_products: List[Dict[str, Any]]
    search_trends: Dict[str, Any]

# Global variables for components
search_engine = None
ml_ranker = None
autosuggest_engine = None
business_scorer = None
click_tracker = None

def get_db_connection():
    """Get database connection."""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def initialize_components():
    """Initialize search components."""
    global search_engine, ml_ranker, autosuggest_engine, business_scorer, click_tracker
    
    try:
        # Try to initialize hybrid search engine
        try:
            from search.hybrid_engine import HybridSearchEngine
            # Initialize search engine with minimal configuration for now
            # In production, these components would be pre-built and loaded
            search_engine = None  # Will be initialized separately with proper components
            logger.info("Search engine setup deferred (requires component initialization)")
        except ImportError:
            logger.warning("Hybrid search engine not available")
            search_engine = None
        
        # Try to initialize ML ranker
        try:
            from ml.ranker import MLRanker
            ml_ranker = MLRanker()
            logger.info("ML ranker initialized")
        except ImportError:
            logger.warning("ML ranker not available")
            ml_ranker = None
        
        # Try to initialize autosuggest engine
        try:
            from search.autosuggest_engine import AdvancedAutosuggestEngine
            from pathlib import Path
            autosuggest_engine = AdvancedAutosuggestEngine(Path(Config.MODEL_DIR), Config.DATABASE_PATH)
            logger.info("Autosuggest engine initialized")
        except ImportError:
            logger.warning("Autosuggest engine not available")
            autosuggest_engine = None
        
        # Try to initialize business scorer
        try:
            from core.business_scoring import BusinessScoringEngine
            business_scorer = BusinessScoringEngine(Config.DATABASE_PATH)
            logger.info("Business scorer initialized")
        except ImportError:
            logger.warning("Business scorer not available")
            business_scorer = None
        
        # Try to initialize click tracker
        try:
            from core.click_tracking import ClickTrackingSystem
            click_tracker = ClickTrackingSystem(Config.DATABASE_PATH)
            logger.info("Click tracker initialized")
        except ImportError:
            logger.warning("Click tracker not available")
            click_tracker = None
            
    except Exception as e:
        logger.error(f"Error initializing components: {e}")

def perform_basic_search(query: str, category: Optional[str] = None, 
                        min_price: Optional[float] = None, max_price: Optional[float] = None,
                        min_rating: Optional[float] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Perform basic database search when advanced components are not available."""
    conn = get_db_connection()
    
    # Build SQL query
    sql = """
    SELECT id, name, category, subcategory, brand, price, original_price, 
           discount_percentage, rating, rating_count, description, features,
           in_stock, stock_quantity
    FROM products
    WHERE name LIKE ? OR description LIKE ? OR brand LIKE ?
    """
    
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    
    if category:
        sql += " AND (category = ? OR subcategory = ?)"
        params.extend([category, category])
    
    if min_price is not None:
        sql += " AND price >= ?"
        params.append(str(min_price))
    
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(str(max_price))
    
    if min_rating is not None:
        sql += " AND rating >= ?"
        params.append(str(min_rating))
    
    sql += " ORDER BY rating DESC, rating_count DESC LIMIT ? OFFSET ?"
    params.extend([str(limit), str(offset)])
    
    try:
        cursor = conn.execute(sql, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['relevance_score'] = 0.8  # Default score
            result['features'] = json.loads(result['features']) if result['features'] else []
            results.append(result)
        
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Basic search error: {e}")
        conn.close()
        return []

@router.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    await initialize_components()

@router.post("/search", response_model=SearchResponse)
async def enhanced_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Enhanced search with ML ranking, business scoring, and analytics.
    """
    start_time = time.time()
    session_id = req.headers.get("session-id", str(uuid.uuid4()))
    
    # Apply spell correction to the query
    corrected_query, has_typo_correction = check_spelling(request.query)
    effective_query = corrected_query if has_typo_correction else request.query
    
    try:
        # Calculate pagination
        offset = (request.page - 1) * request.per_page
        
        # Perform search based on available components
        if search_engine:
            # Use hybrid search engine
            try:
                search_results = search_engine.search(
                    query=effective_query,
                    k=request.per_page
                )
            except Exception as e:
                logger.error(f"Hybrid search error: {e}")
                search_results = perform_basic_search(
                    effective_query, request.category, request.min_price,
                    request.max_price, request.min_rating, request.per_page, offset
                )
        else:
            # Use basic search
            search_results = perform_basic_search(
                effective_query, request.category, request.min_price,
                request.max_price, request.min_rating, request.per_page, offset
            )
        
        # Apply business scoring if available
        if business_scorer and request.include_business_score:
            try:
                product_ids = [result['id'] for result in search_results]
                base_scores = {str(product_id): 0.5 for product_id in product_ids}
                business_score_results = business_scorer.score_products(product_ids, base_scores)
                
                # Convert list of BusinessScore objects to dict
                if isinstance(business_score_results, list):
                    business_scores = {score.product_id: score.final_score for score in business_score_results}
                else:
                    business_scores = business_score_results
                
                for i, result in enumerate(search_results):
                    result['business_score'] = business_scores.get(result['id'], 0.5)
            except Exception as e:
                logger.error(f"Business scoring error: {e}")
                for result in search_results:
                    result['business_score'] = 0.5
        
        # Apply ML ranking if available
        if ml_ranker and request.use_ml_ranking:
            try:
                ranked_results = ml_ranker.rerank(search_results)
                search_results = ranked_results
            except Exception as e:
                logger.error(f"ML ranking error: {e}")
        
        # Calculate final scores and sort
        for result in search_results:
            relevance_score = result.get('relevance_score', 0.5)
            business_score = result.get('business_score', 0.5)
            result['final_score'] = 0.7 * relevance_score + 0.3 * business_score
        
        # Sort by final score
        search_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # Get total count for pagination
        total_results = len(search_results) + offset  # Approximation
        
        # Convert to ProductResult models
        product_results = []
        for result in search_results:
            try:
                product_result = ProductResult(**result)
                product_results.append(product_result)
            except Exception as e:
                logger.error(f"Error converting result: {e}")
                continue
        
        # Track search event in background
        if click_tracker:
            background_tasks.add_task(
                track_search_event,
                request.query,
                session_id,
                len(product_results)
            )
        
        # Calculate response time
        search_time = (time.time() - start_time) * 1000
        
        # Prepare response
        response = SearchResponse(
            query=request.query,  # Original query
            total_results=total_results,
            page=request.page,
            per_page=request.per_page,
            total_pages=(total_results + request.per_page - 1) // request.per_page,
            results=product_results,
            search_time_ms=round(search_time, 2),
            has_typo_correction=has_typo_correction,
            corrected_query=corrected_query if has_typo_correction else None,
            filters_applied={
                "category": request.category,
                "min_price": request.min_price,
                "max_price": request.max_price,
                "min_rating": request.min_rating,
                "sort_by": request.sort_by
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(request: SuggestionRequest):
    """
    Get search suggestions with spell correction and trending queries.
    """
    start_time = time.time()
    
    try:
        suggestions = []
        
        if autosuggest_engine:
            try:
                # Get suggestions from autosuggest engine
                engine_suggestions = autosuggest_engine.get_suggestions(
                    query=request.query,
                    max_suggestions=request.max_suggestions
                )
                
                suggestions = [
                    SuggestionResult(
                        text=sugg.query,
                        type=sugg.suggestion_type,
                        score=sugg.score,
                        metadata=sugg.metadata
                    )
                    for sugg in engine_suggestions
                ]
            except Exception as e:
                logger.error(f"Autosuggest error: {e}")
        
        # Fallback: basic suggestions from database
        if not suggestions:
            suggestions = await get_basic_suggestions(request.query, request.max_suggestions)
        
        response_time = (time.time() - start_time) * 1000
        
        return SuggestionResponse(
            query=request.query,
            suggestions=suggestions,
            response_time_ms=round(response_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

async def get_basic_suggestions(query: str, max_suggestions: int) -> List[SuggestionResult]:
    """Get basic suggestions from database."""
    conn = get_db_connection()
    
    try:
        # Get product name suggestions
        cursor = conn.execute(
            """
            SELECT DISTINCT name, COUNT(*) as popularity
            FROM products 
            WHERE name LIKE ? 
            GROUP BY name
            ORDER BY popularity DESC, name
            LIMIT ?
            """,
            [f"%{query}%", max_suggestions // 2]
        )
        
        suggestions = []
        for row in cursor.fetchall():
            suggestions.append(SuggestionResult(
                text=row[0],
                type="product",
                score=min(row[1] / 100.0, 1.0),
                metadata={"popularity": row[1]}
            ))
        
        # Get brand suggestions
        cursor = conn.execute(
            """
            SELECT DISTINCT brand, COUNT(*) as popularity
            FROM products 
            WHERE brand LIKE ? 
            GROUP BY brand
            ORDER BY popularity DESC, brand
            LIMIT ?
            """,
            [f"%{query}%", max_suggestions // 2]
        )
        
        for row in cursor.fetchall():
            suggestions.append(SuggestionResult(
                text=row[0],
                type="brand",
                score=min(row[1] / 100.0, 1.0),
                metadata={"popularity": row[1]}
            ))
        
        conn.close()
        return suggestions[:max_suggestions]
        
    except Exception as e:
        logger.error(f"Basic suggestions error: {e}")
        conn.close()
        return []

@router.post("/track/click")
async def track_click(event: ClickEvent, background_tasks: BackgroundTasks):
    """Track product click events."""
    try:
        if click_tracker:
            background_tasks.add_task(
                track_click_event,
                event.query,
                event.product_id,
                event.position,
                event.session_id
            )
        
        return {"status": "success", "message": "Click tracked"}
        
    except Exception as e:
        logger.error(f"Click tracking error: {e}")
        raise HTTPException(status_code=500, detail="Click tracking failed")

@router.post("/track/feedback")
async def track_feedback(event: FeedbackEvent, background_tasks: BackgroundTasks):
    """Track user feedback events."""
    try:
        if click_tracker:
            background_tasks.add_task(
                track_feedback_event,
                event.query,
                event.product_id,
                event.feedback_type,
                event.session_id
            )
        
        return {"status": "success", "message": "Feedback tracked"}
        
    except Exception as e:
        logger.error(f"Feedback tracking error: {e}")
        raise HTTPException(status_code=500, detail="Feedback tracking failed")

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(hours: int = Query(24, ge=1, le=168, description="Time range in hours")):
    """Get search analytics and metrics."""
    try:
        if click_tracker:
            try:
                metrics = click_tracker.get_search_metrics(hours)
                return AnalyticsResponse(**metrics)
            except Exception as e:
                logger.error(f"Analytics error: {e}")
        
        # Fallback basic analytics
        return AnalyticsResponse(
            total_searches=0,
            total_clicks=0,
            average_ctr=0.0,
            top_queries=[],
            top_clicked_products=[],
            search_trends={}
        )
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analytics failed")

# Background task functions
async def track_search_event(query: str, session_id: str, result_count: int):
    """Background task to track search events."""
    if click_tracker:
        try:
            from app.core.click_tracking import SearchEvent as CoreSearchEvent
            search_event = CoreSearchEvent(
                session_id=session_id,
                user_id=None,
                query=query,
                timestamp=datetime.now(),
                results_count=result_count,
                response_time_ms=0.0,
                search_type="text",
                filters_applied={},
                sort_order="relevance",
                page_number=1
            )
            click_tracker.track_search(search_event)
        except Exception as e:
            logger.error(f"Search tracking error: {e}")

async def track_click_event(query: str, product_id: int, position: int, session_id: str):
    """Background task to track click events."""
    if click_tracker:
        try:
            from app.core.click_tracking import ClickEvent as CoreClickEvent
            click_event = CoreClickEvent(
                session_id=session_id,
                user_id=None,
                query=query,
                product_id=str(product_id),
                position=position,
                timestamp=datetime.now(),
                click_type="product",
                page_number=1,
                total_results=0
            )
            click_tracker.track_click(click_event)
        except Exception as e:
            logger.error(f"Click tracking error: {e}")

async def track_feedback_event(query: str, product_id: int, feedback_type: str, session_id: str):
    """Background task to track feedback events."""
    if click_tracker:
        try:
            from app.core.click_tracking import FeedbackEvent as CoreFeedbackEvent
            feedback_event = CoreFeedbackEvent(
                session_id=session_id,
                user_id=None,
                query=query,
                product_id=str(product_id),
                feedback_type=feedback_type,
                feedback_text=None,
                timestamp=datetime.now(),
                position=None
            )
            click_tracker.track_feedback(feedback_event)
        except Exception as e:
            logger.error(f"Feedback tracking error: {e}")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "search_engine": search_engine is not None,
            "ml_ranker": ml_ranker is not None,
            "autosuggest_engine": autosuggest_engine is not None,
            "business_scorer": business_scorer is not None,
            "click_tracker": click_tracker is not None
        }
    }
