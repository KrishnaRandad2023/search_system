"""
Project configuration file for Flipkart Search System
"""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ML models configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence transformer model name

# Search engine configuration
DEFAULT_SEARCH_CONFIG = {
    "semantic_weight": 0.65,  # Weight of semantic search vs lexical search
    "normalize_scores": True,  # Normalize scores before combining
    "min_score_threshold": 0.1,  # Minimum score threshold for results
    "max_results": 100,  # Maximum number of results to return
    "use_ml_ranking": True,  # Whether to use ML ranking by default
}

class Config:
    """Application configuration class."""
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///flipkart_products.db")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "flipkart_products.db")
    
    # ML Model settings
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    
    # Search settings
    MAX_SEARCH_RESULTS = 100
    DEFAULT_SEARCH_RESULTS = 20
    AUTOSUGGEST_MAX_RESULTS = 10
    
    # Performance settings
    FAISS_INDEX_TYPE = "IndexFlatIP"  # Inner Product for cosine similarity
    BATCH_SIZE = 32
    
    # API settings
    API_HOST = "0.0.0.0"
    API_PORT = 8002
    DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
    
    # File paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    MODELS_DIR = MODEL_DIR
    LOGS_DIR = LOG_DIR
    
    # Autosuggest settings
    AUTOSUGGEST_CATEGORIES_FILE = DATA_DIR / "categories.json"
    AUTOSUGGEST_BRANDS_FILE = DATA_DIR / "brands.json"
    AUTOSUGGEST_TRENDING_FILE = DATA_DIR / "trending_queries.json"
    
    # Business scoring weights
    BUSINESS_SCORING_WEIGHTS = {
        "stock_availability": 0.3,
        "ctr": 0.25,
        "conversion_rate": 0.25,
        "price_competitiveness": 0.2
    }
    
    # ML Ranker settings
    ML_RANKER_MODEL_PATH = MODEL_DIR / "ranking_model.pkl"
    ML_RANKER_FEATURES = [
        "relevance_score", "business_score", "popularity", 
        "rating", "price_normalized", "discount_percentage"
    ]
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get database path."""
        return cls.DATABASE_PATH
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Get data directory path."""
        return cls.DATA_DIR

# ML ranker configuration
ML_RANKER_CONFIG = {
    "objective": "rank:ndcg",
    "learning_rate": 0.1,
    "num_boost_round": 100,
    "use_early_stopping": True,
    "early_stopping_rounds": 10,
}

# API configuration
API_CONFIG = {
    "title": "Flipkart Search API",
    "description": "Production-grade search API for Flipkart Grid 7.0",
    "version": "1.0.0",
    "openapi_tags": [
        {
            "name": "search",
            "description": "Search operations",
        },
        {
            "name": "autocomplete",
            "description": "Autocomplete operations",
        },
        {
            "name": "metrics",
            "description": "System metrics and analytics",
        },
    ],
    "allow_cors": True,
    "cache_ttl": 300,  # Cache TTL in seconds
}

# Development/production mode
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
ENV = os.environ.get("ENV", "development")

# Database settings
if ENV == "production":
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/flipkart_search")
else:
    DATABASE_URL = f"sqlite:///{DATA_DIR}/flipkart_search.db"
