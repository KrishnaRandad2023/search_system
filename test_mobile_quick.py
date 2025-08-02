#!/usr/bin/env python3
"""Quick test for mobile products"""

from sqlalchemy import create_engine, text

def test_mobile_products():
    engine = create_engine('sqlite:///flipkart_search.db')
    with engine.connect() as conn:
        # First check schema
        schema_result = conn.execute(text("PRAGMA table_info(products)"))
        columns = schema_result.fetchall()
        print("Database columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Test mobile products
        result = conn.execute(text("SELECT title, category, subcategory, current_price FROM products WHERE subcategory LIKE '%Mobile%' LIMIT 5"))
        rows = result.fetchall()
        print(f"\nFound {len(rows)} mobile products:")
        for row in rows:
            print(f"  - {row[0]} | {row[1]} | {row[2]} | ${row[3]}")
        
        # Test any phone-related products
        result2 = conn.execute(text("SELECT title, category, subcategory, current_price FROM products WHERE title LIKE '%phone%' OR title LIKE '%mobile%' OR title LIKE '%smartphone%' LIMIT 5"))
        rows2 = result2.fetchall()
        print(f"\nFound {len(rows2)} phone/mobile/smartphone in titles:")
        for row in rows2:
            print(f"  - {row[0]} | {row[1]} | {row[2]} | ${row[3]}")

if __name__ == "__main__":
    test_mobile_products()
