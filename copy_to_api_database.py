"""
Copy Product Data Script

This script copies products from search_system.db (where we added 5000 diverse products)
to the database format used by the API (flipkart_search.db)
"""

import sqlite3
import os
import time
import random
from pathlib import Path

def copy_products():
    """Copy products from search_system.db to flipkart_search.db"""
    print("=" * 80)
    print("🔄 COPYING PRODUCTS TO API DATABASE")
    print("=" * 80)
    
    # Check if source database exists
    if not os.path.exists('search_system.db'):
        print("❌ Source database 'search_system.db' not found")
        return False
    
    # Check if API database exists - create if not
    api_db_path = 'flipkart_search.db'
    
    # Connect to source database
    src_conn = sqlite3.connect('search_system.db')
    src_cursor = src_conn.cursor()
    
    # Connect to destination database
    dest_conn = sqlite3.connect(api_db_path)
    dest_cursor = dest_conn.cursor()
    
    # Check and create products table in destination if needed
    dest_cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        subcategory TEXT,
        brand TEXT,
        specifications TEXT,
        original_price REAL,
        current_price REAL NOT NULL,
        discount_percent REAL,
        savings REAL,
        rating REAL,
        num_ratings INTEGER DEFAULT 0,
        stock_quantity INTEGER DEFAULT 0,
        is_available INTEGER DEFAULT 1,
        seller_name TEXT,
        seller_rating REAL,
        seller_location TEXT,
        return_policy TEXT,
        exchange_available INTEGER DEFAULT 0,
        cod_available INTEGER DEFAULT 1,
        images TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP,
        views INTEGER DEFAULT 0,
        purchases INTEGER DEFAULT 0,
        is_featured INTEGER DEFAULT 0,
        is_bestseller INTEGER DEFAULT 0,
        delivery_days INTEGER,
        free_delivery INTEGER DEFAULT 0
    )
    """)
    dest_conn.commit()
    
    # Get count of products in source database
    src_cursor.execute("SELECT COUNT(*) FROM products")
    src_count = src_cursor.fetchone()[0]
    print(f"📊 Found {src_count} products in source database")
    
    # Get current count in destination database
    dest_cursor.execute("SELECT COUNT(*) FROM products")
    initial_dest_count = dest_cursor.fetchone()[0]
    print(f"📊 Initial count in API database: {initial_dest_count}")
    
    # Get products from source database
    src_cursor.execute("SELECT * FROM products")
    products = src_cursor.fetchall()
    
    # Get column names from source database
    src_cursor.execute("PRAGMA table_info(products)")
    src_columns = [col[1] for col in src_cursor.fetchall()]
    
    # Get column names from destination database
    dest_cursor.execute("PRAGMA table_info(products)")
    dest_columns = [col[1] for col in dest_cursor.fetchall()]
    
    # Start batch insertion
    batch_size = 100
    total_batches = (len(products) + batch_size - 1) // batch_size
    
    print(f"⏳ Starting batch insertion ({total_batches} batches)")
    start_time = time.time()
    
    total_inserted = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(products))
        batch_products = products[start_idx:end_idx]
        
        try:
            for product in batch_products:
                # Create a dictionary from source product
                product_dict = {src_columns[i]: product[i] for i in range(len(src_columns))}
                
                # Prepare data for insertion with additional required fields
                dest_data = {
                    'product_id': product_dict.get('product_id', f"PROD{random.randint(100000, 999999)}"),
                    'title': product_dict.get('title', 'Unknown Product'),
                    'description': product_dict.get('description', ''),
                    'category': product_dict.get('category', 'Uncategorized'),
                    'subcategory': product_dict.get('subcategory', ''),
                    'brand': product_dict.get('brand', 'Unknown'),
                    'specifications': '{}',
                    'original_price': product_dict.get('original_price', product_dict.get('current_price', 0)),
                    'current_price': product_dict.get('current_price', 0),
                    'discount_percent': product_dict.get('discount_percent', 0),
                    'savings': product_dict.get('original_price', 0) - product_dict.get('current_price', 0),
                    'rating': product_dict.get('rating', 0),
                    'num_ratings': product_dict.get('num_ratings', 0),
                    'stock_quantity': random.randint(5, 100),
                    'is_available': 1 if product_dict.get('is_available', True) else 0,
                    'seller_name': 'Flipkart Official',
                    'seller_rating': 4.5,
                    'seller_location': random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad']),
                    'return_policy': '30 days return policy',
                    'exchange_available': random.choice([0, 1]),
                    'cod_available': random.choice([0, 1]),
                    'images': 'https://placehold.co/600x400',
                    'tags': product_dict.get('category', '').lower(),
                    'views': random.randint(10, 1000),
                    'purchases': random.randint(0, 100),
                    'is_featured': 1 if random.random() < 0.1 else 0,
                    'is_bestseller': 1 if random.random() < 0.05 else 0,
                    'delivery_days': random.randint(1, 7),
                    'free_delivery': 1 if product_dict.get('current_price', 0) > 500 else 0
                }
                
                # Insert into destination database
                cols = ', '.join(list(dest_data.keys()))
                placeholders = ', '.join(['?'] * len(dest_data))
                values = list(dest_data.values())
                
                try:
                    dest_cursor.execute(
                        f"INSERT OR REPLACE INTO products ({cols}) VALUES ({placeholders})",
                        values
                    )
                    total_inserted += 1
                except sqlite3.IntegrityError:
                    # Skip duplicates
                    pass
            
            # Commit batch
            dest_conn.commit()
            
            # Progress update
            percent_complete = (batch_num + 1) / total_batches * 100
            elapsed_time = time.time() - start_time
            products_processed = end_idx
            print(f"⏳ Progress: {percent_complete:.1f}% - Processed {products_processed}/{len(products)} products ({elapsed_time:.1f}s elapsed)")
            
        except Exception as e:
            print(f"❌ Error adding batch {batch_num+1}/{total_batches}: {e}")
    
    # Get final count in destination database
    dest_cursor.execute("SELECT COUNT(*) FROM products")
    final_dest_count = dest_cursor.fetchone()[0]
    
    # Close connections
    src_conn.close()
    dest_conn.close()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Copied {total_inserted} products in {elapsed:.2f} seconds")
    print(f"📊 Final count in API database: {final_dest_count}")
    print(f"📊 New products added: {final_dest_count - initial_dest_count}")
    
    return True

if __name__ == "__main__":
    copy_products()
