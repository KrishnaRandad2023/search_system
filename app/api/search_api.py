"""
FastAPI Search API for Flipkart Grid 7.0
Production-grade API with comprehensive search features, caching, and monitoring
"""

from fastapi import FastAPI, Query, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
import time
import pandas as pd
import os
import json
from sentence_transformers import SentenceTransformer
import logging
from functools import lru_cache
from datetime import datetime
import random
import uuid

# Import our search components
from app.search.hybrid_engine import HybridSearchEngine, load_or_create_search_engine
from app.ml.ranker import MLRanker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Flipkart Search API",
    description="Production-grade search API for Flipkart Grid 7.0",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global variables
search_engine = None
ml_ranker = None
products_df = None
user_sessions = {}
search_metrics = {
    "total_searches": 0,
    "avg_latency": 0,
    "success_rate": 1.0,
    "top_queries": {},
    "zero_results": 0
}

# Define path constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Pydantic models for request and response
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Offset for pagination")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters to apply")
    session_id: Optional[str] = Field(None, description="Session ID for user tracking")
    use_ml_ranking: bool = Field(True, description="Whether to apply ML ranking")

class ProductResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str] = None
    brand: str
    price: float
    rating: float
    image_url: Optional[str] = None
    position: int
    relevance_score: float

class SearchResponse(BaseModel):
    query: str
    total_results: int
    time_ms: float
    results: List[ProductResponse]
    session_id: str
    filters: Dict[str, List[str]]
    search_id: str

class AutocompleteRequest(BaseModel):
    prefix: str = Field(..., description="The prefix to autocomplete")
    limit: int = Field(10, description="Maximum number of suggestions")
    session_id: Optional[str] = Field(None, description="Session ID for user tracking")

class AutocompleteResponse(BaseModel):
    prefix: str
    suggestions: List[str]
    time_ms: float
    session_id: str

class SearchMetricsResponse(BaseModel):
    total_searches: int
    avg_latency: float
    success_rate: float
    top_queries: Dict[str, int]
    zero_results: int
    active_sessions: int

# Helper functions
def get_session_id(request: Union[SearchRequest, AutocompleteRequest]) -> str:
    """Get or create a session ID"""
    if request.session_id:
        return request.session_id
    return str(uuid.uuid4())

def record_search_metrics(query: str, latency: float, num_results: int):
    """Record search metrics for monitoring"""
    global search_metrics
    
    search_metrics["total_searches"] += 1
    
    # Update average latency with moving average
    prev_avg = search_metrics["avg_latency"]
    count = search_metrics["total_searches"]
    search_metrics["avg_latency"] = prev_avg + (latency - prev_avg) / count
    
    # Update success rate
    if num_results == 0:
        search_metrics["zero_results"] += 1
        
    success_rate = 1 - (search_metrics["zero_results"] / count)
    search_metrics["success_rate"] = success_rate
    
    # Update top queries
    if query in search_metrics["top_queries"]:
        search_metrics["top_queries"][query] += 1
    else:
        search_metrics["top_queries"][query] = 1
        
    # Keep only top 10 queries
    search_metrics["top_queries"] = dict(
        sorted(search_metrics["top_queries"].items(), 
               key=lambda x: x[1], 
               reverse=True)[:10]
    )

