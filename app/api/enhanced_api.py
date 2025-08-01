"""
🔥 Production-Ready Enhanced Search API for Flipkart Grid 7.0
Integrates all advanced components: autosuggest, business scoring, click tracking
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import time
import logging
from datetime import datetime
import psutil
import sys
import uuid
import sqlite3
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our enhanced components
autosuggest_engine_cls = None
business_scoring_cls = None
click_tracking_cls = None

try:
    from search.autosuggest_engine import AdvancedAutosuggestEngine
    autosuggest_engine_cls = AdvancedAutosuggestEngine
except ImportError as e:
    print(f"Could not import autosuggest engine: {e}")

try:
    from core.business_scoring import BusinessScoringEngine  
    business_scoring_cls = BusinessScoringEngine
except ImportError as e:
    print(f"Could not import business scoring: {e}")

try:
    from core.click_tracking import ClickTrackingSystem, SearchEvent, ClickEvent, FeedbackEvent
    click_tracking_cls = ClickTrackingSystem
except ImportError as e:
    print(f"Could not import click tracking: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="🔥 Flipkart Grid Enhanced Search API",
    description="Production-grade search system with AI/ML ranking and comprehensive analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pydantic Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1, max_length=200)
    page: int = Field(1, description="Page number", ge=1, le=100)
    size: int = Field(10, description="Results per page", ge=1, le=50)
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    sort: str = Field("relevance", description="Sort order")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    page: int
    size: int
    response_time_ms: float
    suggestions: List[str] = []
    filters_applied: Dict[str, Any] = {}
    sort_order: str = "relevance"
    session_id: str

class AutocompleteRequest(BaseModel):
    query: str = Field(..., description="Partial query for autocomplete", max_length=100)
    max_suggestions: int = Field(8, description="Maximum suggestions", ge=1, le=20)

class ClickTrackingRequest(BaseModel):
    session_id: str
    query: str
    product_id: str
    position: int
    click_type: str = "product"
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    feedback_type: str  # "thumbs_up", "thumbs_down", "not_relevant"
    product_id: Optional[str] = None
    feedback_text: Optional[str] = None
    position: Optional[int] = None
    user_id: Optional[str] = None

# Global components
autosuggest_engine = None
business_scorer = None
click_tracker = None

# Startup time for uptime calculation
app_start_time = datetime.now()

@app.on_event("startup")
async def initialize_components():
    """Initialize enhanced search components on startup"""
    global autosuggest_engine, business_scorer, click_tracker
    
    logger.info("🚀 Initializing Enhanced Search Components...")
    
    try:
        # Database path
        db_path = str(Path(__file__).parent.parent.parent / "data" / "db" / "flipkart_products.db")
        data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Check if database exists
        if not Path(db_path).exists():
            logger.error(f"❌ Database not found at {db_path}")
            logger.error("Please run: python scripts/generate_flipkart_products.py")
            return
            
        # Initialize components
        logger.info("Loading autosuggest engine...")
        if autosuggest_engine_cls:
            autosuggest_engine = autosuggest_engine_cls(data_dir, db_path)
        
        logger.info("Loading business scorer...")
        if business_scoring_cls:
            business_scorer = business_scoring_cls(db_path)
        
        logger.info("Loading click tracker...")
        if click_tracking_cls:
            click_tracker = click_tracking_cls(db_path)
        
        # Generate sample tracking data if empty
        if click_tracker:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM search_events")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    logger.info("Generating sample tracking data...")
                    click_tracker.generate_sample_data(1000)
            except Exception as e:
                logger.warning(f"Could not generate sample data: {e}")
        
        logger.info("✅ Enhanced components initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced components: {e}")
        raise

# Dependency to get session ID
def get_session_id(request: Request) -> str:
    """Get or create session ID"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())[:12]
    return session_id

@app.get("/health")
async def health_check():
    """Enhanced health check with component status"""
    
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    # Check component health
    components_health = {
        "autosuggest_engine": autosuggest_engine is not None,
        "business_scorer": business_scorer is not None,
        "click_tracker": click_tracker is not None
    }
    
    # System metrics
    memory_info = psutil.virtual_memory()
    
    all_healthy = all(components_health.values())
    status = "healthy" if all_healthy else "degraded"
    
    return JSONResponse({
        "status": status,
        "uptime_seconds": uptime,
        "components": {k: "healthy" if v else "unhealthy" for k, v in components_health.items()},
        "metrics": {
            "memory_usage_percent": memory_info.percent,
            "memory_available_mb": memory_info.available / (1024 * 1024),
            "cpu_usage_percent": psutil.cpu_percent()
        }
    })

