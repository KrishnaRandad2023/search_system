"""
Check shoe products in the API database (flipkart_search.db)
"""

import sqlite3
import json
import os

def check_shoe_products(db_path='flipkart_search.db'):
    """Check specifically for shoe products in the database"""
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print(f"❌ Table 'products' does not exist in {db_path}")
            return
            
        # Check categories in the database
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = cursor.fetchall()
        print(f"📊 Categories in {db_path}:")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category[0]}")
            
        # Search for shoe products
        cursor.execute("""
            SELECT product_id, title, category, subcategory 
            FROM products 
            WHERE title LIKE '%shoe%' 
               OR category LIKE '%footwear%' 
               OR subcategory LIKE '%shoe%'
            LIMIT 10
        """)
        shoe_products = cursor.fetchall()
        
        print(f"\n🔍 Found {len(shoe_products)} shoe products in {db_path}")
        
        if shoe_products:
            print("\nSample shoe products:")
            for i, product in enumerate(shoe_products, 1):
                print(f"  {i}. {product[1]} - ID: {product[0]}, Category: {product[2]}, Subcategory: {product[3]}")
                
        # Also check for column values that seem odd or missing
        cursor.execute("""
            SELECT COUNT(*) 
            FROM products 
            WHERE current_price = 0 OR current_price IS NULL
        """)
        zero_price_count = cursor.fetchone()[0]
        print(f"\n⚠️ Products with zero/null price: {zero_price_count}")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total product count: {total_count}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
if __name__ == "__main__":
    print("=" * 80)
    print("🔍 CHECKING SHOE PRODUCTS IN API DATABASE")
    print("=" * 80)
    check_shoe_products()
