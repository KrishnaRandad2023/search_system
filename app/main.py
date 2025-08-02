"""
FastAPI Main Application for Flipkart Search System
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from loguru import logger

from app.api import autosuggest, search, health, analytics, feedback, database_admin, system_demo, search_insights, autosuggest_feedback, smart_search
try:
    from app.api import hybrid_api
    HYBRID_API_AVAILABLE = True
except ImportError:
    HYBRID_API_AVAILABLE = False
    logger.warning("Hybrid API not available")

try:
    from app.api import direct_search
    DIRECT_SEARCH_AVAILABLE = True
except ImportError:
    DIRECT_SEARCH_AVAILABLE = False
    logger.warning("Direct search API not available")

try:
    from app.api import search_v2
    SEARCH_V2_AVAILABLE = True
except ImportError:
    SEARCH_V2_AVAILABLE = False
    logger.warning("Search v2 API not available")

try:
    from app.api import v1_endpoints
    V1_ENDPOINTS_AVAILABLE = True
except ImportError:
    V1_ENDPOINTS_AVAILABLE = False
    logger.warning("V1 endpoints API not available")
from app.config.settings import get_settings
from app.utils.logger import setup_logging
from app.db.database import init_db


# Setup logging
setup_logging()

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Flipkart Search System...")
    
    # Ensure required directories exist
    try:
        import os
        from pathlib import Path
        
        # Create models directory and subdirectories
        models_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "models"
        os.makedirs(models_dir, exist_ok=True)
        
        # Create data directories
        data_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(data_dir / "raw", exist_ok=True)
        
        logger.info("✅ Directory structure verified")
    except Exception as e:
        logger.error(f"⚠️ Error creating directories: {e}")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Load ML models (in background)
    logger.info("🧠 Loading ML models...")
    # TODO: Initialize ML models here
    
    logger.info("🎯 Application startup complete!")
    
    yield
    
    logger.info("🛑 Shutting down Flipkart Search System...")


# Create FastAPI app
app = FastAPI(
    title="Flipkart Search System API",
    description="AI/ML-powered e-commerce search with autosuggest and semantic search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response


# HTML interface for easy testing
@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with search interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏆 Flipkart Grid 7.0 - Search System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: linear-gradient(90deg, #2874f0, #3b82f6); color: white; padding: 30px; text-align: center; }
            .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
            .header p { font-size: 1.1rem; opacity: 0.9; }
            .main-content { padding: 40px; }
            .search-section { background: #f8fafc; border-radius: 10px; padding: 30px; margin-bottom: 30px; }
            .search-input { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #e2e8f0; border-radius: 8px; margin-bottom: 15px; }
            .search-input:focus { outline: none; border-color: #2874f0; }
            .btn { background: #2874f0; color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 5px; }
            .btn:hover { background: #1e5db8; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-top: 30px; }
            .card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
            .card h3 { color: #2874f0; margin-bottom: 15px; }
            .endpoint { background: #f1f5f9; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 14px; margin: 5px 0; }
            .badge { background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .stats { display: flex; justify-content: space-around; background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .stat { text-align: center; }
            .stat-number { font-size: 2rem; font-weight: bold; color: #2874f0; }
            .results { margin-top: 20px; padding: 20px; background: #f8fafc; border-radius: 8px; display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 Flipkart Grid 7.0</h1>
                <p>AI-Powered E-commerce Search System</p>
            </div>
            
            <div class="main-content">
                <div class="search-section">
                    <h2>🔍 Test Search & Autosuggest</h2>
                    <input type="text" id="searchInput" class="search-input" placeholder="Search for products... (e.g., 'laptop', 'mobile', 'gaming')" autocomplete="off">
                    <button class="btn" onclick="testSearch()">🔍 Search Products</button>
                    <button class="btn" onclick="testAutosuggest()">💡 Get Suggestions</button>
                    <button class="btn" onclick="openDocs()">📚 API Docs</button>
                    <div id="results" class="results"></div>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">5,000</div>
                        <div>Products</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">2,000</div>
                        <div>Autosuggest Queries</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">15+</div>
                        <div>API Endpoints</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">&lt;100ms</div>
                        <div>Response Time</div>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>🔍 Search API</h3>
                        <div class="endpoint">GET /search?q=mobile</div>
                        <div class="endpoint">GET /search/filters</div>
                        <div class="endpoint">GET /search/similar/{id}</div>
                        <span class="badge">5K Products</span>
                    </div>
                    
                    <div class="card">
                        <h3>💡 Autosuggest API</h3>
                        <div class="endpoint">GET /autosuggest?q=mob</div>
                        <div class="endpoint">GET /autosuggest/trending</div>
                        <div class="endpoint">GET /autosuggest/categories</div>
                        <span class="badge">Real-time</span>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Analytics API</h3>
                        <div class="endpoint">POST /analytics/event</div>
                        <div class="endpoint">GET /analytics/search-stats</div>
                        <div class="endpoint">GET /analytics/trends</div>
                        <span class="badge">Business Insights</span>
                    </div>
                    
                    <div class="card">
                        <h3>🏥 System Health</h3>
                        <div class="endpoint">GET /health</div>
                        <div class="endpoint">GET /health/detailed</div>
                        <div class="endpoint">GET /docs</div>
                        <span class="badge">Production Ready</span>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f1f5f9; border-radius: 8px;">
                    <h3>🎯 Ready for Flipkart Grid 7.0 Submission!</h3>
                    <p>Production-grade search system with intelligent autosuggest, advanced filtering, and ML-ready architecture.</p>
                </div>
            </div>
        </div>
        
        <script>
            function testSearch() {
                const query = document.getElementById('searchInput').value || 'mobile';
                // Try direct search first (working), fallback to regular search
                const searchUrl = '/api/v1/direct/search';
                fetch(`${searchUrl}?q=${encodeURIComponent(query)}&limit=5`)
                    .then(response => response.json())
                    .then(data => {
                        const results = document.getElementById('results');
                        results.style.display = 'block';
                        results.innerHTML = `
                            <h4>🔍 Search Results for "${data.query}"</h4>
                            <p><strong>Total:</strong> ${data.total_count} products found in ${data.response_time_ms?.toFixed(2)}ms</p>
                            <div style="max-height: 300px; overflow-y: auto;">
                                ${data.products.map(product => `
                                    <div style="border: 1px solid #e2e8f0; padding: 10px; margin: 5px 0; border-radius: 5px;">
                                        <strong>${product.title}</strong><br>
                                        <span style="color: #2874f0;">₹${product.current_price}</span> | 
                                        <span style="color: #10b981;">★${product.rating}</span> | 
                                        <span>${product.category}</span>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    })
                    .catch(error => {
                        // Fallback to regular search if direct search fails
                        fetch(`/search?q=${encodeURIComponent(query)}&limit=5`)
                            .then(response => response.json())
                            .then(data => {
                                const results = document.getElementById('results');
                                results.style.display = 'block';
                                results.innerHTML = `
                                    <h4>🔍 Search Results for "${data.query}" (Fallback)</h4>
                                    <p><strong>Total:</strong> ${data.total_count} products found</p>
                                    <div style="max-height: 300px; overflow-y: auto;">
                                        ${data.products.map(product => `
                                            <div style="border: 1px solid #e2e8f0; padding: 10px; margin: 5px 0; border-radius: 5px;">
                                                <strong>${product.title}</strong><br>
                                                <span style="color: #2874f0;">₹${product.price}</span> | 
                                                <span style="color: #10b981;">★${product.rating}</span> | 
                                                <span>${product.category}</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                `;
                            })
                            .catch(fallbackError => {
                                document.getElementById('results').innerHTML = `<p style="color: red;">Search Error: ${fallbackError.message}</p>`;
                            });
                    });
            }
            
            function testAutosuggest() {
                const query = document.getElementById('searchInput').value || 'mob';
                fetch(`/api/v1/metadata/autosuggest?q=${encodeURIComponent(query)}&limit=8`)
                    .then(response => response.json())
                    .then(data => {
                        const results = document.getElementById('results');
                        results.style.display = 'block';
                        results.innerHTML = `
                            <h4>💡 Autosuggest for "${data.query}" (${data.total_count || data.suggestions.length} results)</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
                                ${data.suggestions.map(suggestion => `
                                    <span style="background: #2874f0; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;">
                                        ${suggestion.text} (${suggestion.popularity})
                                    </span>
                                `).join('')}
                            </div>
                        `;
                    })
                    .catch(error => {
                        document.getElementById('results').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                    });
            }
            
            function openDocs() {
                window.open('/docs', '_blank');
            }
            
            // Auto-suggest on typing
            document.getElementById('searchInput').addEventListener('input', function(e) {
                if (e.target.value.length > 2) {
                    // Optional: implement real-time autosuggest here
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content


# API info endpoint  
@app.get("/api", response_model=Dict[str, Any])
async def api_info():
    """API information endpoint"""
    return {
        "message": "🛍️ Flipkart Search System API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "search": "/search",
            "autosuggest": "/autosuggest", 
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Real-time autosuggest",
            "Semantic product search",
            "ML-powered ranking",
            "Typo correction",
            "Analytics tracking"
        ]
    }


# Include API routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(autosuggest.router, prefix="/autosuggest", tags=["Autosuggest"])
app.include_router(autosuggest_feedback.router, prefix="/autosuggest/feedback", tags=["Autosuggest Feedback"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(smart_search.router, prefix="/search", tags=["Smart Search"])
if HYBRID_API_AVAILABLE:
    app.include_router(hybrid_api.router, tags=["Hybrid ML Search"])
app.include_router(search_insights.router, prefix="/search-insights", tags=["Search Insights"])
if SEARCH_V2_AVAILABLE:
    app.include_router(search_v2.router, tags=["Search v2"])  # Frontend search API 
    app.include_router(search_v2.v1_router, tags=["Search v2 Analytics"])  # v1 compatibility for tracking
if V1_ENDPOINTS_AVAILABLE:
    app.include_router(v1_endpoints.router, prefix="/api/v1/metadata", tags=["API v1 Metadata"])  # Other frontend API endpoints
if DIRECT_SEARCH_AVAILABLE:
    app.include_router(direct_search.router, tags=["Direct Search"])  # Working search endpoint
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"]) 
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(database_admin.router, tags=["Database Admin"])  # Admin endpoints
app.include_router(system_demo.router, tags=["System Demo"])  # Demo endpoints


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG_MODE,
        workers=1 if settings.DEBUG_MODE else settings.WORKERS
    )
