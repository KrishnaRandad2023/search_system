"""
Direct Database Search Service - Bypass SQLAlchemy issues
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DirectSearchService:
    """Direct database search service bypassing SQLAlchemy"""
    
    def __init__(self, db_path: str = "flipkart_search.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def search_products(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: bool = False
    ) -> Dict[str, Any]:
        """Search products directly in database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build the query
            base_query = """
                SELECT id, product_id, title, description, category, subcategory, brand,
                       current_price, original_price, discount_percent, rating, num_ratings,
                       stock_quantity, is_available, is_bestseller, is_featured, images
                FROM products 
                WHERE is_available = 1
            """
            
            params = []
            
            # Add stock filter
            if in_stock:
                base_query += " AND stock_quantity > 0"
            
            # Add text search
            if query.strip():
                query_lower = query.lower().strip()
                base_query += """
                    AND (
                        lower(title) LIKE ? OR 
                        lower(description) LIKE ? OR 
                        lower(brand) LIKE ? OR 
                        lower(category) LIKE ? OR 
                        lower(subcategory) LIKE ?
                    )
                """
                search_term = f"%{query_lower}%"
                params.extend([search_term] * 5)
            
            # Add category filter
            if category:
                base_query += " AND lower(category) LIKE lower(?)"
                params.append(f"%{category}%")
            
            # Add rating filter
            if min_rating:
                base_query += " AND rating >= ?"
                params.append(min_rating)
            
            # Add price filter
            if max_price:
                base_query += " AND current_price <= ?"
                params.append(max_price)
            
            # Add sorting
            base_query += """
                ORDER BY is_bestseller DESC, is_featured DESC, 
                         rating DESC, num_ratings DESC
            """
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS counted"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Add pagination
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Execute main query
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [
                'id', 'product_id', 'title', 'description', 'category', 'subcategory', 
                'brand', 'current_price', 'original_price', 'discount_percent', 
                'rating', 'num_ratings', 'stock_quantity', 'is_available', 
                'is_bestseller', 'is_featured', 'images'
            ]
            
            products = []
            for row in results:
                product = dict(zip(columns, row))
                products.append(product)
            
            conn.close()
            
            return {
                "products": products,
                "total_count": total_count,
                "page_size": limit,
                "offset": offset,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Direct search error: {e}")
            raise e

# Global instance
_search_service = None

def get_direct_search_service() -> DirectSearchService:
    """Get the global direct search service instance"""
    global _search_service
    if _search_service is None:
        _search_service = DirectSearchService()
    return _search_service
