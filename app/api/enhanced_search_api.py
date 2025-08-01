"""
🔥 Enhanced FastAPI Search API for Flipkart Grid 7.0
Industry-level search system with comprehensive features:
- Hybrid search (semantic + lexical)
- ML-powered ranking with business logic
- Advanced autosuggest with spell correction
- Real-time click tracking & analytics
- Performance monitoring & metrics
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
import asyncio
import psutil
import sys
import uuid
import sqlite3
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.search.autosuggest_engine import AdvancedAutosuggestEngine, SuggestionResult
    from app.core.business_scoring import BusinessScoringEngine
    from app.core.click_tracking import ClickTrackingSystem, SearchEvent, ClickEvent, FeedbackEvent
    from app.search.hybrid_engine import HybridSearchEngine
    from app.ml.ranker import MLRanker
    HAS_IMPORTS = True
except ImportError as e:
    print(f"Import error: {e}")
    HAS_IMPORTS = False
    # We'll handle these as Any types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="🔥 Flipkart Grid Search API",
    description="Industry-level search system with AI/ML ranking and comprehensive analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
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

class ProductDetails(BaseModel):
    id: str
    title: str
    brand: Optional[str]
    category: str
    price: float
    rating: Optional[float]
    review_count: Optional[int]
    image_url: Optional[str]
    is_in_stock: bool
    delivery_days: Optional[int]
    discount_percentage: Optional[int] = 0

# Global components - using Any to avoid type conflicts
search_engine: Any = None
autosuggest_engine: Any = None
ml_ranker: Any = None
business_scorer: Any = None
click_tracker: Any = None

# Startup time for uptime calculation
app_start_time = datetime.now()

@app.on_event("startup")
async def initialize_components():
    """Initialize all search components on startup"""
    global search_engine, autosuggest_engine, ml_ranker, business_scorer, click_tracker
    
    logger.info("🚀 Initializing Flipkart Grid Search System...")
    
    try:
        # Database and data paths
        base_dir = Path(__file__).parent.parent.parent
        db_path = str(base_dir / "data" / "db" / "flipkart_products.db")
        data_dir = base_dir / "data"
        models_dir = base_dir / "data" / "models"
        
        # Check if database exists
        if not Path(db_path).exists():
            logger.error(f"❌ Database not found at {db_path}")
            logger.error("Please run: python scripts/generate_flipkart_products.py")
            return
            
        # Initialize components with proper error handling
        logger.info("Loading search engine...")
        if HAS_IMPORTS:
            # Use the factory function for HybridSearchEngine
            from app.search.hybrid_engine import load_or_create_search_engine
            search_engine = load_or_create_search_engine(
                data_path=str(data_dir / "products.csv"),  # May need to adjust path
                model_path=str(models_dir),
                embedding_model_name='all-MiniLM-L6-v2'
            )
            
            logger.info("Loading autosuggest engine...")
            autosuggest_engine = AdvancedAutosuggestEngine(data_dir, db_path)
            
            logger.info("Loading ML ranker...")
            ml_ranker = MLRanker()
            
            logger.info("Loading business scorer...")
            business_scorer = BusinessScoringEngine(db_path)
            
            logger.info("Loading click tracker...")
            click_tracker = ClickTrackingSystem(db_path)
        else:
            logger.warning("⚠️ Running in fallback mode - imports failed")
            # Create dummy components
            search_engine = None
            autosuggest_engine = None
            ml_ranker = None
            business_scorer = None
            click_tracker = None
        
        logger.info("✅ All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        # Don't raise to allow API to start in degraded mode
        search_engine = None
        autosuggest_engine = None
        ml_ranker = None
        business_scorer = None
        click_tracker = None

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
        "search_engine": search_engine is not None,
        "autosuggest_engine": autosuggest_engine is not None,
        "ml_ranker": ml_ranker is not None,
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

@app.post("/search", response_model=SearchResponse)
async def search_products(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_session_id)
):
    """
    🔍 Main search endpoint with hybrid search + ML ranking + business logic
    """
    
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
        
    start_time = time.time()
    
    try:
        # Use provided session_id or generate one
        actual_session_id = request.session_id or session_id
        
        # 1. Perform hybrid search
        search_results = search_engine.search(
            query=request.query,
            top_k=request.size * 3,  # Get more results for ranking
            filters=request.filters
        )
        
        if not search_results:
            # Track zero-results search
            background_tasks.add_task(
                track_search_event,
                actual_session_id,
                request.user_id,
                request.query,
                0,
                time.time() - start_time
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
        
        # 2. Apply ML ranking
        if ml_ranker:
            try:
                # Prepare features for ranking
                features = []
                product_ids = []
                base_scores = {}
                
                for result in search_results:
                    product_ids.append(result['product_id'])
                    base_scores[result['product_id']] = result['score']
                    
                    # Extract features for ML ranker
                    features.append([
                        result['score'],  # Base relevance score
                        result.get('rating', 0),
                        result.get('review_count', 0),
                        result.get('price', 0),
                        1 if result.get('is_in_stock', False) else 0,
                        result.get('discount_percentage', 0) / 100,
                    ])
                
                # Get ML scores
                ml_scores = ml_ranker.predict_scores(features)
                
                # Update results with ML scores
                for i, result in enumerate(search_results):
                    result['ml_score'] = float(ml_scores[i])
                    
            except Exception as e:
                logger.warning(f"ML ranking failed: {e}")
                # Continue without ML ranking
                for result in search_results:
                    result['ml_score'] = result['score']
        
        # 3. Apply business scoring
        if business_scorer:
            try:
                product_ids = [r['product_id'] for r in search_results]
                base_scores = {r['product_id']: r.get('ml_score', r['score']) for r in search_results}
                
                business_scores = business_scorer.score_products(
                    product_ids, 
                    base_scores,
                    user_context={'user_id': request.user_id}
                )
                
                # Create mapping for quick lookup
                business_score_map = {bs.product_id: bs for bs in business_scores}
                
                # Update results with business scores
                for result in search_results:
                    if result['product_id'] in business_score_map:
                        bs = business_score_map[result['product_id']]
                        result['business_score'] = bs.business_score
                        result['final_score'] = bs.final_score
                        result['score_breakdown'] = bs.scoring_breakdown
                    else:
                        result['final_score'] = result.get('ml_score', result['score'])
                        
            except Exception as e:
                logger.warning(f"Business scoring failed: {e}")
                # Use ML scores as final scores
                for result in search_results:
                    result['final_score'] = result.get('ml_score', result['score'])
        
        # 4. Sort by final score
        search_results.sort(key=lambda x: x.get('final_score', x['score']), reverse=True)
        
        # 5. Apply pagination
        start_idx = (request.page - 1) * request.size
        end_idx = start_idx + request.size
        paginated_results = search_results[start_idx:end_idx]
        
        # 6. Format results
        formatted_results = []
        for i, result in enumerate(paginated_results):
            formatted_result = {
                "id": result['product_id'],
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
                "image_urls": result.get('image_urls', []),
                "position": start_idx + i + 1,
                "relevance_score": round(result.get('final_score', result['score']), 3),
                "tags": result.get('tags', [])
            }
            formatted_results.append(formatted_result)
        
        response_time = time.time() - start_time
        
        # 7. Track search event in background
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
        logger.error(f"Search error: {e}")
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

@app.get("/metrics/search")
async def get_search_metrics(hours: int = Query(24, description="Time period in hours")):
    """
    📈 Get search performance metrics and analytics
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
            "time_period_hours": hours
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
    if click_tracker:
        search_event = SearchEvent(
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
        click_tracker.track_search(search_event)

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
            total_results=50  # Default
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

# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
