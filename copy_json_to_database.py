"""
Copy JSON Products Script

This script copies products from data/raw/products.json to the database format 
used by the API (flipkart_search.db)
"""

import json
import os
import time
import random
import sqlite3
from pathlib import Path

def copy_json_products():
    """Copy products from JSON file to flipkart_search.db"""
    print("=" * 80)
    print("🔄 COPYING JSON PRODUCTS TO API DATABASE")
    print("=" * 80)
    
    # Check if source JSON exists
    json_path = os.path.join('data', 'raw', 'products.json')
    if not os.path.exists(json_path):
        print(f"❌ Source JSON file '{json_path}' not found")
        return False
    
    # Check if API database exists
    api_db_path = 'flipkart_search.db'
    
    # Load JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            products_json = json.load(f)
            
        print(f"📊 Loaded {len(products_json)} products from JSON file")
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return False
    
    # Connect to destination database
    dest_conn = sqlite3.connect(api_db_path)
    dest_cursor = dest_conn.cursor()
    
    # Check current product count
    dest_cursor.execute("SELECT COUNT(*) FROM products")
    initial_count = dest_cursor.fetchone()[0]
    print(f"📊 Initial count in API database: {initial_count}")
    
    # Check for existing product IDs to avoid duplicates
    dest_cursor.execute("SELECT product_id FROM products")
    existing_ids = {row[0] for row in dest_cursor.fetchall()}
    print(f"📊 Found {len(existing_ids)} existing product IDs")
    
    # Start batch insertion
    batch_size = 100
    total_products = len(products_json)
    total_batches = (total_products + batch_size - 1) // batch_size
    
    print(f"⏳ Starting batch insertion ({total_batches} batches)")
    start_time = time.time()
    
    total_inserted = 0
    total_skipped = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_products)
        batch_products = products_json[start_idx:end_idx]
        
        for json_product in batch_products:
            # Skip products that don't have required fields
            if 'title' not in json_product:
                total_skipped += 1
                continue
                
            # Generate a product ID if not present
            if 'product_id' not in json_product and 'id' not in json_product:
                product_id = f"JSON{random.randint(100000, 999999)}"
            else:
                product_id = json_product.get('product_id', str(json_product.get('id', '')))
                
            # Skip if product ID already exists
            if product_id in existing_ids:
                total_skipped += 1
                continue
                
            # Map JSON fields to database fields
            try:
                # Extract or set default values
                title = json_product.get('title', 'Unknown Product')
                description = json_product.get('description', '')
                category = json_product.get('category', 'Electronics')
                subcategory = json_product.get('subcategory', '')
                brand = json_product.get('brand', 'Unknown')
                
                # Handle price field
                if 'current_price' in json_product:
                    price = float(json_product.get('current_price', 0))
                elif 'price' in json_product:
                    price = float(json_product.get('price', 0))
                else:
                    price = 0.0
                    
                if isinstance(price, str):
                    # Remove currency symbols and commas
                    price = price.replace('₹', '').replace('$', '').replace(',', '')
                    price = float(price)
                
                # Calculate discounted price if available
                original_price = price
                if 'discount' in json_product:
                    discount = float(json_product['discount'])
                    current_price = price * (1 - discount/100)
                else:
                    current_price = price
                    discount = 0
                    
                # Insert into database
                dest_cursor.execute("""
                INSERT INTO products (
                    product_id, title, description, category, subcategory, brand,
                    specifications, original_price, current_price, discount_percent,
                    savings, rating, num_ratings, stock_quantity, is_available,
                    seller_name, seller_rating, seller_location, return_policy,
                    exchange_available, cod_available, images, tags, views, purchases,
                    is_featured, is_bestseller, delivery_days, free_delivery
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, title, description, category, subcategory, brand,
                    '{}', original_price, current_price, discount,
                    original_price - current_price, random.uniform(3.5, 5.0), random.randint(10, 1000), 
                    random.randint(5, 100), 1, 'Flipkart Seller', 4.5,
                    random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad']),
                    '30 days return policy', random.choice([0, 1]), 1,
                    json_product.get('image', 'https://placehold.co/600x400'),
                    category.lower(), random.randint(10, 1000), random.randint(0, 100),
                    1 if random.random() < 0.1 else 0, 1 if random.random() < 0.05 else 0,
                    random.randint(1, 7), 1 if current_price > 500 else 0
                ))
                
                # Add to existing IDs
                existing_ids.add(product_id)
                total_inserted += 1
            
            except Exception as e:
                print(f"❌ Error inserting product {json_product.get('title', 'Unknown')}: {e}")
                total_skipped += 1
        
        # Commit batch
        dest_conn.commit()
        
        # Progress update
        percent_complete = (batch_num + 1) / total_batches * 100
        elapsed_time = time.time() - start_time
        products_processed = end_idx
        print(f"⏳ Progress: {percent_complete:.1f}% - Processed {products_processed}/{total_products} products ({elapsed_time:.1f}s elapsed)")
    
    # Get final count in destination database
    dest_cursor.execute("SELECT COUNT(*) FROM products")
    final_count = dest_cursor.fetchone()[0]
    
    # Close connection
    dest_conn.close()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Added {total_inserted} new products in {elapsed:.2f} seconds")
    print(f"⚠️ Skipped {total_skipped} products (duplicates or invalid)")
    print(f"📊 Final count in API database: {final_count}")
    print(f"📊 New products added: {final_count - initial_count}")
    
    return True

if __name__ == "__main__":
    copy_json_products()