@app.post("/search/enhanced", response_model=SearchResponse)
async def enhanced_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_session_id)
):
    """
    🔍 Enhanced search with business scoring and tracking
    """
    
    start_time = time.time()
    
    try:
        # Use provided session_id or generate one
        actual_session_id = request.session_id or session_id
        
        # Perform database search
        db_path = str(Path(__file__).parent.parent.parent / "data" / "db" / "flipkart_products.db")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Basic search query
        query_terms = request.query.lower().split()
        search_conditions = []
        params = []
        
        for term in query_terms:
            search_conditions.append("(LOWER(title) LIKE ? OR LOWER(brand) LIKE ? OR LOWER(category) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        
        if search_conditions:
            where_clause = " AND ".join(search_conditions)
            sql_query = f"""
                SELECT * FROM products 
                WHERE {where_clause} AND is_in_stock = 1
                ORDER BY rating DESC, review_count DESC
                LIMIT ?
            """
            params.append(request.size * 2)  # Get more for ranking
        else:
            sql_query = """
                SELECT * FROM products 
                WHERE is_in_stock = 1
                ORDER BY rating DESC, review_count DESC
                LIMIT ?
            """
            params = [request.size * 2]
        
        cursor.execute(sql_query, params)
        raw_results = cursor.fetchall()
        conn.close()
        
        if not raw_results:
            # Track zero-results search
            background_tasks.add_task(
                track_search_event,
                actual_session_id,
                request.user_id,
                request.query,
                0,
                (time.time() - start_time) * 1000
            )
            
            return SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                page=request.page,
                size=request.size,
                response_time_ms=round((time.time() - start_time) * 1000, 2),
                session_id=actual_session_id
            )
        
        # Convert to list of dicts
        search_results = [dict(row) for row in raw_results]
        
        # Apply business scoring
        if business_scorer:
            try:
                product_ids = [r['id'] for r in search_results]
                base_scores = {r['id']: 0.8 for r in search_results}  # Base relevance
                
                business_scores = business_scorer.score_products(
                    product_ids, 
                    base_scores,
                    user_context={'user_id': request.user_id}
                )
                
                # Create mapping for quick lookup
                business_score_map = {bs.product_id: bs for bs in business_scores}
                
                # Update results with business scores
                for result in search_results:
                    if result['id'] in business_score_map:
                        bs = business_score_map[result['id']]
                        result['business_score'] = bs.business_score
                        result['final_score'] = bs.final_score
                        result['score_breakdown'] = bs.scoring_breakdown
                    else:
                        result['final_score'] = 0.5
                        
                # Sort by business score
                search_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
                        
            except Exception as e:
                logger.warning(f"Business scoring failed: {e}")
                # Continue without business scoring
        
        # Apply pagination
        start_idx = (request.page - 1) * request.size
        end_idx = start_idx + request.size
        paginated_results = search_results[start_idx:end_idx]
        
        # Format results
        formatted_results = []
        for i, result in enumerate(paginated_results):
            formatted_result = {
                "id": result['id'],
                "title": result['title'],
                "brand": result.get('brand'),
                "category": result['category'],
                "price": result['price'],
                "original_price": result.get('original_price'),
                "discount_percentage": result.get('discount_percentage', 0),
                "rating": result.get('rating'),
                "review_count": result.get('review_count', 0),
                "is_in_stock": result.get('is_in_stock', True),
                "delivery_days": result.get('delivery_days'),
                "seller_name": result.get('seller_name'),
                "is_flipkart_assured": result.get('is_flipkart_assured', False),
                "position": start_idx + i + 1,
                "relevance_score": round(result.get('final_score', 0.5), 3),
                "business_score": round(result.get('business_score', 0.5), 3)
            }
            formatted_results.append(formatted_result)
        
        response_time = time.time() - start_time
        
        # Track search event in background
        background_tasks.add_task(
            track_search_event,
            actual_session_id,
            request.user_id,
            request.query,
            len(search_results),
            response_time * 1000
        )
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(search_results),
            page=request.page,
            size=request.size,
            response_time_ms=round(response_time * 1000, 2),
            filters_applied=request.filters,
            sort_order=request.sort,
            session_id=actual_session_id
        )
        
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/autocomplete")
async def get_autocomplete(request: AutocompleteRequest):
    """
    🔮 Advanced autocomplete with spell correction and context awareness
    """
    
    if not autosuggest_engine:
        raise HTTPException(status_code=503, detail="Autosuggest engine not initialized")
    
    start_time = time.time()
    
    try:
        suggestions = autosuggest_engine.get_suggestions(
            request.query, 
            max_suggestions=request.max_suggestions
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "query": request.query,
            "suggestions": [
                {
                    "text": s.query,
                    "type": s.suggestion_type,
                    "score": round(s.score, 3),
                    "metadata": s.metadata
                }
                for s in suggestions
            ],
            "total_suggestions": len(suggestions),
            "response_time_ms": round(response_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")

@app.post("/track/click")
async def track_click(request: ClickTrackingRequest, background_tasks: BackgroundTasks):
    """
    📊 Track user clicks for analytics and ML model improvement
    """
    
    if not click_tracker:
        raise HTTPException(status_code=503, detail="Click tracker not initialized")
    
    try:
        # Track click event in background
        background_tasks.add_task(
            track_click_event,
            request.session_id,
            request.user_id,
            request.query,
            request.product_id,
            request.position,
            request.click_type
        )
        
        return {"status": "success", "message": "Click tracked"}
        
    except Exception as e:
        logger.error(f"Click tracking error: {e}")
        raise HTTPException(status_code=500, detail=f"Click tracking failed: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    💬 Collect user feedback for search result improvement
    """
    
    if not click_tracker:
        raise HTTPException(status_code=503, detail="Click tracker not initialized")
    
    try:
        # Track feedback in background
        background_tasks.add_task(
            track_feedback_event,
            request.session_id,
            request.user_id,
            request.query,
            request.product_id,
            request.feedback_type,
            request.feedback_text,
            request.position
        )
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback failed: {str(e)}")

@app.get("/metrics/dashboard")
async def get_metrics_dashboard(hours: int = Query(24, description="Time period in hours")):
    """
    📈 Get comprehensive search metrics dashboard
    """
    
    if not click_tracker:
        raise HTTPException(status_code=503, detail="Click tracker not initialized")
    
    try:
        search_metrics = click_tracker.get_search_metrics(hours)
        click_metrics = click_tracker.get_click_metrics(hours)
        conversion_metrics = click_tracker.get_conversion_metrics(hours)
        behavior_insights = click_tracker.get_user_behavior_insights(hours)
        
        return {
            "search_metrics": search_metrics,
            "click_metrics": click_metrics,
            "conversion_metrics": conversion_metrics,
            "behavior_insights": behavior_insights,
            "time_period_hours": hours,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

@app.get("/product/{product_id}")
async def get_product_details(product_id: str):
    """
    🛍️ Get detailed product information
    """
    
    try:
        db_path = str(Path(__file__).parent.parent.parent / "data" / "db" / "flipkart_products.db")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(product)
        
    except Exception as e:
        logger.error(f"Product details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get product details: {str(e)}")

# Background task functions
async def track_search_event(session_id: str, user_id: Optional[str], query: str, 
                           results_count: int, response_time_ms: float):
    """Background task to track search events"""
    if click_tracker and click_tracking_cls:
        search_event = click_tracking_cls.__dict__.get('SearchEvent')
        if search_event:
            event = search_event(
                session_id=session_id,
                user_id=user_id,
                query=query,
                timestamp=datetime.now(),
                results_count=results_count,
                response_time_ms=response_time_ms,
                search_type="text",
                filters_applied={},
                sort_order="relevance",
                page_number=1
            )
            click_tracker.track_search(event)

async def track_click_event(session_id: str, user_id: Optional[str], query: str,
                          product_id: str, position: int, click_type: str):
    """Background task to track click events"""
    if click_tracker:
        click_event = ClickEvent(
            session_id=session_id,
            user_id=user_id,
            query=query,
            product_id=product_id,
            position=position,
            timestamp=datetime.now(),
            click_type=click_type,
            page_number=1,
            total_results=50
        )
        click_tracker.track_click(click_event)

async def track_feedback_event(session_id: str, user_id: Optional[str], query: str,
                             product_id: Optional[str], feedback_type: str, 
                             feedback_text: Optional[str], position: Optional[int]):
    """Background task to track feedback events"""
    if click_tracker:
        feedback_event = FeedbackEvent(
            session_id=session_id,
            user_id=user_id,
            query=query,
            product_id=product_id,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            timestamp=datetime.now(),
            position=position
        )
        click_tracker.track_feedback(feedback_event)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
