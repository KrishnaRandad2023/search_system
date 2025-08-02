"""
Fix schema mismatches in the API database to ensure consistent searches
"""

import sqlite3

def fix_database_schema():
    """Fix inconsistencies in database schema for better search results"""
    
    print("🔧 FIXING DATABASE SCHEMA")
    print("=" * 80)
    
    # Connect to the database
    conn = sqlite3.connect('flipkart_search.db')
    cursor = conn.cursor()
    
    # Get current schema
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("Current columns in products table:")
    for col in column_names:
        print(f"  - {col}")
    
    # Check and fix price columns
    if "price" in column_names and "current_price" in column_names:
        # Ensure current_price has values if price has values
        cursor.execute("""
        UPDATE products
        SET current_price = price
        WHERE current_price IS NULL OR current_price = 0
        """)
        print("✅ Updated current_price from price column where needed")
    
    # Check and fix stock columns
    if "stock" in column_names and "stock_quantity" in column_names:
        # Ensure stock_quantity has values if stock has values
        cursor.execute("""
        UPDATE products
        SET stock_quantity = stock
        WHERE stock_quantity IS NULL OR stock_quantity = 0
        """)
        print("✅ Updated stock_quantity from stock column where needed")
    
    # Ensure all footwear products have proper categorization
    cursor.execute("""
    UPDATE products
    SET category = 'Footwear'
    WHERE subcategory IN ('Sneakers', 'Loafers', 'Boots', 'Running Shoes', 'Casual Shoes', 'Formal Shoes', 'Flip-Flops')
    AND category != 'Footwear'
    """)
    print("✅ Updated category to 'Footwear' for footwear subcategories")
    
    # Create appropriate indexes for search optimization
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_title ON products(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)")
        print("✅ Created search optimization indexes")
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")
    
    # Create a triggers to update search_text field (if it exists)
    if "search_text" in column_names:
        try:
            # First add search_text column if it's somehow missing from some rows
            cursor.execute("""
            UPDATE products
            SET search_text = title || ' ' || COALESCE(description, '') || ' ' || COALESCE(brand, '') || ' ' || COALESCE(category, '') || ' ' || COALESCE(subcategory, '')
            WHERE search_text IS NULL
            """)
            
            # Create trigger for future updates
            cursor.execute("DROP TRIGGER IF EXISTS update_search_text")
            cursor.execute("""
            CREATE TRIGGER update_search_text 
            AFTER UPDATE ON products
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET search_text = NEW.title || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.brand, '') || ' ' || COALESCE(NEW.category, '') || ' ' || COALESCE(NEW.subcategory, '')
                WHERE product_id = NEW.product_id;
            END;
            """)
            print("✅ Created search_text update trigger")
        except Exception as e:
            print(f"⚠️ Error creating trigger: {e}")
    
    # Commit changes and close
    conn.commit()
    
    # Get updated footwear counts
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Footwear'")
    footwear_count = cursor.fetchone()[0]
    
    cursor.execute("""
    SELECT COUNT(*) FROM products 
    WHERE category = 'Footwear' OR subcategory LIKE '%shoe%' OR title LIKE '%shoe%'
    """)
    all_footwear_count = cursor.fetchone()[0]
    
    print(f"\n📊 Footwear Category Products: {footwear_count}")
    print(f"📊 All Footwear-related Products: {all_footwear_count}")
    
    conn.close()
    print("\n✅ Database schema fixed successfully")

if __name__ == "__main__":
    fix_database_schema()
