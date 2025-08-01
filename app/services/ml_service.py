"""
ML Service Layer - Safe integration of ML components
This service provides ML functionality while gracefully falling back if components fail
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

class MLService:
    """Service layer for ML components with safe fallbacks"""
    
    def __init__(self):
        self.ml_ranker = None
        self.hybrid_engine = None
        self.embeddings_available = False
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize ML components with error handling"""
        try:
            from app.ml.ranker import MLRanker
            self.ml_ranker = MLRanker()
            logger.info("ML Ranker initialized successfully")
        except Exception as e:
            logger.warning(f"ML Ranker not available: {e}")
            self.ml_ranker = None
        
        try:
            from app.search.hybrid_engine import HybridSearchEngine
            # Initialize with safe defaults
            data_dir = Path("data")
            if data_dir.exists():
                self.hybrid_engine = HybridSearchEngine(data_dir=data_dir)
                logger.info("Hybrid Search Engine initialized successfully")
        except Exception as e:
            logger.warning(f"Hybrid Search Engine not available: {e}")
            self.hybrid_engine = None
    
    def is_ml_available(self) -> bool:
        """Check if ML components are available"""
        return self.ml_ranker is not None or self.hybrid_engine is not None
    
    def rank_products(self, products: List[Dict], query: str) -> List[Dict]:
        """
        Rank products using ML if available, otherwise use simple ranking
        
        Args:
            products: List of product dictionaries
            query: Search query
            
        Returns:
            Ranked list of products
        """
        if not products:
            return products
        
        try:
            if self.ml_ranker and len(products) > 1:
                return self._ml_rank_products(products, query)
            else:
                return self._simple_rank_products(products, query)
        except Exception as e:
            logger.error(f"ML ranking failed, using simple ranking: {e}")
            return self._simple_rank_products(products, query)
    
    def _ml_rank_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Use ML ranker to rank products"""
        try:
            # Extract features for ML ranking
            features = []
            for product in products:
                feature_vector = self._extract_features(product, query)
                features.append(feature_vector)
            
            if not features:
                return self._simple_rank_products(products, query)
            
            # Get ML scores
            features_array = np.array(features)
            scores = self.ml_ranker.predict(features_array)
            
            # Combine products with scores and sort
            product_scores = list(zip(products, scores))
            product_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Add ML score to products
            ranked_products = []
            for product, score in product_scores:
                product_copy = product.copy()
                product_copy['ml_score'] = float(score)
                product_copy['ranking_method'] = 'ml'
                ranked_products.append(product_copy)
            
            return ranked_products
            
        except Exception as e:
            logger.error(f"ML ranking error: {e}")
            return self._simple_rank_products(products, query)
    
    def _simple_rank_products(self, products: List[Dict], query: str) -> List[Dict]:
        """Simple relevance-based ranking as fallback"""
        query_lower = query.lower()
        
        def calculate_simple_score(product):
            score = 0.0
            
            # Title relevance (highest weight)
            title = product.get('title', '').lower()
            if query_lower in title:
                if title.startswith(query_lower):
                    score += 10.0  # Starts with query
                else:
                    score += 5.0   # Contains query
            
            # Brand relevance
            brand = product.get('brand', '').lower()
            if query_lower in brand:
                score += 3.0
            
            # Category relevance
            category = product.get('category', '').lower()
            if query_lower in category:
                score += 2.0
            
            # Rating boost
            rating = product.get('rating', 0)
            score += rating * 0.5
            
            # Popularity boost (num_ratings)
            num_ratings = product.get('num_ratings', 0)
            score += min(num_ratings / 1000.0, 2.0)
            
            # Bestseller boost
            if product.get('is_bestseller', False):
                score += 1.0
                
            # Stock availability
            if product.get('stock', 0) > 0:
                score += 0.5
            
            return score
        
        # Calculate scores and sort
        for product in products:
            product['simple_score'] = calculate_simple_score(product)
            product['ranking_method'] = 'simple'
        
        products.sort(key=lambda x: x['simple_score'], reverse=True)
        return products
    
    def _extract_features(self, product: Dict, query: str) -> List[float]:
        """Extract features for ML ranking"""
        features = []
        
        # Text relevance features
        query_lower = query.lower()
        title = product.get('title', '').lower()
        
        # Title match features
        features.append(1.0 if query_lower in title else 0.0)
        features.append(1.0 if title.startswith(query_lower) else 0.0)
        
        # Exact word matches
        query_words = set(query_lower.split())
        title_words = set(title.split())
        word_overlap = len(query_words.intersection(title_words)) / max(len(query_words), 1)
        features.append(word_overlap)
        
        # Product quality features
        features.append(product.get('rating', 0.0))
        features.append(min(product.get('num_ratings', 0) / 100.0, 10.0))  # Normalized
        features.append(1.0 if product.get('is_bestseller', False) else 0.0)
        
        # Price features (normalized)
        price = product.get('price', 0)
        features.append(min(price / 10000.0, 5.0))  # Price normalized
        
        # Discount features
        discount = product.get('discount_percentage', 0)
        features.append(discount / 100.0)
        
        # Stock features
        stock = product.get('stock', 0)
        features.append(1.0 if stock > 0 else 0.0)
        features.append(min(stock / 100.0, 1.0))  # Stock level normalized
        
        return features
    
    def get_semantic_results(self, query: str, limit: int = 50) -> Optional[List[Dict]]:
        """Get semantic search results if available"""
        if not self.hybrid_engine:
            return None
        
        try:
            results = self.hybrid_engine.search(
                query=query,
                top_k=limit,
                use_semantic=True,
                use_lexical=True
            )
            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return None

# Global instance
_ml_service = None

def get_ml_service() -> MLService:
    """Get global ML service instance"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
    return _ml_service
