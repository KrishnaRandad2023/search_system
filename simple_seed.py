"""
Simplified Database Seeding Script
"""

import asyncio
import sys
import os
from pathlib import Path
import random
import sqlite3

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import Base, get_db_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Product data - sample data for testing
PRODUCTS = [
    {
        "product_id": "MOBF12345",
        "title": "Samsung Galaxy S21 Ultra 5G",
        "description": "Latest Samsung flagship with amazing camera and 5G capabilities",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Samsung",
        "current_price": 89999.0,
        "original_price": 105999.0,
        "rating": 4.7,
        "num_ratings": 1250,
        "is_available": True
    },
    {
        "product_id": "MOBF23456",
        "title": "iPhone 13 Pro Max",
        "description": "Apple's premium smartphone with ProMotion display and A15 Bionic chip",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Apple",
        "current_price": 129999.0,
        "original_price": 139999.0,
        "rating": 4.8,
        "num_ratings": 950,
        "is_available": True
    },
    {
        "product_id": "LAPF34567",
        "title": "HP Pavilion Gaming Laptop",
        "description": "15.6 inch gaming laptop with NVIDIA GTX 1650, 8GB RAM and 512GB SSD",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "HP",
        "current_price": 62999.0,
        "original_price": 75999.0,
        "rating": 4.2,
        "num_ratings": 850,
        "is_available": True
    },
    {
        "product_id": "LAPF45678",
        "title": "MacBook Air M1",
        "description": "Apple's lightweight laptop with incredible performance and battery life",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Apple",
        "current_price": 89990.0,
        "original_price": 99990.0,
        "rating": 4.9,
        "num_ratings": 1100,
        "is_available": True
    },
    {
        "product_id": "ACCF56789",
        "title": "Sony WH-1000XM4 Wireless Headphones",
        "description": "Industry-leading noise cancelling wireless headphones",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Sony",
        "current_price": 24990.0,
        "original_price": 29990.0,
        "rating": 4.6,
        "num_ratings": 750,
        "is_available": True
    }
]

async def seed_database():
    """Seed database with sample data using direct SQLite connection"""
    print("🗃️ Starting direct database seeding...")
    
    # Connect to SQLite database
    db_path = 'search_system.db'
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create products table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        subcategory TEXT,
        brand TEXT,
        current_price REAL NOT NULL,
        original_price REAL,
        rating REAL,
        num_ratings INTEGER DEFAULT 0,
        is_available INTEGER DEFAULT 1
    )
    ''')
    
    # Insert products
    print("📦 Inserting sample products...")
    for product in PRODUCTS:
        try:
            cursor.execute(
                '''
                INSERT OR REPLACE INTO products 
                (product_id, title, description, category, subcategory, brand, 
                current_price, original_price, rating, num_ratings, is_available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    product["product_id"],
                    product["title"],
                    product["description"],
                    product["category"],
                    product["subcategory"],
                    product["brand"],
                    product["current_price"],
                    product["original_price"],
                    product["rating"],
                    product["num_ratings"],
                    1 if product["is_available"] else 0
                )
            )
        except Exception as e:
            print(f"❌ Error inserting product {product['product_id']}: {e}")
    
    # Commit changes and close connection
    conn.commit()
    print(f"✅ Inserted {len(PRODUCTS)} sample products")
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"📊 Database now contains {count} products")
    
    # Close connection
    conn.close()
    print("✅ Database seeding completed successfully")

def main():
    """Main entry point"""
    asyncio.run(seed_database())

if __name__ == "__main__":
    main()
