"""
Hybrid Search API - Combines Smart Rules + ML Intelligence
===========================================================

This API provides hybrid search capabilities that combine:
1. Fast rule-based pattern matching (Smart System)
2. Semantic understanding with BERT embeddings (ML System)
3. Configurable weights and graceful fallbacks

Endpoints:
- /hybrid-search: Main hybrid search with ML + smart rules
- /neural-autosuggest: ML-powered autosuggest with semantic understanding
- /hybrid-analytics: Performance analytics for hybrid system
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.services.hybrid_ml_service import get_hybrid_ml_service, is_hybrid_ml_available
from app.schemas.product import SearchResponse, ProductResponse
from app.schemas.autosuggest import AutosuggestItem, AutosuggestResponse

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/hybrid", tags=["Hybrid ML Search"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str = Field(..., description="Search query", min_length=1)
    page: int = Field(default=1, description="Page number", ge=1)
    limit: int = Field(default=20, description="Results per page", ge=1, le=100)
    category: Optional[str] = Field(default=None, description="Filter by category")
    brand: Optional[str] = Field(default=None, description="Filter by brand")
    min_price: Optional[float] = Field(default=None, description="Minimum price", ge=0)
    max_price: Optional[float] = Field(default=None, description="Maximum price", ge=0)
    min_rating: Optional[float] = Field(default=None, description="Minimum rating", ge=0, le=5)
    sort_by: str = Field(default="relevance", description="Sort order")
    in_stock: bool = Field(default=True, description="Filter by stock availability")
    
    # Hybrid-specific parameters
    use_ml: bool = Field(default=True, description="Enable ML semantic search")
    ml_weight: Optional[float] = Field(default=None, description="ML weight (0.0-1.0)", ge=0.0, le=1.0)
    include_analysis: bool = Field(default=True, description="Include query analysis")


class NeuralAutosuggestRequest(BaseModel):
    """Request model for neural autosuggest"""
    query: str = Field(..., description="Query prefix", min_length=1)
    limit: int = Field(default=10, description="Maximum suggestions", ge=1, le=50)
    category: Optional[str] = Field(default=None, description="Filter by category")
    include_semantic: bool = Field(default=True, description="Include ML semantic suggestions")
    include_smart: bool = Field(default=True, description="Include smart rule-based suggestions")


class HybridAnalysisResponse(BaseModel):
    """Response model for hybrid query analysis"""
    query: str
    analysis_method: str
    analysis_time_ms: float
    smart_analysis: Dict[str, Any]
    ml_analysis: Optional[Dict[str, Any]]
    hybrid_confidence: float
    methods_used: Dict[str, bool]


class HybridSearchResponse(SearchResponse):
    """Extended search response with hybrid metadata"""
    hybrid_metadata: Optional[Dict[str, Any]] = None


class HybridAutosuggestResponse(AutosuggestResponse):
    """Extended autosuggest response with hybrid metadata"""
    hybrid_metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@router.post("/search", response_model=HybridSearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    🚀 Hybrid Search - Smart Rules + ML Semantics
    
    Combines fast rule-based pattern matching with semantic understanding:
    - Smart rules: <50ms, reliable, pattern-based
    - ML semantics: BERT embeddings, semantic similarity
    - Hybrid scoring: Configurable weights, graceful fallbacks
    
    Performance:
    - Smart only: ~50ms
    - Hybrid: ~100ms  
    - ML fallback: Automatic if ML fails
    """
    start_time = time.time()
    
    try:
        # Get hybrid ML service
        hybrid_service = get_hybrid_ml_service()
        
        # Perform hybrid search
        search_results = hybrid_service.search_products(
            db=db,
            query=request.query,
            page=request.page,
            limit=request.limit,
            category=request.category,
            brand=request.brand,
            min_price=request.min_price,
            max_price=request.max_price,
            min_rating=request.min_rating,
            sort_by=request.sort_by,
            in_stock=request.in_stock,
            use_ml=request.use_ml,
            ml_weight=request.ml_weight
        )
        
        # Add hybrid metadata
        search_time = (time.time() - start_time) * 1000
        hybrid_metadata = {
            'ml_available': hybrid_service.is_ml_available(),
            'embeddings_available': hybrid_service.is_embeddings_available(),
            'search_method': getattr(search_results.query_analysis, 'search_method', 'unknown') if hasattr(search_results, 'query_analysis') else 'unknown',
            'total_time_ms': search_time,
            'weights_used': getattr(search_results.query_analysis, 'weights_used', {}) if hasattr(search_results, 'query_analysis') else {},
            'request_params': {
                'use_ml': request.use_ml,
                'ml_weight': request.ml_weight,
                'include_analysis': request.include_analysis
            }
        }
        
        # Create hybrid response
        hybrid_response = HybridSearchResponse(
            **search_results.dict(),
            hybrid_metadata=hybrid_metadata
        )
        
        logger.info(f"Hybrid search completed in {search_time:.1f}ms - Method: {hybrid_metadata['search_method']}")
        return hybrid_response
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@router.get("/neural-autosuggest", response_model=HybridAutosuggestResponse)
async def neural_autosuggest(
    query: str = Query(..., description="Query prefix", min_length=1),
    limit: int = Query(default=10, description="Maximum suggestions", ge=1, le=50),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    include_semantic: bool = Query(default=True, description="Include ML semantic suggestions"),
    include_smart: bool = Query(default=True, description="Include smart rule-based suggestions"),
    db: Session = Depends(get_db)
):
    """
    🧠 Neural Autosuggest - Smart + ML Suggestions
    
    Combines rule-based and ML-powered autosuggest:
    - Smart suggestions: Fast pattern matching, brand/category aware
    - Semantic suggestions: BERT embeddings, similar query completion
    - Hybrid ranking: Best of both approaches
    
    Performance:
    - Smart only: ~30ms
    - Hybrid: ~80ms
    - Automatic fallback if ML unavailable
    """
    start_time = time.time()
    
    try:
        # Get hybrid ML service
        hybrid_service = get_hybrid_ml_service()
        
        # Generate hybrid suggestions
        suggestions = hybrid_service.get_hybrid_suggestions(
            db=db,
            query=query,
            limit=limit,
            category=category,
            include_semantic=include_semantic,
            include_smart=include_smart
        )
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Add hybrid metadata
        hybrid_metadata = {
            'ml_available': hybrid_service.is_ml_available(),
            'suggestions_method': 'hybrid' if (include_semantic and include_smart) else ('ml_only' if include_semantic else 'smart_only'),
            'total_suggestions': len(suggestions),
            'response_time_ms': response_time,
            'request_params': {
                'include_semantic': include_semantic,
                'include_smart': include_smart,
                'category_filter': category
            }
        }
        
        # Create response
        hybrid_response = HybridAutosuggestResponse(
            query=query,
            suggestions=suggestions,
            total_count=len(suggestions),
            response_time_ms=response_time,
            hybrid_metadata=hybrid_metadata
        )
        
        logger.info(f"Neural autosuggest completed in {response_time:.1f}ms - {len(suggestions)} suggestions")
        return hybrid_response
        
    except Exception as e:
        logger.error(f"Neural autosuggest error: {e}")
        raise HTTPException(status_code=500, detail=f"Neural autosuggest failed: {str(e)}")


