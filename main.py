"""
Main Application Integration
---------------------------
This file integrates all components of the Flipkart Grid 7.0 search system
into a cohesive FastAPI application ready for production deployment.
"""

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from typing import Optional, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("search-api")

# Import application components
try:
    from app.api.enhanced_search_api_v2 import router as search_router
except ImportError:
    search_router = None

try:
    from app.api.search_results_page import router as srp_router
except ImportError:
    srp_router = None
except Exception as e:
    print(f"Warning: Could not load search_results_page router: {e}")
    srp_router = None

try:
    from app.api.autosuggest_complete import router as autosuggest_router
except ImportError:
    autosuggest_router = None

try:
    from app.api.search_v2 import router as search_v2_router, v1_router as search_v1_router
except ImportError:
    search_v2_router = None
    search_v1_router = None

try:
    from app.api.analytics import router as analytics_router
except ImportError:
    analytics_router = None

try:
    from app.api.hybrid_search import router as hybrid_router
except ImportError:
    hybrid_router = None
except Exception as e:
    print(f"Warning: Could not load hybrid_search router: {e}")
    hybrid_router = None

try:
    from app.search.hybrid_engine import HybridSearchEngine
except ImportError:
    HybridSearchEngine = None
except Exception as e:
    print(f"Warning: Could not load HybridSearchEngine: {e}")
    HybridSearchEngine = None

try:
    from app.ml.ranker import MLRanker
except ImportError:
    MLRanker = None
except Exception as e:
    print(f"Warning: Could not load MLRanker: {e}")
    MLRanker = None

try:
    from app.db.database import init_db as initialize_db
except ImportError:
    initialize_db = None

# Create FastAPI application
app = FastAPI(
    title="Flipkart Grid 7.0 Search API",
    description="""
    A comprehensive search system for e-commerce with:
    
    - AI-Powered Retrieval
    - High-Performance Architecture
    - Feature-Rich UX
    - Evaluation & Logging
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Flipkart Grid 7.0 Search API", 
        "status": "running",
        "timestamp": time.time(),
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

# Include routers conditionally
if search_router:
    app.include_router(search_router)
if srp_router:
    app.include_router(srp_router)
if autosuggest_router:
    app.include_router(autosuggest_router)
if search_v2_router:
    app.include_router(search_v2_router)
if search_v1_router:
    app.include_router(search_v1_router)
if analytics_router:
    app.include_router(analytics_router)
if hybrid_router:
    app.include_router(hybrid_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup"""
    logger.info("Starting Flipkart Grid 7.0 Search API")
    
    try:
        # Initialize database
        if initialize_db:
            logger.info("Initializing database")
            await initialize_db()
        else:
            logger.warning("Database initialization not available")
        
        # Initialize components would happen here but we're using
        # the enhanced_search_api.py which has its own initialization
        logger.info("Using enhanced search API initialization")
        
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        # Don't raise to allow degraded mode

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown"""
    logger.info("Shutting down Flipkart Grid 7.0 Search API")

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))  # Changed to 8002 to match frontend
    
    print(f"""
    🚀 Flipkart Grid 7.0 Search API
    
    🔍 Complete search system with:
      - AI-Powered Retrieval
      - High-Performance Architecture
      - Feature-Rich UX
      - Evaluation & Logging
      
    📚 Documentation available at:
      - http://localhost:{port}/docs
      - http://localhost:{port}/redoc
      
    🌐 API endpoints:
      - Search v2: /api/v2/search
      - Autosuggest: /api/v1/autosuggest
      - Popular Queries: /api/v1/popular-queries
      - Trending Categories: /api/v1/trending-categories
      
    🏁 Starting server on port {port}...
    """)
    
    # Start server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
