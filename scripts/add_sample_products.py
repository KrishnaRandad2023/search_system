"""
Quick script to add sample products for frontend testing
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

def add_sample_products():
    """Add sample products to the database"""
    
    # Setup database connection
    db_path = Path(__file__).parent.parent / "data" / "flipkart_products.db"
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        subcategory TEXT,
        brand TEXT,
        price REAL,
        original_price REAL,
        discount_percentage REAL,
        rating REAL,
        num_ratings INTEGER,
        num_reviews INTEGER,
        stock INTEGER,
        is_active INTEGER,
        is_bestseller INTEGER,
        is_new_arrival INTEGER,
        image_url TEXT
    )
    ''')
    conn.commit()
    
    # Sample products data
    sample_products = [
        {
            "product_id": "HP-LAPTOP-001",
            "title": "HP Pavilion 15 Gaming Laptop",
            "description": "HP Pavilion Gaming Laptop with Intel Core i5, 8GB RAM, 512GB SSD, NVIDIA GTX 1650",
            "category": "Electronics",
            "subcategory": "Laptops",
            "brand": "HP",
            "price": 65999.0,
            "original_price": 79999.0,
            "discount_percentage": 17.5,
            "rating": 4.3,
            "num_ratings": 1247,
            "num_reviews": 432,
            "stock": 15,
            "is_active": True,
            "is_bestseller": True,
            "is_new_arrival": False,
            "image_url": "https://example.com/hp-pavilion.jpg"
        },
        {
            "product_id": "DELL-LAPTOP-001",
            "title": "Dell Inspiron 15 3000 Laptop",
            "description": "Dell Inspiron 15 with AMD Ryzen 5, 8GB RAM, 256GB SSD, Windows 11",
            "category": "Electronics",
            "subcategory": "Laptops", 
            "brand": "Dell",
            "price": 45999.0,
            "original_price": 52999.0,
            "discount_percentage": 13.2,
            "rating": 4.1,
            "num_ratings": 892,
            "num_reviews": 234,
            "stock": 8,
            "is_active": True,
            "is_bestseller": False,
            "is_new_arrival": True,
            "image_url": "https://example.com/dell-inspiron.jpg"
        },
        {
            "product_id": "APPLE-LAPTOP-001",
            "title": "MacBook Air M2 13-inch",
            "description": "Apple MacBook Air with M2 chip, 8GB unified memory, 256GB SSD storage",
            "category": "Electronics",
            "subcategory": "Laptops",
            "brand": "Apple",
            "price": 114900.0,
            "original_price": 119900.0,
            "discount_percentage": 4.2,
            "rating": 4.8,
            "num_ratings": 2341,
            "num_reviews": 892,
            "stock": 5,
            "is_active": True,
            "is_bestseller": True,
            "is_new_arrival": False,
            "image_url": "https://example.com/macbook-air-m2.jpg"
        },
        {
            "product_id": "SAMSUNG-PHONE-001",
            "title": "Samsung Galaxy S24 5G",
            "description": "Samsung Galaxy S24 with 256GB storage, 12GB RAM, Triple camera setup",
            "category": "Electronics",
            "subcategory": "Smartphones",
            "brand": "Samsung",
            "price": 74999.0,
            "original_price": 79999.0,
            "discount_percentage": 6.3,
            "rating": 4.5,
            "num_ratings": 1876,
            "num_reviews": 654,
            "stock": 12,
            "is_active": True,
            "is_bestseller": True,
            "is_new_arrival": True,
            "image_url": "https://example.com/galaxy-s24.jpg"
        },
        {
            "product_id": "IPHONE-001",
            "title": "iPhone 15 Pro Max 256GB",
            "description": "Apple iPhone 15 Pro Max with A17 Pro chip, 256GB storage, Pro camera system",
            "category": "Electronics",
            "subcategory": "Smartphones",
            "brand": "Apple",
            "price": 159900.0,
            "original_price": 159900.0,
            "discount_percentage": 0.0,
            "rating": 4.7,
            "num_ratings": 3245,
            "num_reviews": 1234,
            "stock": 3,
            "is_active": True,
            "is_bestseller": True,
            "is_new_arrival": False,
            "image_url": "https://example.com/iphone-15-pro-max.jpg"
        },
        {
            "product_id": "HEADPHONES-001",
            "title": "Sony WH-1000XM5 Headphones",
            "description": "Sony WH-1000XM5 Wireless Noise Canceling Headphones with 30-hour battery",
            "category": "Electronics",
            "subcategory": "Audio",
            "brand": "Sony",
            "price": 29990.0,
            "original_price": 34990.0,
            "discount_percentage": 14.3,
            "rating": 4.6,
            "num_ratings": 987,
            "num_reviews": 456,
            "stock": 20,
            "is_active": True,
            "is_bestseller": False,
            "is_new_arrival": False,
            "image_url": "https://example.com/sony-wh1000xm5.jpg"
        }
    ]
    
    # Connect to database - use the one we created at the beginning
    for product in sample_products:
        cursor.execute('''
            INSERT OR REPLACE INTO products (
                product_id, title, description, category, subcategory, brand,
                price, original_price, discount_percentage, rating, num_ratings, num_reviews,
                stock, is_active, is_bestseller, is_new_arrival, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product["product_id"], product["title"], product["description"],
            product["category"], product["subcategory"], product["brand"],
            product["price"], product["original_price"], product["discount_percentage"],
            product["rating"], product["num_ratings"], product["num_reviews"],
            product["stock"], 
            1 if product["is_active"] else 0, 
            1 if product["is_bestseller"] else 0,
            1 if product["is_new_arrival"] else 0, 
            product["image_url"]
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Added {len(sample_products)} sample products to the database!")
    
    # Print summary
    print("\n📦 Sample Products Added:")
    for product in sample_products:
        print(f"  - {product['title']} (₹{product['price']:,.0f})")

if __name__ == "__main__":
    add_sample_products()