@router.get("/analyze", response_model=HybridAnalysisResponse)
async def hybrid_query_analysis(
    query: str = Query(..., description="Query to analyze", min_length=1),
    db: Session = Depends(get_db)
):
    """
    🔍 Hybrid Query Analysis - Smart + ML Insights
    
    Analyzes queries using both approaches:
    - Smart analysis: Rule-based entity extraction, patterns
    - ML analysis: BERT embeddings, semantic classification
    - Hybrid confidence: Combined confidence scoring
    """
    start_time = time.time()
    
    try:
        # Get hybrid ML service
        hybrid_service = get_hybrid_ml_service()
        
        # Perform hybrid analysis
        analysis = hybrid_service.analyze_query(query, db)
        
        # Structure response
        response = HybridAnalysisResponse(
            query=query,
            analysis_method=analysis.get('analysis_method', 'unknown'),
            analysis_time_ms=analysis.get('analysis_time_ms', 0),
            smart_analysis={
                'query_type': analysis.get('query_type'),
                'sentiment': analysis.get('sentiment'),
                'brands': analysis.get('brands', []),
                'categories': analysis.get('categories', []),
                'price_range': analysis.get('price_range'),
                'modifiers': analysis.get('modifiers', []),
                'confidence': analysis.get('confidence', 0)
            },
            ml_analysis=analysis.get('semantic_analysis'),
            hybrid_confidence=analysis.get('hybrid_confidence', analysis.get('confidence', 0)),
            methods_used=analysis.get('methods_used', {})
        )
        
        logger.info(f"Hybrid analysis completed in {response.analysis_time_ms:.1f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Hybrid analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid analysis failed: {str(e)}")


