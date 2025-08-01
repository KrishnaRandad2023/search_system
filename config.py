"""
Configuration settings for Flipkart Grid 7.0 Search System
"""

import os
from pathlib import Path

class Config:
    """Configuration class for the search system."""
    
    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "flipkart_products.db")
    
    # Ensure data directory exists
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # ML Model paths
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    EMBEDDING_MODEL_PATH = os.path.join(MODEL_DIR, "embeddings")
    ML_RANKER_MODEL_PATH = os.path.join(MODEL_DIR, "ranker.pkl")
    
    # Search configuration
    DEFAULT_SEARCH_LIMIT = 20
    MAX_SEARCH_LIMIT = 100
    
    # API configuration
    API_HOST = "127.0.0.1"
    API_PORT = 8000
    
    # Logging configuration
    LOG_LEVEL = "INFO"
