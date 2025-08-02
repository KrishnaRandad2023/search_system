#!/usr/bin/env python3
"""Check jeans products in database"""

from sqlalchemy import create_engine, text

def check_jeans_products():
    engine = create_engine('sqlite:///flipkart_search.db')
    with engine.connect() as conn:
        # Check products containing "jean"
        result = conn.execute(text("SELECT title FROM products WHERE title LIKE '%jean%' LIMIT 10"))
        rows = result.fetchall()
        print(f"Found {len(rows)} products containing 'jean':")
        for row in rows:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    check_jeans_products()
