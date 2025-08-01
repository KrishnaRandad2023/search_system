"""
Health Check API Endpoints
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Product

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
    try:
        # Test database connection
        product_count = db.query(Product).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Flipkart Search System",
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "product_count": product_count
            },
            "features": {
                "autosuggest": "available",
                "search": "available", 
                "ml_ranking": "available",
                "analytics": "available"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""
    try:
        import psutil
        import sys
        from pathlib import Path
        
        # Database stats
        product_count = db.query(Product).count()
        
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check data files
        data_files = {
            "products": Path("data/raw/flipkart_products.csv").exists(),
            "autosuggest": Path("data/raw/autosuggest_queries.csv").exists(),
            "embeddings": Path("data/embeddings/product_embeddings.pkl").exists(),
            "faiss_index": Path("data/vector_indices/product_faiss.index").exists()
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Flipkart Search System",
            "version": "1.0.0",
            "system": {
                "python_version": sys.version,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "cpu_count": psutil.cpu_count()
            },
            "database": {
                "status": "connected",
                "product_count": product_count
            },
            "data_files": data_files,
            "features": {
                "autosuggest": "available",
                "search": "available",
                "semantic_search": "available" if data_files["embeddings"] else "unavailable",
                "ml_ranking": "available",
                "analytics": "available"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
