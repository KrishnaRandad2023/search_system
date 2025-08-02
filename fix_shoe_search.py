"""
Fix for search API to ensure "shoes" and related queries work properly
"""

import sqlite3
import json

def fix_search_mappings():
    """
    Add missing mappings for shoes and related terms in the search_mappings table
    This ensures that searches for "shoes" properly find footwear products
    """
    
    print("🔧 ADDING SHOE SEARCH MAPPINGS")
    print("=" * 80)
    
    # Connect to the database
    conn = sqlite3.connect('flipkart_search.db')
    cursor = conn.cursor()
    
    # Check if search_mappings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_mappings'")
    if not cursor.fetchone():
        # Create the search_mappings table if it doesn't exist
        cursor.execute("""
        CREATE TABLE search_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Created search_mappings table")
    
    # Define shoe-related mappings to add
    shoe_mappings = [
        ("shoes", "Footwear", None, "shoes,footwear,casual,formal,running"),
        ("shoe", "Footwear", None, "shoes,footwear,casual,formal,running"),
        ("sneakers", "Footwear", "Sneakers", "shoes,footwear,casual,sports"),
        ("loafers", "Footwear", "Loafers", "shoes,footwear,casual,formal"),
        ("boots", "Footwear", "Boots", "shoes,footwear,casual,formal"),
        ("running shoes", "Footwear", "Running Shoes", "shoes,footwear,sports,athletic"),
        ("casual shoes", "Footwear", "Casual Shoes", "shoes,footwear,casual"),
        ("formal shoes", "Footwear", "Formal Shoes", "shoes,footwear,formal,office"),
        ("sports shoes", "Footwear", "Running Shoes", "shoes,footwear,sports,athletic"),
        ("flip flops", "Footwear", "Flip-Flops", "shoes,footwear,casual,summer"),
    ]
    
    # Check and add mappings
    for mapping in shoe_mappings:
        search_term, category, subcategory, tags = mapping
        
        # Check if the mapping already exists
        cursor.execute("SELECT id FROM search_mappings WHERE search_term = ?", (search_term,))
        if cursor.fetchone():
            print(f"ℹ️ Mapping for '{search_term}' already exists, updating...")
            cursor.execute("""
            UPDATE search_mappings 
            SET category = ?, subcategory = ?, tags = ? 
            WHERE search_term = ?
            """, (category, subcategory, tags, search_term))
        else:
            # Add new mapping
            cursor.execute("""
            INSERT INTO search_mappings (search_term, category, subcategory, tags)
            VALUES (?, ?, ?, ?)
            """, (search_term, category, subcategory, tags))
            print(f"✅ Added mapping for '{search_term}'")
    
    # Add additional mapping to semantic synonyms for more precise matching
    try:
        # Check if the semantic_synonyms table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_synonyms'")
        if not cursor.fetchone():
            # Create the semantic_synonyms table if it doesn't exist
            cursor.execute("""
            CREATE TABLE semantic_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                synonyms TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("✅ Created semantic_synonyms table")
        
        # Define shoe synonyms
        shoe_synonyms = {
            "shoes": json.dumps(["footwear", "sneakers", "loafers", "boots", "casual shoes", "formal shoes"]),
            "footwear": json.dumps(["shoes", "sneakers", "loafers", "boots", "sandals", "flip flops"]),
            "sneakers": json.dumps(["shoes", "casual shoes", "sports shoes", "athletic shoes", "running shoes"]),
            "loafers": json.dumps(["shoes", "casual shoes", "slip-ons", "formal shoes", "men's shoes"]),
            "boots": json.dumps(["shoes", "footwear", "winter boots", "leather boots", "ankle boots"]),
        }
        
        # Add or update synonyms
        for term, synonyms in shoe_synonyms.items():
            cursor.execute("SELECT id FROM semantic_synonyms WHERE term = ?", (term,))
            if cursor.fetchone():
                cursor.execute("UPDATE semantic_synonyms SET synonyms = ? WHERE term = ?", (synonyms, term))
                print(f"ℹ️ Updated synonyms for '{term}'")
            else:
                cursor.execute("INSERT INTO semantic_synonyms (term, synonyms) VALUES (?, ?)", (term, synonyms))
                print(f"✅ Added synonyms for '{term}'")
    
    except Exception as e:
        print(f"⚠️ Error updating semantic synonyms: {e}")
    
    # Add an explicit search rule to ensure "shoe" matches properly
    try:
        # Check if the search_rules table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_rules'")
        if not cursor.fetchone():
            # Create the search_rules table if it doesn't exist
            cursor.execute("""
            CREATE TABLE search_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                pattern TEXT NOT NULL, 
                replacement TEXT,
                priority INTEGER DEFAULT 10,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("✅ Created search_rules table")
        
        # Add rule for shoe-related searches
        cursor.execute("""
        INSERT INTO search_rules (rule_type, pattern, replacement, priority, active)
        VALUES (?, ?, ?, ?, ?)
        """, ('rewrite', 'shoe', 'shoe OR footwear', 100, 1))
        print("✅ Added explicit search rule for 'shoe'")
    
    except Exception as e:
        print(f"⚠️ Error adding search rule: {e}")
    
    # Create a view for footwear products if it doesn't exist
    try:
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS footwear_products AS
        SELECT * FROM products 
        WHERE category LIKE '%footwear%' 
           OR subcategory LIKE '%shoe%' 
           OR title LIKE '%shoe%' 
           OR description LIKE '%footwear%'
        """)
        print("✅ Created footwear_products view")
    except Exception as e:
        print(f"⚠️ Error creating view: {e}")
    
    # Update footwear records to ensure they are tagged properly
    cursor.execute("""
    UPDATE products
    SET tags = CASE 
        WHEN tags IS NULL THEN 'shoes,footwear'
        WHEN tags NOT LIKE '%shoes%' THEN tags || ',shoes,footwear'
        ELSE tags
    END
    WHERE category = 'Footwear' OR subcategory LIKE '%shoe%'
    """)
    print("✅ Updated footwear product tags")
    
    # Commit changes and close
    conn.commit()
    
    # Count the number of footwear products
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Footwear'")
    footwear_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE subcategory LIKE '%shoe%'")
    shoe_subcategory_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE title LIKE '%shoe%'")
    shoe_title_count = cursor.fetchone()[0]
    
    print(f"\n📊 Footwear Category Products: {footwear_count}")
    print(f"📊 Shoe Subcategory Products: {shoe_subcategory_count}")
    print(f"📊 Shoe in Title Products: {shoe_title_count}")
    
    conn.close()
    print("\n✅ Shoe search mappings added successfully")

if __name__ == "__main__":
    fix_search_mappings()
