"""
Load all existing data into the database for full system functionality
"""

import json
import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def create_full_database():
    """Create database with all existing data"""
    
    db_path = Path("data/flipkart_products.db")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables to refresh with full data
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS product_features")
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute("DROP TABLE IF EXISTS queries")
    
    # Create products table with all fields from JSON
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        subcategory TEXT,
        brand TEXT,
        specifications TEXT,
        original_price REAL,
        current_price REAL,
        discount_percent REAL,
        savings REAL,
        rating REAL,
        num_ratings INTEGER,
        stock_quantity INTEGER,
        is_available INTEGER,
        seller_name TEXT,
        seller_rating REAL,
        seller_location TEXT,
        return_policy TEXT,
        exchange_available INTEGER,
        cod_available INTEGER,
        images TEXT,
        tags TEXT,
        created_at TIMESTAMP,
        last_updated TIMESTAMP,
        views INTEGER,
        purchases INTEGER,
        is_featured INTEGER,
        is_bestseller INTEGER,
        delivery_days INTEGER,
        free_delivery INTEGER
    )
    ''')
    
    # Create reviews table
    cursor.execute('''
    CREATE TABLE reviews (
        review_id TEXT PRIMARY KEY,
        product_id TEXT,
        user_id TEXT,
        rating REAL,
        review_text TEXT,
        helpful_votes INTEGER,
        verified_purchase INTEGER,
        review_date TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')
    
    # Create queries table
    cursor.execute('''
    CREATE TABLE queries (
        query_id TEXT PRIMARY KEY,
        query_text TEXT,
        popularity INTEGER,
        created_at TIMESTAMP
    )
    ''')
    
    # Create autosuggest table
    cursor.execute('''
    CREATE TABLE autosuggest_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        popularity INTEGER,
        category TEXT
    )
    ''')
    
    conn.commit()
    print("✅ Database tables created")
    
    # Load products from JSON (main dataset - 12,000 products)
    print("Loading products from JSON...")
    try:
        with open("data/raw/products.json", 'r', encoding='utf-8') as f:
            products_json = json.load(f)
        
        for product in products_json:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO products (
                    product_id, title, description, category, subcategory, brand,
                    specifications, original_price, current_price, discount_percent,
                    savings, rating, num_ratings, stock_quantity, is_available,
                    seller_name, seller_rating, seller_location, return_policy,
                    exchange_available, cod_available, images, tags, created_at,
                    last_updated, views, purchases, is_featured, is_bestseller,
                    delivery_days, free_delivery
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.get('product_id'),
                    product.get('title'),
                    product.get('description'),
                    product.get('category'),
                    product.get('subcategory'),
                    product.get('brand'),
                    json.dumps(product.get('specifications', {})) if product.get('specifications') else None,
                    product.get('original_price'),
                    product.get('current_price'),
                    product.get('discount_percent'),
                    product.get('savings'),
                    product.get('rating'),
                    product.get('num_ratings'),
                    product.get('stock_quantity'),
                    1 if product.get('is_available') else 0,
                    product.get('seller_name'),
                    product.get('seller_rating'),
                    product.get('seller_location'),
                    product.get('return_policy'),
                    1 if product.get('exchange_available') else 0,
                    1 if product.get('cod_available') else 0,
                    json.dumps(product.get('images', [])) if product.get('images') else None,
                    json.dumps(product.get('tags', [])) if product.get('tags') else None,
                    product.get('created_at'),
                    product.get('last_updated'),
                    product.get('views', 0),
                    product.get('purchases', 0),
                    1 if product.get('is_featured') else 0,
                    1 if product.get('is_bestseller') else 0,
                    product.get('delivery_days'),
                    1 if product.get('free_delivery') else 0
                ))
            except Exception as e:
                print(f"Error inserting product {product.get('product_id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Loaded {len(products_json)} products from JSON")
        
    except Exception as e:
        print(f"❌ Error loading products from JSON: {e}")
    
    # Load reviews
    print("Loading reviews...")
    try:
        reviews_df = pd.read_csv("data/raw/flipkart_reviews.csv")
        
        for _, review in reviews_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO reviews (
                review_id, product_id, user_id, rating, review_text,
                helpful_votes, verified_purchase, review_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review.get('review_id'),
                review.get('product_id'),
                review.get('user_id'),
                review.get('rating'),
                review.get('review_text'),
                review.get('helpful_votes', 0),
                1 if review.get('verified_purchase') else 0,
                review.get('review_date')
            ))
        
        print(f"✅ Loaded {len(reviews_df)} reviews")
        
    except Exception as e:
        print(f"❌ Error loading reviews: {e}")
    
    # Load queries
    print("Loading queries...")
    try:
        with open("data/raw/queries.json", 'r', encoding='utf-8') as f:
            queries_json = json.load(f)
        
        for query in queries_json:
            cursor.execute('''
            INSERT OR REPLACE INTO queries (query_id, query_text, popularity, created_at)
            VALUES (?, ?, ?, ?)
            ''', (
                query.get('query_id'),
                query.get('query_text'),
                query.get('popularity'),
                query.get('created_at')
            ))
        
        print(f"✅ Loaded {len(queries_json)} queries")
        
    except Exception as e:
        print(f"❌ Error loading queries: {e}")
    
    # Load autosuggest queries
    print("Loading autosuggest queries...")
    try:
        autosuggest_df = pd.read_csv("data/raw/autosuggest_queries.csv")
        
        for _, query in autosuggest_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO autosuggest_queries (query, popularity, category)
            VALUES (?, ?, ?)
            ''', (
                query.get('query'),
                query.get('popularity'),
                query.get('category')
            ))
        
        print(f"✅ Loaded {len(autosuggest_df)} autosuggest queries")
        
    except Exception as e:
        print(f"❌ Error loading autosuggest queries: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Database fully loaded with all existing data!")
    print(f"Database size: {db_path.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    create_full_database()
