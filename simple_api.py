"""
Simple API test script with direct database access to bypass ORM issues
"""

import sqlite3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Flipkart Search Direct API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v2/search", summary="Search products directly from database")
async def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Number of results to return"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(20, description="Results per page"),
    sort_by: str = Query("relevance", description="Sort method"),
):
    """Search products in the database directly"""
    conn = sqlite3.connect('./flipkart_search.db')
    cursor = conn.cursor()
    
    search_terms = q.split()
    like_conditions = []
    params = []
    
    for term in search_terms:
        like_term = f"%{term}%"
        like_conditions.append("(title LIKE ? OR description LIKE ? OR category LIKE ? OR brand LIKE ?)")
        params.extend([like_term, like_term, like_term, like_term])
    
    where_clause = " AND ".join(like_conditions)
    
    # Get total count for pagination
    cursor.execute(f"SELECT COUNT(*) FROM products WHERE {where_clause}", params)
    total_count = cursor.fetchone()[0]
    
    # Calculate pagination
    offset = (page - 1) * per_page
    actual_limit = per_page
    
    # Get the actual results
    cursor.execute(f"""
    SELECT id, product_id, title, description, category, subcategory, brand, 
           current_price, original_price, discount_percent, rating, num_ratings,
           is_available, images, tags, created_at
    FROM products 
    WHERE {where_clause}
    LIMIT ? OFFSET ?
    """, params + [actual_limit, offset])
    
    products = []
    for row in cursor.fetchall():
        # Also get some additional product data for categories and brands
        products.append({
            "id": str(row[0]),  # Convert to string as frontend expects
            "product_id": row[1],
            "title": row[2],
            "description": row[3] or "",
            "category": row[4] or "",
            "subcategory": row[5] or "",
            "brand": row[6] or "",
            "current_price": row[7],
            "original_price": row[8],
            "discount_percent": row[9],
            "rating": row[10],
            "num_ratings": row[11],
            "availability": "In Stock" if row[12] else "Out of Stock",
            "image_url": row[13] or "",
            "features": row[14].split(",") if row[14] else [],
            "specifications": "",
            "relevance_score": 0.95,  # Dummy scores for frontend
            "popularity_score": 0.85,
            "business_score": 0.75,
            "final_score": 0.9
        })
    
    # Get aggregate data for filters
    cursor.execute("SELECT DISTINCT category FROM products LIMIT 20")
    categories = [{"name": row[0], "count": 10} for row in cursor.fetchall() if row[0]]
    
    cursor.execute("SELECT DISTINCT brand FROM products LIMIT 20")
    brands = [{"name": row[0], "count": 5} for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page
    
    # Return in the format expected by frontend
    return {
        "products": products,
        "total_results": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "filters_applied": {},
        "search_metadata": {
            "query": q,
            "search_type": "hybrid",
            "response_time_ms": 150,
            "has_typo_correction": False,
            "semantic_similarity": 0.8
        },
        "aggregations": {
            "categories": categories,
            "brands": brands,
            "price_ranges": [
                {"range": "Under ₹5,000", "count": 10},
                {"range": "₹5,000 - ₹10,000", "count": 15},
                {"range": "₹10,000 - ₹20,000", "count": 20},
                {"range": "₹20,000 - ₹50,000", "count": 25},
                {"range": "Over ₹50,000", "count": 10}
            ],
            "ratings": [
                {"rating": 4, "count": 50},
                {"rating": 3, "count": 30},
                {"rating": 2, "count": 15},
                {"rating": 1, "count": 5}
            ]
        }
    }

@app.get("/api/products/{product_id}", summary="Get product by ID")
async def get_product(product_id: str):
    """Get a product by its ID"""
    conn = sqlite3.connect('./flipkart_search.db')
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM products WHERE product_id = ?
    """, (product_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Product not found"}
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Create a dictionary from column names and values
    product = dict(zip(columns, row))
    
    conn.close()
    return product

@app.get("/api/categories", summary="Get all categories")
async def get_categories():
    """Get all product categories"""
    conn = sqlite3.connect('./flipkart_search.db')
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT DISTINCT category FROM products
    """)
    
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return {"categories": categories}

@app.get("/api/v1/metadata/autosuggest", summary="Get autosuggest recommendations")
async def get_autosuggest(
    q: str = Query(..., description="Query prefix to get suggestions for"),
    limit: int = Query(10, description="Number of suggestions to return")
):
    """Get autosuggest recommendations"""
    conn = sqlite3.connect('./flipkart_search.db')
    cursor = conn.cursor()
    
    # Get product suggestions
    cursor.execute("""
    SELECT title, category, brand 
    FROM products 
    WHERE title LIKE ? 
    LIMIT ?
    """, (f"%{q}%", limit))
    
    results = cursor.fetchall()
    conn.close()
    
    suggestions = []
    for i, row in enumerate(results):
        suggestions.append({
            "text": row[0],
            "score": 1.0 - (i * 0.05),
            "suggestion_type": "product",
            "metadata": {
                "category": row[1],
                "brand": row[2]
            }
        })
    
    # Add some category suggestions
    categories = ["Electronics", "Mobile Phones", "Laptops", "Cameras", "Audio"]
    for cat in categories:
        if q.lower() in cat.lower() and len(suggestions) < limit:
            suggestions.append({
                "text": cat,
                "score": 0.8,
                "suggestion_type": "category"
            })
    
    return {
        "query": q,
        "suggestions": suggestions,
        "total_count": len(suggestions),
        "response_time_ms": 50
    }

@app.post("/api/v1/track-click", summary="Track product click")
async def track_click(data: dict):
    """Track product click for analytics"""
    # In a real implementation, this would store the click data
    print(f"Click tracked: {data}")
    return {"success": True}

@app.get("/", summary="API root")
async def root():
    """API root endpoint"""
    return {
        "name": "Flipkart Search Direct API",
        "description": "Direct database access API for Flipkart product search",
        "endpoints": [
            "/api/v2/search?q=<query>",
            "/api/products/{product_id}",
            "/api/categories",
            "/api/v1/metadata/autosuggest?q=<query>",
            "/api/v1/track-click"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
