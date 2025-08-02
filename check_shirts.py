#!/usr/bin/env python3
"""Check shirt products in database"""

from sqlalchemy import create_engine, text

def check_shirt_products():
    engine = create_engine('sqlite:///flipkart_search.db')
    with engine.connect() as conn:
        # Check products containing "shirt"
        result = conn.execute(text("SELECT title, category, subcategory FROM products WHERE title LIKE '%shirt%' LIMIT 10"))
        rows = result.fetchall()
        print(f"Found {len(rows)} products containing 'shirt':")
        for row in rows:
            print(f"  - {row[0]} | {row[1]} | {row[2]}")
        
        # Check for exact matches
        result2 = conn.execute(text("SELECT title FROM products WHERE title LIKE '%shirts%' LIMIT 5"))
        rows2 = result2.fetchall()
        print(f"\nFound {len(rows2)} products containing 'shirts' (plural):")
        for row in rows2:
            print(f"  - {row[0]}")
        
        # Check for T-shirts specifically
        result3 = conn.execute(text("SELECT title FROM products WHERE title LIKE '%T-shirts%' LIMIT 5"))
        rows3 = result3.fetchall()
        print(f"\nFound {len(rows3)} products containing 'T-shirts' (with T):")
        for row in rows3:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    check_shirt_products()
