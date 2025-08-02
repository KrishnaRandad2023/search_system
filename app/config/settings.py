"""
Application Configuration Settings
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    DEBUG_MODE: bool = Field(default=True, description="Debug mode")
    WORKERS: int = Field(default=4, description="Number of workers")
    
    # Database Configuration - Fixed to use correct database file
    DATABASE_URL: str = Field(
        default="sqlite:///./data/flipkart_products.db",
        description="Database URL"
    )
    TEST_DATABASE_URL: str = Field(
        default="sqlite:///./data/db/test.db",
        description="Test database URL"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL"
    )
    
    # ML Model Configuration
    SENTENCE_TRANSFORMER_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        description="Embedding dimension"
    )
    FAISS_INDEX_PATH: str = Field(
        default="./data/vector_indices/product_faiss.index",
        description="FAISS index path"
    )
    
    # Search Configuration
    MAX_AUTOSUGGEST_RESULTS: int = Field(
        default=10,
        description="Maximum autosuggest results"
    )
    MAX_SEARCH_RESULTS: int = Field(
        default=50,
        description="Maximum search results"
    )
    SEARCH_TIMEOUT_MS: int = Field(
        default=5000,
        description="Search timeout in milliseconds"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3000", "*"],
        description="CORS allowed origins"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        description="Maximum concurrent requests"
    )
    
    # Data Processing
    BATCH_SIZE: int = Field(default=1000, description="Batch size for processing")
    EMBEDDING_BATCH_SIZE: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    
    # External APIs
    FLIPKART_API_KEY: Optional[str] = Field(
        default=None,
        description="Flipkart API key"
    )
    GOOGLE_CLOUD_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Cloud API key"
    )
    
    # Monitoring
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus port")
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# @lru_cache()  # Temporarily disabled for database fix
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
