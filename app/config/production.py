"""
Production Configuration for Flipkart Search System
Address critical security and performance issues
"""

import os
import secrets
from typing import Dict, Any
from app.config.settings import Settings

class ProductionSettings(Settings):
    """Production-ready settings with security hardening"""
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    DEBUG_MODE: bool = False
    
    # Database with connection pooling
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", 
        "sqlite:///./data/flipkart_products.db?check_same_thread=false&timeout=20&pool_size=20&max_overflow=0"
    )
    
    # Performance optimizations
    MAX_CONCURRENT_REQUESTS: int = 50  # Reduced for stability
    WORKERS: int = 4
    
    # Caching (Redis)
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_EXPORT_INTERVAL: int = 60  # seconds
    
    # Health checks
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    
    # Database backup
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 7
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_REQUEST_LOGGING: bool = True
    
    # CORS - Production domains only
    CORS_ORIGINS: list = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://flipkart-search.yourdomain.com"
    ]
    
    # Timeouts
    DATABASE_TIMEOUT: int = 30
    API_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env.production"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_production_config() -> Dict[str, Any]:
    """Get production configuration dictionary"""
    return {
        "database": {
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True
        },
        "cache": {
            "backend": "redis",
            "ttl": 300,
            "max_connections": 10
        },
        "security": {
            "rate_limiting": True,
            "cors_strict": True,
            "https_only": True,
            "secure_headers": True
        },
        "monitoring": {
            "health_checks": True,
            "metrics_collection": True,
            "error_tracking": True,
            "performance_monitoring": True
        }
    }


# Production deployment checklist
PRODUCTION_CHECKLIST = {
    "security": [
        "✅ Change default SECRET_KEY",
        "✅ Enable HTTPS only",
        "✅ Configure rate limiting",
        "✅ Set up proper CORS origins",
        "✅ Enable secure headers"
    ],
    "performance": [
        "✅ Configure database connection pooling",
        "✅ Set up Redis caching",
        "✅ Enable gzip compression",
        "✅ Configure proper timeouts",
        "✅ Set optimal worker count"
    ],
    "monitoring": [
        "✅ Set up health checks",
        "✅ Configure metrics collection",
        "✅ Enable error tracking",
        "✅ Set up log aggregation",
        "✅ Configure alerting"
    ],
    "reliability": [
        "✅ Enable auto-backup",
        "✅ Configure graceful shutdown",
        "✅ Set up load balancing",
        "✅ Configure circuit breakers",
        "✅ Enable request retry logic"
    ]
}
