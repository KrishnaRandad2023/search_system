"""
Hybrid Search Engine for Flipkart Grid 7.0
Production-grade implementation combining semantic and lexical search with ML ranking
"""

import time
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer
import re
import math
from collections import defaultdict, Counter
import pickle
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAISSVectorIndex:
    """Production-grade FAISS index for ultra-fast semantic search"""
    
    def __init__(self, embedding_dim: int = 384):
        """Initialize FAISS index with optimal configuration"""
        self.embedding_dim = embedding_dim
        self.index: Optional[faiss.Index] = None
        self.is_trained = False
        self.n_vectors = 0
        
    def build_index(self, embeddings: np.ndarray, index_type: str = "IVF_FLAT") -> None:
        """Build optimized FAISS index based on dataset size"""
        logger.info(f"Building FAISS index with {len(embeddings):,} vectors...")
        start_time = time.time()
        
        n_vectors, dim = embeddings.shape
        self.n_vectors = n_vectors
        
        # Choose index type based on dataset size and requirements
        if index_type == "FLAT" or n_vectors < 1000:
            # Exact search - best for small datasets
            self.index = faiss.IndexFlatIP(dim)  # Inner Product for normalized vectors
            logger.info("Using FLAT index (exact search)")
            
        elif index_type == "IVF_FLAT":
            # Inverted File with Flat quantizer - good balance
            n_clusters = min(int(np.sqrt(n_vectors)), 256)  # Optimal cluster count
            quantizer = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIVFFlat(quantizer, dim, n_clusters)
            
            logger.info(f"Using IVF_FLAT index with {n_clusters} clusters")
            
            # Train the index
            logger.info("Training index...")
            self.index.train(embeddings.astype(np.float32))  # type: ignore
            self.is_trained = True
            
        elif index_type == "IVF_PQ":
            # IVF with Product Quantization - best for very large datasets
            n_clusters = min(int(np.sqrt(n_vectors)), 256)
            m = 8  # Number of subquantizers
            bits = 8  # Bits per subquantizer
            
            quantizer = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIVFPQ(quantizer, dim, n_clusters, m, bits)
            
            logger.info(f"Using IVF_PQ index with {n_clusters} clusters, {m}x{bits} quantization")
            
            # Train the index
            logger.info("Training index...")
            self.index.train(embeddings.astype(np.float32))  # type: ignore
            self.is_trained = True
        
        # Add vectors to index
        logger.info("Adding vectors to index...")
        self.index.add(embeddings.astype(np.float32))  # type: ignore
        
        build_time = time.time() - start_time
        logger.info(f"FAISS index built in {build_time:.2f}s")
        logger.info(f"Index contains {self.index.ntotal:,} vectors")  # type: ignore
        
        # Optimize search parameters
        try:
            if hasattr(self.index, 'nprobe'):
                # Set search parameters for IVF indices
                self.index.nprobe = min(32, max(1, n_clusters // 8))  # type: ignore
                logger.info(f"Search nprobe set to {self.index.nprobe}")  # type: ignore
        except Exception as e:
            logger.warning(f"Could not set nprobe: {e}")
    
    def search(self, query_vectors: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors"""
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        query_vectors = query_vectors.astype(np.float32)
        if len(query_vectors.shape) == 1:
            query_vectors = query_vectors.reshape(1, -1)
        
        # Perform search
        similarities, indices = self.index.search(query_vectors, k)  # type: ignore
        
        return similarities, indices
    
    def save_index(self, filepath: str) -> None:
        """Save FAISS index to disk"""
        if self.index is None:
            raise ValueError("No index to save")
        
        index_dir = os.path.dirname(filepath)
        os.makedirs(index_dir, exist_ok=True)
        
        faiss.write_index(self.index, filepath)
        logger.info(f"FAISS index saved to {filepath}")
    
    def load_index(self, filepath: str) -> None:
        """Load FAISS index from disk"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")
        
        self.index = faiss.read_index(filepath)
        self.n_vectors = self.index.ntotal if self.index else 0
        logger.info(f"FAISS index loaded from {filepath}")
        logger.info(f"Index contains {self.n_vectors:,} vectors")


class BM25SearchEngine:
    """Production-grade BM25 implementation for lexical search"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with optimal parameters
        
        Args:
            k1: Term frequency saturation parameter (1.2-2.0)
            b: Document length normalization parameter (0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = defaultdict(int)  # Document frequency for each term
        self.idf = {}
        self.doc_lengths = []
        self.avgdl = 0  # Average document length
        self.N = 0  # Total number of documents
        self.is_fitted = False
        
    def _tokenize(self, text: str) -> List[str]:
        """Advanced tokenization with preprocessing"""
        if not text:
            return []
        
        # Convert to lowercase and split
        tokens = text.lower().split()
        
        # Remove punctuation and special characters
        tokens = [re.sub(r'[^\w\s]', '', token) for token in tokens]
        
        # Filter out empty tokens and very short tokens
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def fit(self, documents: List[str], doc_ids: Optional[List[int]] = None) -> None:
        """Train BM25 on document corpus"""
        logger.info(f"Training BM25 on {len(documents):,} documents...")
        start_time = time.time()
        
        self.corpus = documents
        self.N = len(documents)
        
        if doc_ids is None:
            self.doc_ids = list(range(self.N))
        else:
            self.doc_ids = doc_ids
        
        # Tokenize all documents and calculate statistics
        tokenized_corpus = []
        total_length = 0
        
        for doc in documents:
            tokens = self._tokenize(doc)
            tokenized_corpus.append(tokens)
            doc_length = len(tokens)
            self.doc_lengths.append(doc_length)
            total_length += doc_length
            
            # Count document frequency for each unique term
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1
        
        # Calculate average document length
        self.avgdl = total_length / self.N if self.N > 0 else 0
        
        # Calculate IDF for each term
        logger.info("Calculating IDF scores...")
        for term, doc_freq in self.doc_freqs.items():
            # BM25 IDF formula with small smoothing
            self.idf[term] = math.log((self.N - doc_freq + 0.5) / (doc_freq + 0.5))
        
        self.tokenized_corpus = tokenized_corpus
        self.is_fitted = True
        
        fit_time = time.time() - start_time
        logger.info(f"BM25 training completed in {fit_time:.2f}s")
        logger.info(f"Vocabulary size: {len(self.doc_freqs):,} unique terms")
        logger.info(f"Average document length: {self.avgdl:.1f} tokens")
        
    def _score_document(self, query_terms: List[str], doc_tokens: List[str]) -> float:
        """Calculate BM25 score for a single document"""
        score = 0.0
        doc_length = len(doc_tokens)
        
        # Count term frequencies in document
        term_freqs = Counter(doc_tokens)
        
        for term in query_terms:
            if term in term_freqs:
                # Term frequency
                tf = term_freqs[term]
                
                # IDF score (default to 0 for unseen terms)
                idf = self.idf.get(term, 0)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avgdl))
                
                score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """Search documents using BM25 scoring"""
        if not self.is_fitted:
            raise ValueError("BM25 not fitted. Call fit() first.")
        
        # Tokenize query
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return []
        
        # Score all documents
        scores = []
        for i, doc_tokens in enumerate(self.tokenized_corpus):
            score = self._score_document(query_terms, doc_tokens)
            if score > 0:  # Only include documents with positive scores
                scores.append((self.doc_ids[i], score))
        
        # Sort by score (descending) and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
    
    def save(self, filepath: str) -> None:
        """Save BM25 model to disk"""
        if not self.is_fitted:
            raise ValueError("BM25 not fitted. Call fit() first.")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'k1': self.k1,
                'b': self.b,
                'doc_freqs': dict(self.doc_freqs),
                'idf': self.idf,
                'doc_lengths': self.doc_lengths,
                'avgdl': self.avgdl,
                'N': self.N,
                'doc_ids': self.doc_ids,
                'tokenized_corpus': self.tokenized_corpus
            }, f)
        
        logger.info(f"BM25 model saved to {filepath}")
    
    def load(self, filepath: str) -> None:
        """Load BM25 model from disk"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.k1 = data['k1']
        self.b = data['b']
        self.doc_freqs = defaultdict(int, data['doc_freqs'])
        self.idf = data['idf']
        self.doc_lengths = data['doc_lengths']
        self.avgdl = data['avgdl']
        self.N = data['N']
        self.doc_ids = data['doc_ids']
        self.tokenized_corpus = data['tokenized_corpus']
        self.is_fitted = True
        
        logger.info(f"BM25 model loaded from {filepath}")
        logger.info(f"Vocabulary size: {len(self.doc_freqs):,} terms")


class HybridSearchEngine:
    """Production-grade hybrid search engine combining semantic and lexical search"""
    
    def __init__(
        self, 
        faiss_index: FAISSVectorIndex,
        bm25_engine: BM25SearchEngine,
        embedding_model: SentenceTransformer,
        products_df: pd.DataFrame,
        semantic_weight: float = 0.7,
        normalize_scores: bool = True
    ):
        """
        Initialize the hybrid search engine
        
        Args:
            faiss_index: Initialized FAISS index for semantic search
            bm25_engine: Initialized BM25 engine for lexical search
            embedding_model: SentenceTransformer model for encoding queries
            products_df: DataFrame containing product information
            semantic_weight: Weight of semantic scores in hybrid results (0-1)
            normalize_scores: Whether to normalize scores before combining
        """
        self.faiss_index = faiss_index
        self.bm25_engine = bm25_engine
        self.embedding_model = embedding_model
        self.products_df = products_df
        self.semantic_weight = max(0.0, min(1.0, semantic_weight))  # Clamp between 0 and 1
        self.lexical_weight = 1.0 - self.semantic_weight
        self.normalize_scores = normalize_scores
        logger.info(f"Hybrid search initialized with semantic weight: {self.semantic_weight}")
        
    def search(self, query: str, k: int = 10, query_type: str = "auto") -> List[Dict]:
        """
        Perform hybrid search combining semantic and lexical results
        
        Args:
            query: Search query text
            k: Number of results to return
            query_type: 'semantic', 'lexical', 'hybrid', or 'auto'
        
        Returns:
            List of result dictionaries with product information and scores
        """
        # Clean query
        clean_query = query.strip()
        if not clean_query:
            return []
        
        # Auto-detect query type if needed
        if query_type == "auto":
            # Use semantic search for natural language queries
            if len(clean_query.split()) > 3 and any(w in clean_query.lower() for w in ["how", "what", "which", "where", "when", "why", "who", "best", "recommend"]):
                query_type = "semantic"
                logger.debug(f"Auto-detected query type: semantic for query '{clean_query}'")
            # Use lexical search for specific product searches with specs
            elif any(char.isdigit() for char in clean_query) and len(clean_query.split()) < 6:
                query_type = "lexical"
                logger.debug(f"Auto-detected query type: lexical for query '{clean_query}'")
            # Use hybrid search for most queries
            else:
                query_type = "hybrid"
                logger.debug(f"Auto-detected query type: hybrid for query '{clean_query}'")
        
        # Choose search method based on query type
        start_time = time.time()
        if query_type == "semantic":
            results = self._semantic_search(clean_query, k)
        elif query_type == "lexical":
            results = self._lexical_search(clean_query, k)
        else:  # hybrid
            results = self._hybrid_search(clean_query, k)
            
        search_time = time.time() - start_time
        logger.info(f"Search for '{clean_query}' completed in {search_time*1000:.2f}ms with {len(results)} results")
        
        return results
    
    def _semantic_search(self, query: str, k: int = 10) -> List[Dict]:
        """Perform semantic search using FAISS"""
        start_time = time.time()
        
        # Encode query
        query_embedding = self.embedding_model.encode(
            query, 
            normalize_embeddings=True
        )
        
        # Convert tensor to numpy array if needed
        if hasattr(query_embedding, 'cpu'):
            query_embedding = query_embedding.cpu().numpy()
        elif hasattr(query_embedding, 'numpy'):
            query_embedding = query_embedding.numpy()
        query_embedding = np.array(query_embedding).astype(np.float32)
        
        # Search with FAISS
        similarities, indices = self.faiss_index.search(
            np.array(query_embedding).reshape(1, -1), 
            k=k
        )
        
        # Convert to list of results
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx >= 0 and idx < len(self.products_df):  # Valid index
                product = self.products_df.iloc[idx]
                results.append({
                    'id': product['product_id'],
                    'title': product['title'],
                    'description': product['description'],
                    'category': product['category'],
                    'subcategory': product.get('subcategory', ''),
                    'brand': product['brand'],
                    'price': product['price'],
                    'rating': product['rating'],
                    'semantic_score': float(similarity),
                    'lexical_score': 0.0,
                    'combined_score': float(similarity),
                    'position': i + 1,
                    'match_type': 'semantic'
                })
        
        search_time = time.time() - start_time
        logger.debug(f"Semantic search time: {search_time*1000:.2f}ms")
        
        return results
    
    def _lexical_search(self, query: str, k: int = 10) -> List[Dict]:
        """Perform lexical search using BM25"""
        start_time = time.time()
        
        # Search with BM25
        bm25_results = self.bm25_engine.search(query, k=k)
        
        # Convert to list of results
        results = []
        for i, (doc_id, score) in enumerate(bm25_results):
            if doc_id < len(self.products_df):  # Valid index
                product = self.products_df.iloc[doc_id]
                results.append({
                    'id': product['product_id'],
                    'title': product['title'],
                    'description': product['description'],
                    'category': product['category'],
                    'subcategory': product.get('subcategory', ''),
                    'brand': product['brand'],
                    'price': product['price'],
                    'rating': product['rating'],
                    'semantic_score': 0.0,
                    'lexical_score': float(score),
                    'combined_score': float(score),
                    'position': i + 1,
                    'match_type': 'lexical'
                })
        
        search_time = time.time() - start_time
        logger.debug(f"Lexical search time: {search_time*1000:.2f}ms")
        
        return results
    
    def _hybrid_search(self, query: str, k: int = 10) -> List[Dict]:
        """Perform hybrid search combining semantic and lexical results"""
        start_time = time.time()
        expanded_k = min(k * 3, 100)  # Get more results for better merging
        
        # Encode query for semantic search
        query_embedding = self.embedding_model.encode(
            query, 
            normalize_embeddings=True
        )
        
        # Convert tensor to numpy array if needed
        if hasattr(query_embedding, 'cpu'):
            query_embedding = query_embedding.cpu().numpy()
        elif hasattr(query_embedding, 'numpy'):
            query_embedding = query_embedding.numpy()
        query_embedding = np.array(query_embedding).astype(np.float32)
        
        # Perform semantic search
        similarities, indices = self.faiss_index.search(
            np.array(query_embedding).reshape(1, -1), 
            k=expanded_k
        )
        
        # Perform lexical search
        lexical_results = self.bm25_engine.search(query, k=expanded_k)
        
        # Collect all results
        semantic_dict = {}
        for sim, idx in zip(similarities[0], indices[0]):
            if idx >= 0 and idx < len(self.products_df):
                semantic_dict[idx] = float(sim)
        
        lexical_dict = {doc_id: float(score) for doc_id, score in lexical_results}
        
        # Combine results
        all_indices = set(semantic_dict.keys()) | set(lexical_dict.keys())
        
        # Normalize scores if needed
        if self.normalize_scores:
            # Get score ranges for normalization
            if semantic_dict:
                max_semantic = max(semantic_dict.values())
                min_semantic = min(semantic_dict.values())
                semantic_range = max(0.001, max_semantic - min_semantic)
            else:
                max_semantic = min_semantic = semantic_range = 1.0
            
            if lexical_dict:
                max_lexical = max(lexical_dict.values())
                min_lexical = min(lexical_dict.values())
                lexical_range = max(0.001, max_lexical - min_lexical)
            else:
                max_lexical = min_lexical = lexical_range = 1.0
                
            # Normalize scores to 0-1 range
            for idx in semantic_dict:
                semantic_dict[idx] = (semantic_dict[idx] - min_semantic) / semantic_range
            
            for idx in lexical_dict:
                lexical_dict[idx] = (lexical_dict[idx] - min_lexical) / lexical_range
        
        # Calculate combined scores
        combined_scores = {}
        for idx in all_indices:
            semantic_score = semantic_dict.get(idx, 0.0)
            lexical_score = lexical_dict.get(idx, 0.0)
            
            # Enhanced combination method that boosts products with both high scores
            # This creates a "coincidence boost" effect
            combined_scores[idx] = (
                self.semantic_weight * semantic_score + 
                self.lexical_weight * lexical_score +
                0.1 * min(semantic_score, lexical_score)  # Boost for appearing in both results
            )
        
        # Sort by combined score and get top k
        sorted_indices = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        # Convert to list of results
        results = []
        for i, (idx, score) in enumerate(sorted_indices):
            product = self.products_df.iloc[idx]
            # Determine match type based on which score contributed more
            semantic_score = semantic_dict.get(idx, 0.0)
            lexical_score = lexical_dict.get(idx, 0.0)
            
            if semantic_score > 0 and lexical_score > 0:
                match_type = 'hybrid'
            elif semantic_score > 0:
                match_type = 'semantic'
            else:
                match_type = 'lexical'
            
            results.append({
                'id': product['product_id'],
                'title': product['title'],
                'description': product['description'],
                'category': product['category'],
                'subcategory': product.get('subcategory', ''),
                'brand': product['brand'],
                'price': product['price'],
                'rating': product['rating'],
                'semantic_score': semantic_dict.get(idx, 0.0),
                'lexical_score': lexical_dict.get(idx, 0.0),
                'combined_score': score,
                'position': i + 1,
                'match_type': match_type
            })
        
        search_time = time.time() - start_time
        logger.debug(f"Hybrid search time: {search_time*1000:.2f}ms")
        
        return results
    
    def save(self, directory: str) -> None:
        """Save all components to disk"""
        os.makedirs(directory, exist_ok=True)
        
        # Save FAISS index
        self.faiss_index.save_index(os.path.join(directory, "faiss_index.bin"))
        
        # Save BM25 engine
        self.bm25_engine.save(os.path.join(directory, "bm25_engine.pkl"))
        
        # Save engine configuration
        with open(os.path.join(directory, "hybrid_config.pkl"), 'wb') as f:
            pickle.dump({
                'semantic_weight': self.semantic_weight,
                'normalize_scores': self.normalize_scores
            }, f)
            
        logger.info(f"Hybrid search engine saved to {directory}")
    
    @classmethod
    def load(cls, 
             directory: str, 
             embedding_model: SentenceTransformer, 
             products_df: pd.DataFrame) -> 'HybridSearchEngine':
        """Load all components from disk"""
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
            
        # Load configuration
        with open(os.path.join(directory, "hybrid_config.pkl"), 'rb') as f:
            config = pickle.load(f)
            
        # Load FAISS index
        faiss_index = FAISSVectorIndex()
        faiss_index.load_index(os.path.join(directory, "faiss_index.bin"))
        
        # Load BM25 engine
        bm25_engine = BM25SearchEngine()
        bm25_engine.load(os.path.join(directory, "bm25_engine.pkl"))
        
        # Create hybrid search engine
        engine = cls(
            faiss_index=faiss_index,
            bm25_engine=bm25_engine,
            embedding_model=embedding_model,
            products_df=products_df,
            semantic_weight=config['semantic_weight'],
            normalize_scores=config['normalize_scores']
        )
        
        logger.info(f"Hybrid search engine loaded from {directory}")
        return engine


def load_or_create_search_engine(
    data_path: str,
    model_path: str,
    embedding_model_name: str = 'all-MiniLM-L6-v2'
) -> HybridSearchEngine:
    """
    Load or create a hybrid search engine
    
    Args:
        data_path: Path to the product data file
        model_path: Path to save/load models
        embedding_model_name: Name of the SentenceTransformer model to use
    
    Returns:
        Initialized hybrid search engine
    """
    # Create model directory if it doesn't exist
    os.makedirs(model_path, exist_ok=True)
    
    # Load product data
    logger.info(f"Loading product data from {data_path}")
    products_df = pd.read_csv(data_path)
    
    # Load embedding model
    logger.info(f"Loading embedding model: {embedding_model_name}")
    embedding_model = SentenceTransformer(embedding_model_name)
    
    # Check if models exist
    if (os.path.exists(os.path.join(model_path, "faiss_index.bin")) and
        os.path.exists(os.path.join(model_path, "bm25_engine.pkl")) and
        os.path.exists(os.path.join(model_path, "hybrid_config.pkl"))):
        
        logger.info("Loading existing search engine models")
        return HybridSearchEngine.load(model_path, embedding_model, products_df)
    
    # Create search engine from scratch
    logger.info("Creating new search engine models")
    
    # Preprocess text for embeddings
    logger.info("Preprocessing text...")
    
    # Helper functions for text preprocessing
    def clean_text(text):
        if not isinstance(text, str):
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    # Create search text for BM25
    def create_search_text(row):
        parts = []
        if pd.notna(row.get('title')):
            parts.append(str(row['title']))
        if pd.notna(row.get('brand')):
            parts.append(str(row['brand']))
        if pd.notna(row.get('category')):
            parts.append(str(row['category']))
        if pd.notna(row.get('description')):
            parts.append(str(row['description']))
        return ' '.join(parts)
    
    # Prepare text for embeddings
    products_df['title_clean'] = products_df['title'].apply(clean_text)
    products_df['description_clean'] = products_df['description'].fillna('').apply(clean_text)
    products_df['embedding_text'] = (
        products_df['title_clean'] + ' ' + 
        products_df['description_clean']
    )
    
    # Prepare text for BM25
    products_df['search_text'] = products_df.apply(create_search_text, axis=1)
    
    # Generate embeddings
    logger.info("Generating product embeddings...")
    embeddings_file = os.path.join(model_path, "product_embeddings.npy")
    
    if os.path.exists(embeddings_file):
        logger.info(f"Loading existing embeddings from {embeddings_file}")
        product_embeddings = np.load(embeddings_file)
    else:
        logger.info("Computing new embeddings...")
        product_embeddings = embedding_model.encode(
            products_df['embedding_text'].tolist(),
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=True
        )
        np.save(embeddings_file, product_embeddings)
    
    # Build FAISS index
    logger.info("Building FAISS index...")
    faiss_index = FAISSVectorIndex()
    n_products = len(product_embeddings)
    
    # Choose index type based on dataset size
    if n_products < 5000:
        index_type = "FLAT"  # Exact search for smaller datasets
    elif n_products < 50000:
        index_type = "IVF_FLAT"  # Good balance
    else:
        index_type = "IVF_PQ"  # Memory efficient for large datasets
        
    faiss_index.build_index(product_embeddings, index_type=index_type)
    
    # Build BM25 engine
    logger.info("Building BM25 engine...")
    bm25_engine = BM25SearchEngine(k1=1.5, b=0.75)
    bm25_engine.fit(
        documents=products_df['search_text'].tolist(),
        doc_ids=products_df.index.tolist()
    )
    
    # Create hybrid search engine
    logger.info("Creating hybrid search engine...")
    hybrid_search = HybridSearchEngine(
        faiss_index=faiss_index,
        bm25_engine=bm25_engine,
        embedding_model=embedding_model,
        products_df=products_df,
        semantic_weight=0.65,  # Slightly favor semantic results
        normalize_scores=True
    )
    
    # Save all models
    logger.info("Saving search engine models...")
    hybrid_search.save(model_path)
    
    return hybrid_search