# =============================================================================
# ANALYTICS & MONITORING
# =============================================================================

@router.get("/health")
async def hybrid_system_health():
    """
    ❤️ Hybrid System Health Check
    
    Returns status of all hybrid components:
    - Smart rule system status
    - ML components availability
    - Performance metrics
    """
    try:
        hybrid_service = get_hybrid_ml_service()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'smart_system': {
                    'available': True,
                    'status': 'operational',
                    'description': 'Rule-based pattern matching system'
                },
                'ml_system': {
                    'available': hybrid_service.is_ml_available(),
                    'status': 'operational' if hybrid_service.is_ml_available() else 'unavailable',
                    'description': 'BERT-based semantic search system'
                },
                'embeddings': {
                    'available': hybrid_service.is_embeddings_available(),
                    'status': 'operational' if hybrid_service.is_embeddings_available() else 'not_loaded',
                    'description': 'Product embeddings for semantic search'
                }
            },
            'config': {
                'model_name': hybrid_service.config.get('model_name', 'unknown'),
                'embedding_dim': hybrid_service.config.get('embedding_dim', 0),
                'ml_weight': hybrid_service.config.get('ml_weight', 0),
                'smart_weight': hybrid_service.config.get('smart_weight', 0)
            },
            'performance': {
                'cache_size': len(hybrid_service.query_embeddings_cache),
                'max_cache_size': hybrid_service.config.get('max_cache_size', 0)
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


@router.get("/config")
async def get_hybrid_config():
    """
    ⚙️ Get Hybrid System Configuration
    
    Returns current configuration and settings
    """
    try:
        hybrid_service = get_hybrid_ml_service()
        
        return {
            'config': hybrid_service.config,
            'capabilities': {
                'ml_available': hybrid_service.is_ml_available(),
                'embeddings_available': hybrid_service.is_embeddings_available(),
                'smart_system': True
            },
            'model_info': {
                'sentence_transformer': hybrid_service.config.get('model_name'),
                'embedding_dimension': hybrid_service.config.get('embedding_dim'),
                'cache_status': {
                    'current_size': len(hybrid_service.query_embeddings_cache),
                    'max_size': hybrid_service.config.get('max_cache_size')
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Config retrieval failed: {str(e)}")


@router.post("/config")
async def update_hybrid_config(
    ml_weight: Optional[float] = Query(default=None, description="ML weight (0.0-1.0)", ge=0.0, le=1.0),
    similarity_threshold: Optional[float] = Query(default=None, description="Similarity threshold", ge=0.0, le=1.0),
    max_cache_size: Optional[int] = Query(default=None, description="Max cache size", ge=100)
):
    """
    ⚙️ Update Hybrid System Configuration
    
    Allows runtime configuration updates
    """
    try:
        hybrid_service = get_hybrid_ml_service()
        
        updates = {}
        if ml_weight is not None:
            hybrid_service.config['ml_weight'] = ml_weight
            hybrid_service.config['smart_weight'] = 1.0 - ml_weight
            updates['ml_weight'] = ml_weight
            updates['smart_weight'] = 1.0 - ml_weight
            
        if similarity_threshold is not None:
            hybrid_service.config['similarity_threshold'] = similarity_threshold
            updates['similarity_threshold'] = similarity_threshold
            
        if max_cache_size is not None:
            hybrid_service.config['max_cache_size'] = max_cache_size
            updates['max_cache_size'] = max_cache_size
            
            # Clear cache if it's too large
            if len(hybrid_service.query_embeddings_cache) > max_cache_size:
                hybrid_service.query_embeddings_cache.clear()
        
        return {
            'status': 'updated',
            'timestamp': datetime.utcnow().isoformat(),
            'updates': updates,
            'current_config': hybrid_service.config
        }
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/compare")
async def compare_search_methods(
    query: str = Query(..., description="Query to compare", min_length=1),
    limit: int = Query(default=10, description="Results per method", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    ⚖️ Compare Search Methods
    
    Compare results from different search approaches:
    - Smart rules only
    - ML semantics only  
    - Hybrid combination
    """
    start_time = time.time()
    
    try:
        hybrid_service = get_hybrid_ml_service()
        
        results = {
            'query': query,
            'timestamp': datetime.utcnow().isoformat(),
            'methods': {}
        }
        
        # Smart-only search
        try:
            smart_start = time.time()
            smart_results = hybrid_service.search_products(
                db=db, query=query, limit=limit, use_ml=False
            )
            smart_time = (time.time() - smart_start) * 1000
            
            results['methods']['smart_only'] = {
                'time_ms': smart_time,
                'total_results': smart_results.total_count,
                'top_products': [p.title for p in smart_results.products[:5]],
                'status': 'success'
            }
        except Exception as e:
            results['methods']['smart_only'] = {'status': 'error', 'error': str(e)}
        
        # ML-only search (if available)
        if hybrid_service.is_ml_available():
            try:
                ml_start = time.time()
                # For prototype, this uses hybrid with high ML weight
                ml_results = hybrid_service.search_products(
                    db=db, query=query, limit=limit, use_ml=True, ml_weight=0.9
                )
                ml_time = (time.time() - ml_start) * 1000
                
                results['methods']['ml_semantic'] = {
                    'time_ms': ml_time,
                    'total_results': ml_results.total_count,
                    'top_products': [p.title for p in ml_results.products[:5]],
                    'status': 'success'
                }
            except Exception as e:
                results['methods']['ml_semantic'] = {'status': 'error', 'error': str(e)}
        else:
            results['methods']['ml_semantic'] = {'status': 'unavailable', 'reason': 'ML components not loaded'}
        
        # Hybrid search
        try:
            hybrid_start = time.time()
            hybrid_results = hybrid_service.search_products(
                db=db, query=query, limit=limit, use_ml=True
            )
            hybrid_time = (time.time() - hybrid_start) * 1000
            
            results['methods']['hybrid'] = {
                'time_ms': hybrid_time,
                'total_results': hybrid_results.total_count,
                'top_products': [p.title for p in hybrid_results.products[:5]],
                'status': 'success'
            }
        except Exception as e:
            results['methods']['hybrid'] = {'status': 'error', 'error': str(e)}
        
        # Summary
        total_time = (time.time() - start_time) * 1000
        results['summary'] = {
            'total_comparison_time_ms': total_time,
            'fastest_method': min(
                [method for method in results['methods'].values() 
                 if method.get('status') == 'success'],
                key=lambda x: x.get('time_ms', float('inf')),
                default={'time_ms': 0}
            ).get('time_ms', 0)
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# =============================================================================
# ROUTER METADATA
# =============================================================================

# Add router tags and metadata for documentation
router.tags = ["Hybrid ML Search"]
router.responses = {
    500: {"description": "Internal Server Error"},
    404: {"description": "Not Found"},
    422: {"description": "Validation Error"}
}
