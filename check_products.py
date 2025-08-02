import json
import os

def check_for_products(search_term):
    """Check if products.json contains items matching the search term"""
    file_path = 'data/raw/products.json'
    
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        matching_products = [
            p for p in data 
            if search_term in p.get('title', '').lower() 
            or search_term in p.get('description', '').lower()
            or search_term in p.get('category', '').lower()
        ]
        
        print(f"Found {len(matching_products)} products matching '{search_term}' in {file_path}")
        
        if matching_products:
            print("\nSample matching products:")
            for i, product in enumerate(matching_products[:3], 1):
                print(f"{i}. {product.get('title', 'No title')} - {product.get('category', 'No category')}")
                
    except Exception as e:
        print(f"Error: {e}")

def check_database_products(search_term, db_path='search_system.db'):
    """Check if database contains items matching the search term"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print(f"Table 'products' does not exist in {db_path}")
            return
        
        # Search for matching products
        cursor.execute(f"SELECT product_id, title, category FROM products WHERE title LIKE '%{search_term}%' OR description LIKE '%{search_term}%' OR category LIKE '%{search_term}%'")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} products matching '{search_term}' in {db_path}")
        
        if rows:
            print("\nSample matching products from database:")
            for i, row in enumerate(rows[:3], 1):
                print(f"{i}. {row[1]} - ID: {row[0]}, Category: {row[2]}")
                
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

# Check both sources for shoes
print("=" * 60)
print("CHECKING FOR 'shoes' IN PRODUCT DATA")
print("=" * 60)
check_for_products('shoe')
print("\n")
check_database_products('shoe')
print("\n")
check_database_products('shoe', 'flipkart_search.db')

# Also check for electronics (which worked in previous test)
print("\n")
print("=" * 60)
print("CHECKING FOR 'laptop' IN PRODUCT DATA (CONTROL TEST)")
print("=" * 60)
check_for_products('laptop')
print("\n")
check_database_products('laptop')
print("\n")
check_database_products('laptop', 'flipkart_search.db')
