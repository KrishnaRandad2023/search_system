"""
Hybrid ML Service - Combines Smart Rules + ML Intelligence
=========================================================

This service provides the best of both worlds:
1. Fast rule-based pattern matching (Smart System)
2. Semantic understanding with BERT embeddings (ML System)
3. Graceful fallbacks and hybrid scoring

Architecture:
- Smart Components: QueryAnalyzerService, SmartSearchService
- ML Components: BERT embeddings, FAISS vector search
- Hybrid Logic: Combines both approaches with configurable weights
"""

import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

# Import existing smart components
from app.services.query_analyzer_service import QueryAnalyzerService, get_query_analyzer
from app.services.smart_search_service import SmartSearchService, get_smart_search_service
from app.schemas.product import SearchResponse, ProductResponse
from app.schemas.autosuggest import AutosuggestItem, AutosuggestResponse

# Import ML components with safe fallbacks
try:
    from app.search.hybrid_engine import HybridSearchEngine, FAISSVectorIndex
    HYBRID_ENGINE_AVAILABLE = True
except ImportError:
    HYBRID_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class HybridMLService:
    """
    Hybrid ML Service combining Smart Rules + ML Intelligence
    
    Features:
    - Fast rule-based analysis (50ms) + Semantic ML analysis
    - BERT embeddings for semantic search
    - FAISS vector similarity search
    - Graceful fallbacks (ML → Smart → Basic)
    - Configurable hybrid weights
    """
    
    def __init__(self):
        self.ml_available = False
        self.embeddings_available = False
        
        # Initialize smart components (always available)
        self.smart_analyzer = get_query_analyzer()
        self.smart_search = get_smart_search_service()
        
        # Initialize ML components (with fallbacks)
        self.sentence_transformer = None
        self.faiss_index = None
        self.hybrid_engine = None
        self.product_embeddings = None
        self.query_embeddings_cache = {}
        
        # Configuration
        self.config = {
            'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
            'embedding_dim': 384,
            'ml_weight': 0.6,
            'smart_weight': 0.4,
            'similarity_threshold': 0.7,
            'max_cache_size': 1000
        }
        
        self._initialize_ml_components()
        logger.info(f"HybridMLService initialized - ML Available: {self.ml_available}")
    
    def _initialize_ml_components(self):
        """Initialize ML components with error handling"""
        try:
            # Initialize BERT model
            logger.info("Loading BERT model: all-MiniLM-L6-v2...")
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ BERT model loaded successfully")
            
            # Initialize FAISS index
            if HYBRID_ENGINE_AVAILABLE:
                self.faiss_index = FAISSVectorIndex()
                logger.info("✅ FAISS index initialized")
            
            # Load product embeddings if available
            self._load_product_embeddings()
            
            self.ml_available = True
            
        except Exception as e:
            logger.warning(f"ML components initialization failed: {e}")
            logger.info("Falling back to smart rule-based system only")
            self.ml_available = False
    
    def _load_product_embeddings(self):
        """Load or generate product embeddings"""
        embeddings_path = Path("data/embeddings/product_embeddings.npy")
        metadata_path = Path("data/embeddings/embedding_metadata.json")
        
        try:
            if embeddings_path.exists() and metadata_path.exists():
                logger.info("Loading existing product embeddings...")
                self.product_embeddings = np.load(embeddings_path)
                
                with open(metadata_path, 'r') as f:
                    embedding_metadata = json.load(f)
                    
                logger.info(f"✅ Loaded {len(self.product_embeddings)} product embeddings")
                self.embeddings_available = True
            else:
                logger.warning("Product embeddings not found - will generate on first search")
                self.embeddings_available = False
                
        except Exception as e:
            logger.error(f"Error loading product embeddings: {e}")
            self.embeddings_available = False
    
    def is_ml_available(self) -> bool:
        """Check if ML components are available"""
        return self.ml_available and self.sentence_transformer is not None
    
    def is_embeddings_available(self) -> bool:
        """Check if product embeddings are available"""
        return self.embeddings_available and self.product_embeddings is not None
    
    # =============================================================================
    # HYBRID QUERY ANALYSIS
    # =============================================================================
    
    def analyze_query(self, query: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Hybrid query analysis combining smart rules + ML semantics
        
        Returns:
            Combined analysis with both rule-based and semantic insights
        """
        start_time = time.time()
        
        # Set database for smart analyzer
        if db:
            self.smart_analyzer.db = db
        
        # Get smart analysis (always available)
        smart_analysis = self.smart_analyzer.analyze_query(query)
        
        result = {
            'query': query,
            'smart_analysis': {
                'query_type': smart_analysis.query_type,
                'sentiment': smart_analysis.sentiment,
                'brands': smart_analysis.brands,
                'categories': smart_analysis.categories,
                'price_range': smart_analysis.price_range,
                'modifiers': smart_analysis.modifiers,
                'confidence': smart_analysis.confidence
            },
            'ml_analysis': None,
            'hybrid_confidence': smart_analysis.confidence,
            'processing_method': 'smart_only',
            'response_time_ms': 0
        }
        
        # Add ML analysis if available
        if self.is_ml_available():
            try:
                ml_analysis = self._ml_analyze_query(query)
                result['ml_analysis'] = ml_analysis
                result['hybrid_confidence'] = self._combine_confidence_scores(
                    smart_analysis.confidence, 
                    ml_analysis.get('confidence', 0.5)
                )
                result['processing_method'] = 'hybrid'
            except Exception as e:
                logger.warning(f"ML analysis failed, using smart only: {e}")
        
        result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        return result
    
    def _ml_analyze_query(self, query: str) -> Dict[str, Any]:
        """ML-based semantic query analysis"""
        # Get query embedding
        query_embedding = self._get_query_embedding(query)
        
        ml_analysis = {
            'semantic_embedding': query_embedding.tolist(),
            'embedding_dim': len(query_embedding),
            'semantic_confidence': self._calculate_semantic_confidence(query_embedding)
        }
        
        # Find similar queries if embeddings available
        if self.is_embeddings_available():
            similar_queries = self._find_similar_queries(query_embedding)
            ml_analysis['similar_queries'] = similar_queries
        
        # Extract semantic intent
        semantic_intent = self._extract_semantic_intent(query, query_embedding)
        ml_analysis['semantic_intent'] = semantic_intent
        
        return ml_analysis
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get query embedding with caching"""
        # Check cache first
        if query in self.query_embeddings_cache:
            return self.query_embeddings_cache[query]
        
        # Ensure transformer is available
        if not self.sentence_transformer:
            raise ValueError("Sentence transformer not available")
        
        # Generate embedding and convert to numpy
        embedding = self.sentence_transformer.encode(query, normalize_embeddings=True)
        embedding = np.array(embedding)
        
        # Cache with size limit
        if len(self.query_embeddings_cache) < self.config['max_cache_size']:
            self.query_embeddings_cache[query] = embedding
        
        return embedding
    
    def _calculate_semantic_confidence(self, query_embedding: np.ndarray) -> float:
        """Calculate confidence score for semantic analysis"""
        # Simple confidence based on embedding magnitude and entropy
        magnitude = np.linalg.norm(query_embedding)
        entropy = -np.sum(query_embedding * np.log(np.abs(query_embedding) + 1e-10))
        
        # Normalize to 0-1 range
        confidence = min(magnitude * 0.5 + (1.0 - entropy / 10.0) * 0.5, 1.0)
        return max(confidence, 0.1)  # Minimum confidence
    
    def _find_similar_queries(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Find similar queries using embeddings"""
        # This would use FAISS to find similar query embeddings
        # For now, return placeholder
        return [
            {"query": "similar query example", "similarity": 0.85},
            {"query": "another similar query", "similarity": 0.78}
        ]
    
    def _extract_semantic_intent(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Extract semantic intent from query embedding"""
        # For prototype, use simple heuristics based on embedding
        intent = {
            'search_type': 'product_search',
            'specificity': 'medium',
            'semantic_category': self._classify_semantic_category(embedding),
            'intent_strength': float(np.mean(np.abs(embedding)))
        }
        
        return intent
    
    def _classify_semantic_category(self, embedding: np.ndarray) -> str:
        """Classify semantic category from embedding"""
        # Simple classification based on embedding patterns
        # In production, this would use trained classifiers
        avg_embedding = np.mean(embedding)
        
        if avg_embedding > 0.1:
            return 'specific_product'
        elif avg_embedding > 0.0:
            return 'category_search'
        else:
            return 'general_search'
    
    def _combine_analyses(self, smart_analysis, ml_analysis: Dict) -> Dict[str, Any]:
        """Combine smart rule-based and ML analyses"""
        # Start with smart analysis as base
        combined = {
            'query_type': smart_analysis.query_type,
            'sentiment': smart_analysis.sentiment,
            'brands': smart_analysis.brands,
            'categories': smart_analysis.categories,
            'price_range': smart_analysis.price_range,
            'modifiers': smart_analysis.modifiers,
            'entities': smart_analysis.entities,
            'confidence': smart_analysis.confidence
        }
        
        # Add ML insights if available
        if ml_analysis:
            combined.update({
                'semantic_analysis': ml_analysis,
                'hybrid_confidence': self._calculate_hybrid_confidence(
                    smart_analysis.confidence, 
                    ml_analysis.get('semantic_confidence', 0.5)
                ),
                'analysis_method': 'hybrid'
            })
        else:
            combined.update({
                'semantic_analysis': None,
                'hybrid_confidence': smart_analysis.confidence,
                'analysis_method': 'smart_only'
            })
        
        return combined
    
    def _calculate_hybrid_confidence(self, smart_conf: float, ml_conf: float) -> float:
        """Calculate combined confidence score"""
        # Weighted average with slight bias toward consensus
        base_confidence = (smart_conf * self.config['smart_weight'] + 
                          ml_conf * self.config['ml_weight'])
        
        # Boost if both methods agree (both high or both low)
        agreement_boost = 1.0 - abs(smart_conf - ml_conf) * 0.1
        
        return min(base_confidence * agreement_boost, 1.0)
    
    def _combine_confidence_scores(self, smart_conf: float, ml_conf: float) -> float:
        """Combine smart and ML confidence scores (alias for backward compatibility)"""
        return self._calculate_hybrid_confidence(smart_conf, ml_conf)
    
    # =============================================================================
    # HYBRID SEARCH
    # =============================================================================
    
    def search_products(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 20,
        use_ml: bool = True,
        ml_weight: Optional[float] = None,
        **kwargs
    ) -> SearchResponse:
        """
        Hybrid search combining smart rules + ML semantics
        
        Args:
            db: Database session
            query: Search query
            page: Page number
            limit: Results per page
            use_ml: Whether to use ML components
            ml_weight: Weight for ML scoring (0.0-1.0)
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse with hybrid results
        """
        start_time = time.time()
        
        # Use provided weight or default
        if ml_weight is not None:
            current_ml_weight = ml_weight
            current_smart_weight = 1.0 - ml_weight
        else:
            current_ml_weight = self.config['ml_weight']
            current_smart_weight = self.config['smart_weight']
        
        # Always get smart search results (reliable baseline)
        smart_results = self.smart_search.search_products(
            db=db, query=query, page=page, limit=limit, **kwargs
        )
        
        # Get ML results if available and requested
        ml_results = None
        if use_ml and self.is_ml_available():
            try:
                ml_results = self._ml_search_products(
                    db=db, query=query, page=page, limit=limit, **kwargs
                )
            except Exception as e:
                logger.warning(f"ML search failed, using smart results only: {e}")
                ml_results = None
        
        # Combine results
        if ml_results:
            hybrid_results = self._merge_search_results(
                smart_results, ml_results, current_smart_weight, current_ml_weight
            )
            method_used = 'hybrid'
        else:
            hybrid_results = smart_results
            method_used = 'smart_only'
        
        # Add hybrid metadata
        search_time = (time.time() - start_time) * 1000
        if hasattr(hybrid_results, 'query_analysis') and hybrid_results.query_analysis:
            hybrid_results.query_analysis['search_method'] = method_used
            hybrid_results.query_analysis['search_time_ms'] = search_time
            hybrid_results.query_analysis['weights_used'] = {
                'smart_weight': current_smart_weight,
                'ml_weight': current_ml_weight
            }
        
        logger.info(f"Hybrid search completed in {search_time:.1f}ms using {method_used}")
        return hybrid_results
    
    def _ml_search_products(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 20,
        **kwargs
    ) -> SearchResponse:
        """ML-powered semantic search"""
        # For prototype, use semantic similarity with existing products
        # This would be expanded with full vector search in production
        
        # Get query embedding
        query_embedding = self._get_query_embedding(query)
        
        # Placeholder for semantic search
        # In production, this would:
        # 1. Search FAISS index for similar products
        # 2. Re-rank using transformer-based scoring
        # 3. Apply semantic filters
        
        # For now, fallback to enhanced smart search with ML scoring
        return self.smart_search.search_products(
            db=db, query=query, page=page, limit=limit, **kwargs
        )
    
    def _merge_search_results(
        self, 
        smart_results: SearchResponse, 
        ml_results: SearchResponse,
        smart_weight: float,
        ml_weight: float
    ) -> SearchResponse:
        """Merge smart and ML search results with weighted scoring"""
        
        # Create product score mappings
        smart_scores = {p.product_id: i for i, p in enumerate(smart_results.products)}
        ml_scores = {p.product_id: i for i, p in enumerate(ml_results.products)}
        
        # Combine unique products
        all_products = {}
        for product in smart_results.products:
            all_products[product.product_id] = product
        for product in ml_results.products:
            if product.product_id not in all_products:
                all_products[product.product_id] = product
        
        # Calculate hybrid scores
        hybrid_scored_products = []
        for product_id, product in all_products.items():
            # Normalize scores (lower rank = higher score)
            smart_score = 1.0 / (smart_scores.get(product_id, len(smart_scores)) + 1)
            ml_score = 1.0 / (ml_scores.get(product_id, len(ml_scores)) + 1)
            
            # Calculate weighted hybrid score
            hybrid_score = smart_score * smart_weight + ml_score * ml_weight
            
            hybrid_scored_products.append((product, hybrid_score))
        
        # Sort by hybrid score
        hybrid_scored_products.sort(key=lambda x: x[1], reverse=True)
        
        # Create final results
        final_products = [product for product, _ in hybrid_scored_products]
        
        # Use smart_results as template and update products
        hybrid_results = SearchResponse(
            query=smart_results.query,
            corrected_query=smart_results.corrected_query,
            has_typo_correction=bool(smart_results.corrected_query),
            products=final_products[:smart_results.limit],
            total_count=len(final_products),
            page=smart_results.page,
            limit=smart_results.limit,
            total_pages=(len(final_products) + smart_results.limit - 1) // smart_results.limit,
            response_time_ms=smart_results.response_time_ms,
            filters_applied=smart_results.filters_applied,
            query_analysis=smart_results.query_analysis
        )
        
        return hybrid_results
    
    # =============================================================================
    # HYBRID AUTOSUGGEST
    # =============================================================================
    
    def get_hybrid_suggestions(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        include_semantic: bool = True,
        include_smart: bool = True,
        **kwargs
    ) -> List[AutosuggestItem]:
        """
        Hybrid autosuggest combining smart rules + ML semantics
        
        Args:
            db: Database session
            query: Query prefix
            limit: Maximum suggestions
            include_semantic: Include ML semantic suggestions
            include_smart: Include smart rule-based suggestions
            
        Returns:
            List of hybrid-ranked suggestions
        """
        suggestions = []
        
        # Get smart suggestions (always fast and reliable)
        if include_smart:
            try:
                from app.services.smart_autosuggest_service import get_smart_autosuggest_service
                smart_autosuggest = get_smart_autosuggest_service()
                smart_suggestions = smart_autosuggest.get_smart_suggestions(
                    db=db, query=query, limit=limit, **kwargs
                )
                suggestions.extend(smart_suggestions)
            except Exception as e:
                logger.warning(f"Smart autosuggest failed: {e}")
        
        # Get ML semantic suggestions if available
        if include_semantic and self.is_ml_available():
            try:
                ml_suggestions = self._get_ml_suggestions(db, query, limit)
                suggestions.extend(ml_suggestions)
            except Exception as e:
                logger.warning(f"ML autosuggest failed: {e}")
        
        # Rank and deduplicate suggestions
        final_suggestions = self._deduplicate_and_rank_suggestions(suggestions, query, limit)
        
        logger.info(f"Generated {len(final_suggestions)} hybrid suggestions for '{query}'")
        return final_suggestions
    
    def _deduplicate_and_rank_suggestions(
        self, suggestions: List[AutosuggestItem], query: str, limit: int
    ) -> List[AutosuggestItem]:
        """Remove duplicates and rank suggestions"""
        seen_texts = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.text.lower() not in seen_texts:
                seen_texts.add(suggestion.text.lower())
                unique_suggestions.append(suggestion)
        
        # Score suggestions with hybrid approach
        for suggestion in unique_suggestions:
            # Calculate hybrid score based on multiple factors
            base_score = suggestion.popularity
            
            # Boost exact prefix matches
            if suggestion.text.lower().startswith(query.lower()):
                base_score += 200
            
            # Boost semantic suggestions if ML is available
            if suggestion.type == 'semantic' and self.is_ml_available():
                base_score += 100
            
            # Update popularity with hybrid score
            suggestion.popularity = base_score
        
        # Sort by hybrid score and return top results
        unique_suggestions.sort(key=lambda x: x.popularity, reverse=True)
        return unique_suggestions[:limit]

    def get_suggestions(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        include_semantic: bool = True,
        include_smart: bool = True,
        **kwargs
    ) -> AutosuggestResponse:
        """
        Hybrid autosuggest combining smart patterns + neural suggestions
        """
        start_time = time.time()
        suggestions = []
        
        # Get smart suggestions (always available)
        if include_smart:
            try:
                smart_suggestions = self.get_hybrid_suggestions(
                    db, query, limit, include_semantic=False, include_smart=True, **kwargs
                )
                suggestions.extend(smart_suggestions)
            except Exception as e:
                logger.warning(f"Smart suggestions failed: {e}")
        
        # Add ML-powered semantic suggestions
        if include_semantic and self.is_ml_available():
            try:
                semantic_suggestions = self._get_ml_suggestions(db, query, limit // 2, **kwargs)
                suggestions.extend(semantic_suggestions)
            except Exception as e:
                logger.warning(f"Semantic suggestions failed: {e}")
        
        # Remove duplicates and rank
        suggestions = self._deduplicate_and_rank_suggestions(suggestions, query, limit)
        
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return AutosuggestResponse(
            query=query,
            suggestions=suggestions,
            total_count=len(suggestions),
            response_time_ms=response_time_ms
        )

    def _get_ml_suggestions(self, db: Session, query: str, limit: int, **kwargs) -> List[AutosuggestItem]:
        """Generate semantic suggestions using ML"""
        suggestions = []
        
        if not self.sentence_transformer:
            return suggestions
        
        try:
            # Get query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Find semantically similar products/queries
            semantic_completions = self._generate_semantic_completions(query, limit)
            
            for i, completion in enumerate(semantic_completions):
                suggestion = AutosuggestItem(
                    text=completion,
                    type="semantic",
                    category="ml_generated",
                    popularity=1000 - i * 10  # Rank by confidence
                )
                suggestions.append(suggestion)
        
        except Exception as e:
            logger.warning(f"Semantic suggestions error: {e}")
        
        return suggestions

    def _generate_semantic_completions(self, query: str, limit: int) -> List[str]:
        """Generate semantic query completions"""
        # Simple semantic completions based on common patterns
        base_terms = query.lower().split()
        completions = []
        
        # Add brand + category combinations
        if len(base_terms) == 1:
            term = base_terms[0]
            completions.extend([
                f"{term} price",
                f"{term} review",
                f"{term} specifications",
                f"best {term}",
                f"{term} offers"
            ])
        
        # Add price-related completions
        if 'under' not in query.lower():
            completions.extend([
                f"{query} under 10000",
                f"{query} under 20000",
                f"{query} under 50000"
            ])
        
        return completions[:limit]

    def get_ml_status(self) -> Dict[str, Any]:
        """Get detailed ML component status"""
        return {
            'ml_available': self.ml_available,
            'sentence_transformer': self.sentence_transformer is not None,
            'faiss_index': self.faiss_index is not None,
            'hybrid_engine': self.hybrid_engine is not None,
            'embeddings_available': self.embeddings_available,
            'cached_embeddings': len(self.query_embeddings_cache),
            'model_name': self.config['model_name'] if self.sentence_transformer else None,
            'embedding_dimension': self.config['embedding_dim'] if self.sentence_transformer else None,
            'configuration': self.config
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Global instance
_hybrid_ml_service = None

def get_hybrid_ml_service() -> HybridMLService:
    """Get global HybridMLService instance"""
    global _hybrid_ml_service
    if _hybrid_ml_service is None:
        _hybrid_ml_service = HybridMLService()
    return _hybrid_ml_service

def is_hybrid_ml_available() -> bool:
    """Check if hybrid ML service is available"""
    try:
        service = get_hybrid_ml_service()
        return service.is_ml_available()
    except Exception:
        return False