def apply_filters(results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """Apply filters to search results"""
    if not filters:
        return results
        
    filtered_results = results.copy()
    
    for field, value in filters.items():
        if field == 'price_range':
            min_price = value.get('min', 0)
            max_price = value.get('max', float('inf'))
            filtered_results = [
                r for r in filtered_results 
                if min_price <= r['price'] <= max_price
            ]
        elif field == 'rating_min':
            filtered_results = [
                r for r in filtered_results 
                if r['rating'] >= value
            ]
        elif field == 'brand':
            if isinstance(value, list):
                filtered_results = [
                    r for r in filtered_results 
                    if r['brand'] in value
                ]
            else:
                filtered_results = [
                    r for r in filtered_results 
                    if r['brand'] == value
                ]
        elif field == 'category':
            if isinstance(value, list):
                filtered_results = [
                    r for r in filtered_results 
                    if r['category'] in value
                ]
            else:
                filtered_results = [
                    r for r in filtered_results 
                    if r['category'] == value
                ]
                
    return filtered_results

def extract_available_filters(results: List[Dict]) -> Dict[str, Any]:
    """Extract available filter values from results"""
    categories = set()
    brands = set()
    
    for result in results:
        categories.add(result['category'])
        brands.add(result['brand'])
    
    return {
        'categories': sorted(list(categories)),
        'brands': sorted(list(brands)),
        'price_range': {
            'min': min([r['price'] for r in results]) if results else 0,
            'max': max([r['price'] for r in results]) if results else 0,
        },
        'rating_range': {
            'min': min([r['rating'] for r in results]) if results else 0,
            'max': max([r['rating'] for r in results]) if results else 0,
        }
    }

# Autocomplete implementation
class AutocompleteEngine:
    """Simple Trie-based autocomplete engine"""
    
    def __init__(self):
        self.trie = {}
        self.common_queries = set()
        
    def add_query(self, query: str):
        """Add a query to the trie"""
        query = query.lower().strip()
        self.common_queries.add(query)
        
        # Add to trie
        node = self.trie
        for char in query:
            if char not in node:
                node[char] = {}
            node = node[char]
        
        # Mark end of word
        if '_end_' not in node:
            node['_end_'] = 0
        node['_end_'] += 1
    
    def search(self, prefix: str, limit: int = 10) -> List[str]:
        """Search for suggestions based on prefix"""
        prefix = prefix.lower().strip()
        
        # Navigate to prefix node
        node = self.trie
        for char in prefix:
            if char not in node:
                return []  # Prefix not found
            node = node[char]
        
        # Collect all completions
        suggestions = []
        self._collect_suggestions(node, prefix, suggestions, limit)
        return suggestions
    
    def _collect_suggestions(self, node: Dict, prefix: str, suggestions: List[str], limit: int):
        """Recursively collect suggestions from trie"""
        if len(suggestions) >= limit:
            return
            
        if '_end_' in node:
            suggestions.append(prefix)
            
        for char, next_node in sorted(node.items()):
            if char != '_end_' and len(suggestions) < limit:
                self._collect_suggestions(next_node, prefix + char, suggestions, limit)
                
    def build_from_dataframe(self, df: pd.DataFrame):
        """Build autocomplete from product data"""
        # Add titles
        for title in df['title'].dropna():
            title_lower = title.lower()
            self.add_query(title)
            
            # Add words from title
            words = title_lower.split()
            for i in range(len(words)):
                phrase = ' '.join(words[i:min(i+3, len(words))])
                if len(phrase) >= 3:
                    self.add_query(phrase)
        
        # Add brands
        for brand in df['brand'].dropna().unique():
            self.add_query(brand)
            
        # Add categories
        for category in df['category'].dropna().unique():
            self.add_query(category)
            
        logger.info(f"Built autocomplete with {len(self.common_queries)} entries")

# Function to initialize components
@app.on_event("startup")
async def startup_event():
    """Initialize search components on startup"""
    global search_engine, ml_ranker, products_df, autocomplete
    
    try:
        # Load product data
        product_data_path = os.path.join(DATA_DIR, "products.csv")
        if not os.path.exists(product_data_path):
            # Create sample data for development
            logger.info("Creating sample product data")
            products_df = pd.DataFrame({
                'product_id': [f'P{i:04d}' for i in range(100)],
                'title': [f'Sample Product {i}' for i in range(100)],
                'description': [f'Description for product {i}' for i in range(100)],
                'category': ['Electronics'] * 50 + ['Fashion'] * 50,
                'brand': [f'Brand{i%10}' for i in range(100)],
                'price': [random.uniform(500, 10000) for _ in range(100)],
                'rating': [random.uniform(3, 5) for _ in range(100)],
            })
            os.makedirs(os.path.dirname(product_data_path), exist_ok=True)
            products_df.to_csv(product_data_path, index=False)
        else:
            logger.info(f"Loading product data from {product_data_path}")
            products_df = pd.read_csv(product_data_path)
            
        # Initialize search engine
        search_engine_path = os.path.join(MODEL_DIR, "search_engine")
        os.makedirs(search_engine_path, exist_ok=True)
        
        logger.info("Initializing search engine")
        search_engine = load_or_create_search_engine(
            data_path=product_data_path,
            model_path=search_engine_path,
            embedding_model_name='all-MiniLM-L6-v2'  # Small but effective model
        )
        
        # Initialize ML ranker
        ml_ranker_path = os.path.join(MODEL_DIR, "ml_ranker.pkl")
        logger.info("Initializing ML ranker")
        ml_ranker = MLRanker(model_path=ml_ranker_path)
        
        # Train ranker if needed
        if not ml_ranker.is_trained and os.path.exists(product_data_path):
            from app.ml.ranker import generate_synthetic_training_data
            
            logger.info("Generating synthetic training data for ML ranker")
            search_data, click_data = generate_synthetic_training_data(products_df, num_queries=100)
            
            logger.info("Training ML ranker")
            metrics = ml_ranker.train(search_data, click_data)
            logger.info(f"ML ranker training metrics: {metrics}")
            
            # Save model
            ml_ranker.save(ml_ranker_path)
        
        # Initialize autocomplete
        logger.info("Initializing autocomplete engine")
        autocomplete = AutocompleteEngine()
        autocomplete.build_from_dataframe(products_df)
        
        logger.info("Startup complete - Search API is ready")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

# API endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Flipkart Search API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "/search", 
            "/autocomplete", 
            "/metrics"
        ]
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search products with comprehensive filtering and ranking
    """
    global search_engine, ml_ranker, user_sessions
    
    start_time = time.time()
    
    # Validate request
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # Get or create session
    session_id = get_session_id(request)
    
    # Update session data
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            "queries": [],
            "last_active": datetime.now(),
            "results_seen": set()
        }
    
    user_sessions[session_id]["last_active"] = datetime.now()
    user_sessions[session_id]["queries"].append(request.query)
    
    # Perform search
    try:
        # Execute search query
        search_results = search_engine.search(
            query=request.query,
            k=max(50, request.limit * 2)  # Get extra results for filtering
        )
        
        # Apply ML ranking if requested
        if request.use_ml_ranking and ml_ranker and ml_ranker.is_trained:
            search_results = ml_ranker.rerank(search_results)
        
        # Apply filters
        filtered_results = apply_filters(search_results, request.filters)
        
        # Apply pagination
        paginated_results = filtered_results[request.offset:request.offset + request.limit]
        
        # Extract available filters
        available_filters = extract_available_filters(search_results)
        
        # Create response
        response = {
            "query": request.query,
            "total_results": len(filtered_results),
            "time_ms": round((time.time() - start_time) * 1000, 2),
            "results": [
                {
                    "id": result["id"],
                    "title": result["title"],
                    "description": result["description"],
                    "category": result["category"],
                    "subcategory": result.get("subcategory", None),
                    "brand": result["brand"],
                    "price": result["price"],
                    "rating": result["rating"],
                    "image_url": result.get("image_url", None),
                    "position": i + 1 + request.offset,
                    "relevance_score": result.get("combined_score", 0.0)
                }
                for i, result in enumerate(paginated_results)
            ],
            "session_id": session_id,
            "filters": available_filters,
            "search_id": str(uuid.uuid4())
        }
        
        # Record metrics
        record_search_metrics(
            query=request.query,
            latency=response["time_ms"] / 1000,
            num_results=len(filtered_results)
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/autocomplete", response_model=AutocompleteResponse)
async def get_autocomplete(request: AutocompleteRequest):
    """
    Get autocomplete suggestions based on prefix
    """
    global autocomplete, user_sessions
    
    start_time = time.time()
    
    # Validate request
    if not autocomplete:
        raise HTTPException(status_code=503, detail="Autocomplete engine not initialized")
    
    if not request.prefix or len(request.prefix.strip()) == 0:
        return {
            "prefix": "",
            "suggestions": [],
            "time_ms": 0,
            "session_id": get_session_id(request)
        }
        
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    
    # Update session data
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            "queries": [],
            "last_active": datetime.now(),
            "results_seen": set()
        }
    
    user_sessions[session_id]["last_active"] = datetime.now()
    
    # Get suggestions
    try:
        suggestions = autocomplete.search(request.prefix, limit=request.limit)
        
        # Personalize suggestions if we have session data
        if session_id in user_sessions and len(user_sessions[session_id]["queries"]) > 0:
            # Boost suggestions that match previous queries
            previous_queries = user_sessions[session_id]["queries"]
            
            # Simple personalization - move previous queries to top if they match prefix
            previous_matches = [
                q for q in previous_queries 
                if q.lower().startswith(request.prefix.lower())
            ]
            
            # Deduplicate while preserving order
            seen = set()
            personalized = [x for x in previous_matches if not (x in seen or seen.add(x))]
            
            # Add remaining suggestions
            for s in suggestions:
                if s not in seen and len(personalized) < request.limit:
                    personalized.append(s)
                    seen.add(s)
                    
            suggestions = personalized
        
        response = {
            "prefix": request.prefix,
            "suggestions": suggestions,
            "time_ms": round((time.time() - start_time) * 1000, 2),
            "session_id": session_id
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Autocomplete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Autocomplete error: {str(e)}")

@app.get("/metrics", response_model=SearchMetricsResponse)
async def get_metrics():
    """
    Get search system metrics
    """
    global search_metrics, user_sessions
    
    # Clean up inactive sessions (older than 30 minutes)
    thirty_mins_ago = datetime.now().timestamp() - (30 * 60)
    active_sessions = {
        sid: data for sid, data in user_sessions.items()
        if data["last_active"].timestamp() > thirty_mins_ago
    }
    user_sessions = active_sessions
    
    # Create response
    response = {
        "total_searches": search_metrics["total_searches"],
        "avg_latency": round(search_metrics["avg_latency"] * 1000, 2),  # Convert to ms
        "success_rate": round(search_metrics["success_rate"] * 100, 2),  # Convert to percentage
        "top_queries": search_metrics["top_queries"],
        "zero_results": search_metrics["zero_results"],
        "active_sessions": len(user_sessions)
    }
    
    return JSONResponse(content=response)

@app.post("/feedback")
async def record_feedback(request: Request):
    """
    Record user feedback for search results
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["session_id", "search_id", "product_id", "action"]
        if not all(field in data for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        # Save feedback for future ML training
        feedback_file = os.path.join(DATA_DIR, "user_feedback.jsonl")
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        
        # Add timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Append to file
        with open(feedback_file, "a") as f:
            f.write(json.dumps(data) + "\n")
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "search_engine": "initialized" if search_engine else "not_initialized",
            "ml_ranker": "trained" if ml_ranker and ml_ranker.is_trained else "not_trained",
            "autocomplete": "initialized" if 'autocomplete' in globals() else "not_initialized",
            "database": "connected" if products_df is not None else "not_connected"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/a/b/{experiment_id}/{variant}")
async def record_ab_test(
    experiment_id: str = Path(..., description="A/B test experiment ID"),
    variant: str = Path(..., description="A/B test variant"),
    session_id: str = Query(..., description="Session ID")
):
    """Record A/B test assignment"""
    try:
        # Save A/B test assignment
        ab_test_file = os.path.join(DATA_DIR, "ab_tests.jsonl")
        os.makedirs(os.path.dirname(ab_test_file), exist_ok=True)
        
        data = {
            "experiment_id": experiment_id,
            "variant": variant,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Append to file
        with open(ab_test_file, "a") as f:
            f.write(json.dumps(data) + "\n")
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error recording A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording A/B test: {str(e)}")

# Run the application with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
