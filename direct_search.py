"""
Simple search script using direct database access
"""

import sqlite3
import json
from pathlib import Path


def search_products(query, limit=10):
    """Search products in the database directly"""
    conn = sqlite3.connect('./flipkart_search.db')
    cursor = conn.cursor()
    
    search_terms = query.split()
    like_conditions = []
    params = []
    
    for term in search_terms:
        like_term = f"%{term}%"
        like_conditions.append("(title LIKE ? OR description LIKE ? OR category LIKE ? OR brand LIKE ?)")
        params.extend([like_term, like_term, like_term, like_term])
    
    where_clause = " AND ".join(like_conditions)
    
    cursor.execute(f"""
    SELECT id, product_id, title, description, category, brand, current_price, rating
    FROM products 
    WHERE {where_clause}
    LIMIT ?
    """, params + [limit])
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "product_id": row[1],
            "title": row[2],
            "description": row[3],
            "category": row[4],
            "brand": row[5],
            "price": row[6],  # Using current_price as price
            "rating": row[7]
        })
    
    conn.close()
    return results


if __name__ == "__main__":
    query = input("Enter search query: ")
    products = search_products(query)
    print(f"Found {len(products)} results for '{query}':")
    
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product['title']}")
        print(f"   Brand: {product['brand']} | Category: {product['category']}")
        print(f"   Price: ₹{product['price']} | Rating: {product['rating']}")
