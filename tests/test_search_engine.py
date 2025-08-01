"""
Tests for the search engine components
"""

import pytest
import numpy as np
import os
import tempfile
from app.search.hybrid_engine import FAISSVectorIndex, BM25SearchEngine, HybridSearchEngine
from sentence_transformers import SentenceTransformer
import pandas as pd

# Sample data for testing
sample_docs = [
    "red cotton t-shirt with logo",
    "blue denim jeans",
    "wireless headphones with noise cancellation",
    "smartphone with high resolution camera",
    "laptop with 16gb ram and ssd storage"
]

sample_df = pd.DataFrame({
    'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
    'title': sample_docs,
    'description': sample_docs,
    'category': ['Fashion', 'Fashion', 'Electronics', 'Electronics', 'Electronics'],
    'brand': ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE'],
    'price': [499, 1299, 2999, 15999, 45999],
    'rating': [4.2, 4.5, 4.0, 4.8, 4.3],
})

# Test fixture for embedding model
@pytest.fixture(scope="module")
def embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# Test fixture for embeddings
@pytest.fixture(scope="module")
def embeddings(embedding_model):
    return embedding_model.encode(sample_docs, normalize_embeddings=True)

class TestFAISSVectorIndex:
    
    def test_init(self):
        index = FAISSVectorIndex(embedding_dim=384)
        assert index.embedding_dim == 384
        assert index.index is None
        assert index.is_trained is False
        
    def test_build_index(self, embeddings):
        index = FAISSVectorIndex(embedding_dim=embeddings.shape[1])
        index.build_index(embeddings, index_type="FLAT")
        assert index.index is not None
        assert index.n_vectors == len(embeddings)
        
    def test_search(self, embedding_model, embeddings):
        # Build index
        index = FAISSVectorIndex(embedding_dim=embeddings.shape[1])
        index.build_index(embeddings, index_type="FLAT")
        
        # Create query embedding
        query = "blue jeans"
        query_embedding = embedding_model.encode([query], normalize_embeddings=True)
        
        # Search
        similarities, indices = index.search(query_embedding, k=2)
        
        # Verify results
        assert similarities.shape == (1, 2)
        assert indices.shape == (1, 2)
        assert indices[0][0] == 1  # Should match "blue denim jeans"
        
    def test_save_load_index(self, embeddings):
        # Create temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_index.bin")
            
            # Create and save index
            index1 = FAISSVectorIndex(embedding_dim=embeddings.shape[1])
            index1.build_index(embeddings, index_type="FLAT")
            index1.save_index(filepath)
            
            # Load index
            index2 = FAISSVectorIndex(embedding_dim=embeddings.shape[1])
            index2.load_index(filepath)
            
            # Verify loaded index
            assert index2.n_vectors == len(embeddings)
            assert index2.index is not None

class TestBM25SearchEngine:
    
    def test_init(self):
        engine = BM25SearchEngine(k1=1.5, b=0.75)
        assert engine.k1 == 1.5
        assert engine.b == 0.75
        assert engine.is_fitted is False
        
    def test_fit(self):
        engine = BM25SearchEngine()
        engine.fit(sample_docs)
        
        assert engine.is_fitted
        assert len(engine.doc_freqs) > 0
        assert len(engine.idf) > 0
        assert len(engine.doc_lengths) == len(sample_docs)
        
    def test_search(self):
        engine = BM25SearchEngine()
        engine.fit(sample_docs)
        
        # Search for relevant query
        results = engine.search("blue jeans", k=2)
        
        # Verify results
        assert len(results) > 0
        assert results[0][0] == 1  # Should match "blue denim jeans"
        
    def test_save_load(self):
        # Create temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "bm25_model.pkl")
            
            # Create and save model
            engine1 = BM25SearchEngine()
            engine1.fit(sample_docs)
            engine1.save(filepath)
            
            # Load model
            engine2 = BM25SearchEngine()
            engine2.load(filepath)
            
            # Verify loaded model
            assert engine2.is_fitted
            assert len(engine2.doc_freqs) > 0
            assert len(engine2.idf) > 0
            
            # Check results are the same
            results1 = engine1.search("blue jeans", k=2)
            results2 = engine2.search("blue jeans", k=2)
            
            assert results1[0][0] == results2[0][0]
            assert results1[0][1] == results2[0][1]

class TestHybridSearchEngine:
    
    @pytest.fixture
    def hybrid_engine(self, embedding_model, embeddings):
        # Create FAISS index
        faiss_index = FAISSVectorIndex(embedding_dim=embeddings.shape[1])
        faiss_index.build_index(embeddings, index_type="FLAT")
        
        # Create BM25 engine
        bm25_engine = BM25SearchEngine()
        bm25_engine.fit(sample_docs)
        
        # Create hybrid engine
        return HybridSearchEngine(
            faiss_index=faiss_index,
            bm25_engine=bm25_engine,
            embedding_model=embedding_model,
            products_df=sample_df,
            semantic_weight=0.7
        )
    
    def test_search_semantic(self, hybrid_engine):
        # Test semantic search
        results = hybrid_engine.search("noise cancelling headphones", k=2, query_type="semantic")
        
        assert len(results) > 0
        assert results[0]['id'] == 'P003'  # Should match "wireless headphones with noise cancellation"
        assert results[0]['match_type'] == 'semantic'
    
    def test_search_lexical(self, hybrid_engine):
        # Test lexical search
        results = hybrid_engine.search("16gb ram laptop", k=2, query_type="lexical")
        
        assert len(results) > 0
        assert results[0]['id'] == 'P005'  # Should match "laptop with 16gb ram and ssd storage"
        assert results[0]['match_type'] == 'lexical'
    
    def test_search_hybrid(self, hybrid_engine):
        # Test hybrid search
        results = hybrid_engine.search("smartphone camera", k=2, query_type="hybrid")
        
        assert len(results) > 0
        assert results[0]['id'] == 'P004'  # Should match "smartphone with high resolution camera"
        
        # Check that scores are properly set
        assert 'semantic_score' in results[0]
        assert 'lexical_score' in results[0]
        assert 'combined_score' in results[0]
