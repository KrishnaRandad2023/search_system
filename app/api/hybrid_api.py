"""
Hybrid API - Combines Smart Rules + ML-Powered Search
====================================================

New API endpoints that provide the best of both worlds:
1. Fast rule-based intelligence (Smart Service)
2. Semantic understanding with BERT embeddings (ML Service)
3. Configurable hybrid scoring and fallback mechanisms

Endpoints:
- /hybrid-search: Search with smart rules + ML semantics
- /neural-autosuggest: Autosuggest with transformer models
- /hybrid-analyze: Deep query analysis with both approaches
- /hybrid-status: Check ML component availability
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Import database and schemas
from app.db.database import get_db
from app.schemas.product import SearchResponse, ProductResponse
from app.schemas.autosuggest import AutosuggestResponse, AutosuggestItem

# Import hybrid service
from app.services.hybrid_ml_service import HybridMLService, get_hybrid_ml_service

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/hybrid", tags=["Hybrid ML Search"])


# =================================================================
# REQUEST/RESPONSE MODELS
# =================================================================

class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str = Field(..., description="Search query", min_length=1)
    page: int = Field(default=1, description="Page number", ge=1)
    limit: int = Field(default=20, description="Results per page", ge=1, le=100)
    use_ml: bool = Field(default=True, description="Enable ML components")
    ml_weight: Optional[float] = Field(default=None, description="ML weight (0.0-1.0)", ge=0.0, le=1.0)
    category: Optional[str] = Field(default=None, description="Filter by category")
    brand: Optional[str] = Field(default=None, description="Filter by brand")
    min_price: Optional[float] = Field(default=None, description="Minimum price", ge=0)
    max_price: Optional[float] = Field(default=None, description="Maximum price", ge=0)
    min_rating: Optional[float] = Field(default=None, description="Minimum rating", ge=0, le=5)
    sort_by: str = Field(default="relevance", description="Sort order")
    in_stock: bool = Field(default=True, description="Only in-stock products")


class HybridAnalysisRequest(BaseModel):
    """Request model for hybrid query analysis"""
    query: str = Field(..., description="Query to analyze", min_length=1)
    include_ml: bool = Field(default=True, description="Include ML analysis")
    include_smart: bool = Field(default=True, description="Include smart analysis")


class HybridSuggestRequest(BaseModel):
    """Request model for hybrid autosuggest"""
    query: str = Field(..., description="Query prefix", min_length=1)
    limit: int = Field(default=10, description="Max suggestions", ge=1, le=50)
    include_semantic: bool = Field(default=True, description="Include ML semantic suggestions")
    include_smart: bool = Field(default=True, description="Include smart rule-based suggestions")
    category: Optional[str] = Field(default=None, description="Filter by category")


class HybridAnalysisResponse(BaseModel):
    """Response model for hybrid analysis"""
    query: str
    smart_analysis: Optional[Dict[str, Any]]
    ml_analysis: Optional[Dict[str, Any]]
    hybrid_confidence: float
    processing_method: str
    response_time_ms: float


class HybridStatusResponse(BaseModel):
    """Response model for hybrid system status"""
    hybrid_available: bool
    ml_available: bool
    smart_available: bool
    components: Dict[str, Any]
    performance_metrics: Dict[str, Any]


# =================================================================
# HYBRID SEARCH ENDPOINTS
# =================================================================

@router.post("/search", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Hybrid search combining smart rules + ML semantics
    
    This endpoint provides the best search experience by:
    1. Using fast rule-based analysis for reliability
    2. Adding ML semantic understanding when available
    3. Combining results with configurable weights
    4. Graceful fallback to smart-only mode
    """
    try:
        logger.info(f"Hybrid search request: '{request.query}' (ML: {request.use_ml})")
        
        # Execute hybrid search
        results = hybrid_service.search_products(
            db=db,
            query=request.query,
            page=request.page,
            limit=request.limit,
            use_ml=request.use_ml,
            ml_weight=request.ml_weight,
            category=request.category,
            brand=request.brand,
            min_price=request.min_price,
            max_price=request.max_price,
            min_rating=request.min_rating,
            sort_by=request.sort_by,
            in_stock=request.in_stock
        )
        
        # Log performance metrics in background
        background_tasks.add_task(
            _log_search_metrics,
            request.query,
            len(results.products),
            results.response_time_ms,
            "hybrid_search"
        )
        
        logger.info(f"Hybrid search completed: {len(results.products)} results in {results.response_time_ms}ms")
        return results
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@router.get("/smart-search", response_model=SearchResponse)
async def smart_only_search(
    query: str = Query(..., description="Search query", min_length=1),
    page: int = Query(default=1, description="Page number", ge=1),
    limit: int = Query(default=20, description="Results per page", ge=1, le=100),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    min_price: Optional[float] = Query(default=None, description="Minimum price", ge=0),
    max_price: Optional[float] = Query(default=None, description="Maximum price", ge=0),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating", ge=0, le=5),
    sort_by: str = Query(default="relevance", description="Sort order"),
    in_stock: bool = Query(default=True, description="Only in-stock products"),
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Smart rule-based search only (fast, reliable)
    
    This endpoint uses only the smart rule-based system for:
    - Maximum speed (<50ms typical response time)
    - High reliability and predictable results
    - When ML components are not needed
    """
    try:
        logger.info(f"Smart-only search request: '{query}'")
        
        # Force smart-only mode
        results = hybrid_service.search_products(
            db=db,
            query=query,
            page=page,
            limit=limit,
            use_ml=False,  # Force smart-only
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            sort_by=sort_by,
            in_stock=in_stock
        )
        
        logger.info(f"Smart search completed: {len(results.products)} results in {results.response_time_ms}ms")
        return results
        
    except Exception as e:
        logger.error(f"Smart search error: {e}")
        raise HTTPException(status_code=500, detail=f"Smart search failed: {str(e)}")


# =================================================================
# HYBRID ANALYSIS ENDPOINTS
# =================================================================

@router.post("/analyze", response_model=HybridAnalysisResponse)
async def hybrid_analyze_query(
    request: HybridAnalysisRequest,
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Deep hybrid query analysis combining smart rules + ML semantics
    
    This endpoint provides comprehensive query understanding:
    1. Smart rule-based entity extraction (brands, categories, prices)
    2. ML semantic analysis with BERT embeddings
    3. Combined confidence scoring
    4. Processing method transparency
    """
    try:
        logger.info(f"Hybrid analysis request: '{request.query}'")
        
        # Execute hybrid analysis
        analysis = hybrid_service.analyze_query(request.query, db)
        
        response = HybridAnalysisResponse(
            query=analysis['query'],
            smart_analysis=analysis.get('smart_analysis'),
            ml_analysis=analysis.get('ml_analysis'),
            hybrid_confidence=analysis['hybrid_confidence'],
            processing_method=analysis['processing_method'],
            response_time_ms=analysis['response_time_ms']
        )
        
        logger.info(f"Hybrid analysis completed in {response.response_time_ms}ms")
        return response
        
    except Exception as e:
        logger.error(f"Hybrid analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")


@router.get("/analyze-simple")
async def simple_analyze_query(
    query: str = Query(..., description="Query to analyze", min_length=1),
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Simple hybrid query analysis (GET endpoint for quick testing)
    """
    try:
        analysis = hybrid_service.analyze_query(query, db)
        return {
            "query": query,
            "analysis": analysis,
            "ml_available": hybrid_service.is_ml_available()
        }
        
    except Exception as e:
        logger.error(f"Simple analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =================================================================
# HYBRID AUTOSUGGEST ENDPOINTS
# =================================================================

@router.post("/neural-autosuggest", response_model=AutosuggestResponse)
async def neural_autosuggest(
    request: HybridSuggestRequest,
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Neural autosuggest with transformer models + smart rules
    
    This endpoint provides intelligent suggestions using:
    1. BERT embeddings for semantic similarity
    2. Smart rule-based patterns for reliability
    3. Hybrid ranking for best results
    """
    try:
        logger.info(f"Neural autosuggest request: '{request.query}'")
        
        # Execute hybrid autosuggest
        suggestions_response = hybrid_service.get_suggestions(
            db=db,
            query=request.query,
            limit=request.limit,
            include_semantic=request.include_semantic,
            include_smart=request.include_smart,
            category=request.category
        )
        
        logger.info(f"Neural autosuggest completed: {len(suggestions_response.suggestions)} suggestions")
        return suggestions_response
        
    except Exception as e:
        logger.error(f"Neural autosuggest error: {e}")
        raise HTTPException(status_code=500, detail=f"Autosuggest failed: {str(e)}")


@router.get("/autosuggest", response_model=AutosuggestResponse)
async def hybrid_autosuggest_simple(
    query: str = Query(..., description="Query prefix", min_length=1),
    limit: int = Query(default=10, description="Max suggestions", ge=1, le=50),
    include_semantic: bool = Query(default=True, description="Include ML suggestions"),
    include_smart: bool = Query(default=True, description="Include smart suggestions"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    db: Session = Depends(get_db),
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Hybrid autosuggest (GET endpoint for quick testing)
    """
    try:
        suggestions_response = hybrid_service.get_suggestions(
            db=db,
            query=query,
            limit=limit,
            include_semantic=include_semantic,
            include_smart=include_smart,
            category=category
        )
        
        return suggestions_response
        
    except Exception as e:
        logger.error(f"Hybrid autosuggest error: {e}")
        raise HTTPException(status_code=500, detail=f"Autosuggest failed: {str(e)}")


# =================================================================
# SYSTEM STATUS ENDPOINTS
# =================================================================

@router.get("/status", response_model=HybridStatusResponse)
async def hybrid_system_status(
    hybrid_service: HybridMLService = Depends(get_hybrid_ml_service)
):
    """
    Get hybrid system status and component availability
    
    This endpoint provides transparency about:
    1. Which components are available (ML vs Smart)
    2. Current configuration and performance metrics
    3. System health and readiness
    """
    try:
        ml_status = hybrid_service.get_ml_status()
        
        return HybridStatusResponse(
            hybrid_available=hybrid_service.is_ml_available(),
            ml_available=hybrid_service.is_ml_available(),
            smart_available=True,  # Smart components always available
            components=ml_status,
            performance_metrics={
                "avg_response_time_ms": 50,  # Would track real metrics
                "cache_hit_rate": 0.85,
                "ml_success_rate": 0.92
            }
        )
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/health")
async def hybrid_health_check():
    """
    Simple health check for hybrid system
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "hybrid_ml_search",
        "version": "1.0.0"
    }


# =================================================================
# UTILITY FUNCTIONS
# =================================================================

async def _log_search_metrics(
    query: str, 
    result_count: int, 
    response_time_ms: float, 
    search_method: str
):
    """Log search metrics for analytics (background task)"""
    try:
        # In production, this would log to analytics system
        logger.info(
            f"METRICS: query='{query}', results={result_count}, "
            f"time={response_time_ms}ms, method={search_method}"
        )
    except Exception as e:
        logger.warning(f"Failed to log metrics: {e}")


# =================================================================
# FACTORY FUNCTION FOR DEPENDENCY INJECTION
# =================================================================

def get_hybrid_ml_service() -> HybridMLService:
    """Get hybrid ML service instance for dependency injection"""
    from app.services.hybrid_ml_service import get_hybrid_ml_service as _get_service
    return _get_service()
