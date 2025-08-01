"""
Tests for the ML ranker component
"""

import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from app.ml.ranker import MLRanker

# Sample data for testing
sample_results = [
    {
        'id': 'P001',
        'title': 'Red T-shirt',
        'description': 'Cotton red t-shirt with logo',
        'category': 'Fashion',
        'brand': 'BrandA',
        'price': 499.0,
        'rating': 4.2,
        'semantic_score': 0.85,
        'lexical_score': 0.75,
        'combined_score': 0.82,
        'position': 1,
        'match_type': 'hybrid'
    },
    {
        'id': 'P002',
        'title': 'Blue Jeans',
        'description': 'Classic blue denim jeans',
        'category': 'Fashion',
        'brand': 'BrandB',
        'price': 1299.0,
        'rating': 4.5,
        'semantic_score': 0.65,
        'lexical_score': 0.90,
        'combined_score': 0.73,
        'position': 2,
        'match_type': 'lexical'
    },
    {
        'id': 'P003',
        'title': 'Wireless Headphones',
        'description': 'Wireless headphones with noise cancellation',
        'category': 'Electronics',
        'brand': 'BrandC',
        'price': 2999.0,
        'rating': 4.0,
        'semantic_score': 0.70,
        'lexical_score': 0.60,
        'combined_score': 0.67,
        'position': 3,
        'match_type': 'semantic'
    }
]

# Sample training data
sample_search_data = [
    {
        'query': 'red shirt',
        'results': sample_results
    },
    {
        'query': 'blue jeans',
        'results': sample_results[::-1]  # Reversed to have different order
    }
]

sample_click_data = {
    'red shirt': {
        'P001': 4.0,  # High relevance
        'P002': 2.0   # Medium relevance
    },
    'blue jeans': {
        'P002': 4.0,  # High relevance
        'P001': 1.0   # Low relevance
    }
}

class TestMLRanker:
    
    def test_init(self):
        ranker = MLRanker()
        assert ranker.model is None
        assert ranker.is_trained is False
        
    def test_extract_features(self):
        ranker = MLRanker()
        features = ranker._extract_features(sample_results[0])
        
        # Check feature extraction
        assert len(features) > 0
        assert features[0] == sample_results[0]['semantic_score']
        assert features[1] == sample_results[0]['lexical_score']
    
    def test_training(self):
        ranker = MLRanker(num_boost_round=10)  # Use small number for testing
        metrics = ranker.train(sample_search_data, sample_click_data)
        
        # Check that model was trained
        assert ranker.is_trained
        assert ranker.model is not None
        assert 'train_ndcg' in metrics
        
    def test_rerank(self):
        # Train model
        ranker = MLRanker(num_boost_round=10)
        ranker.train(sample_search_data, sample_click_data)
        
        # Rerank results
        reranked = ranker.rerank(sample_results)
        
        # Check reranked results
        assert len(reranked) == len(sample_results)
        assert all('ml_score' in r for r in reranked)
        assert all('position' in r for r in reranked)
        
        # Check that positions were updated
        positions = [r['position'] for r in reranked]
        assert positions == list(range(1, len(reranked) + 1))
    
    def test_save_load(self):
        # Create temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "ml_ranker.pkl")
            
            # Create and save model
            ranker1 = MLRanker(num_boost_round=10)
            ranker1.train(sample_search_data, sample_click_data)
            ranker1.save(filepath)
            
            # Load model
            ranker2 = MLRanker()
            ranker2.load(filepath)
            
            # Verify loaded model
            assert ranker2.is_trained
            assert ranker2.model is not None
            assert ranker2.feature_names == ranker1.feature_names
            
            # Check that predictions are the same
            pred1 = ranker1.rerank(sample_results)
            pred2 = ranker2.rerank(sample_results)
            
            # Compare scores
            scores1 = [r['ml_score'] for r in pred1]
            scores2 = [r['ml_score'] for r in pred2]
            assert all(abs(s1 - s2) < 1e-6 for s1, s2 in zip(scores1, scores2))
            
            # Compare positions
            pos1 = [r['position'] for r in pred1]
            pos2 = [r['position'] for r in pred2]
            assert pos1 == pos2
