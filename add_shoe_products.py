import sqlite3
import sys

# Sample shoe products to add to the database
SHOE_PRODUCTS = [
    {
        "product_id": "SHOE12345",
        "title": "Nike Air Max Running Shoes",
        "description": "Premium running shoes with air cushioning and breathable mesh upper",
        "category": "Footwear",
        "subcategory": "Sports Shoes",
        "brand": "Nike",
        "current_price": 6999.0,
        "original_price": 8999.0,
        "rating": 4.6,
        "num_ratings": 850,
        "is_available": True
    },
    {
        "product_id": "SHOE23456",
        "title": "Adidas Originals Casual Shoes",
        "description": "Classic design casual shoes with comfortable insole and durable outsole",
        "category": "Footwear",
        "subcategory": "Casual Shoes",
        "brand": "Adidas",
        "current_price": 4999.0,
        "original_price": 5999.0,
        "rating": 4.3,
        "num_ratings": 620,
        "is_available": True
    },
    {
        "product_id": "SHOE34567",
        "title": "Puma Urban Sneakers",
        "description": "Stylish urban sneakers for everyday wear with synthetic leather upper",
        "category": "Footwear",
        "subcategory": "Sneakers",
        "brand": "Puma",
        "current_price": 3499.0,
        "original_price": 4299.0,
        "rating": 4.1,
        "num_ratings": 450,
        "is_available": True
    },
    {
        "product_id": "SHOE45678",
        "title": "Bata Formal Leather Shoes",
        "description": "Premium leather formal shoes for professional settings",
        "category": "Footwear",
        "subcategory": "Formal Shoes",
        "brand": "Bata",
        "current_price": 2499.0,
        "original_price": 2999.0,
        "rating": 4.0,
        "num_ratings": 380,
        "is_available": True
    },
    {
        "product_id": "SHOE56789",
        "title": "Woodland Hiking Boots",
        "description": "Durable hiking boots with waterproof material and excellent grip",
        "category": "Footwear",
        "subcategory": "Boots",
        "brand": "Woodland",
        "current_price": 5499.0,
        "original_price": 6499.0,
        "rating": 4.5,
        "num_ratings": 320,
        "is_available": True
    }
]

def add_shoe_products():
    """Add shoe products to the database"""
    print("🔍 Adding shoe products to search_system.db...")
    
    # Connect to SQLite database
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    # Insert products
    for product in SHOE_PRODUCTS:
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
            print(f"✅ Added: {product['title']}")
        except Exception as e:
            print(f"❌ Error adding {product['product_id']}: {e}")
    
    # Commit changes and close connection
    conn.commit()
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"📊 Database now contains {count} total products")
    
    # Check shoe products
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Footwear'")
    shoe_count = cursor.fetchone()[0]
    print(f"👟 Database now contains {shoe_count} shoe products")
    
    # Close connection
    conn.close()
    print("✅ Shoe products added successfully")

if __name__ == "__main__":
    add_shoe_products()
