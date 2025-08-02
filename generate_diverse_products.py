"""
Diverse Product Generator for Flipkart Search System

This script generates 5000 diverse products across multiple categories
and adds them to the search_system.db database.
"""

import sqlite3
import random
import time
import os
from datetime import datetime, timedelta

# Constants for product generation
CATEGORIES = {
    "Electronics": ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras", "Smartwatches", 
                    "Gaming Consoles", "Televisions", "Audio Systems", "Computer Accessories"],
    "Clothing": ["T-shirts", "Jeans", "Formal Wear", "Casual Wear", "Ethnic Wear", 
                 "Sportswear", "Innerwear", "Winter Wear", "Accessories", "Kids Wear"],
    "Footwear": ["Sports Shoes", "Casual Shoes", "Formal Shoes", "Boots", "Sandals", 
                 "Flip-Flops", "Loafers", "Running Shoes", "Sneakers", "Ethnic Footwear"],
    "Home & Kitchen": ["Furniture", "Kitchen Appliances", "Home Decor", "Bedding", "Cookware", 
                       "Storage & Organization", "Bath", "Cleaning Supplies", "Dinnerware", "Lighting"],
    "Beauty & Personal Care": ["Skincare", "Haircare", "Makeup", "Fragrances", "Bath & Body", 
                              "Men's Grooming", "Beauty Tools", "Oral Care", "Personal Hygiene", "Wellness"],
    "Books & Stationery": ["Fiction", "Non-fiction", "Academic", "Children's Books", "Self-Help", 
                         "Notebooks", "Writing Instruments", "Art Supplies", "Office Supplies", "Calendars"],
    "Sports & Fitness": ["Exercise Equipment", "Sports Gear", "Outdoor Recreation", "Yoga & Pilates", 
                       "Team Sports", "Fitness Trackers", "Athletic Clothing", "Nutritional Supplements", "Camping", "Cycling"],
    "Toys & Baby": ["Action Figures", "Dolls", "Educational Toys", "Games", "Remote Control Toys", 
                  "Baby Care", "Diapers", "Baby Clothing", "Baby Furniture", "Baby Transport"],
    "Grocery": ["Packaged Food", "Beverages", "Snacks", "Dairy", "Breakfast", 
               "Canned & Jarred Food", "Condiments & Sauces", "Baking", "Health Foods", "Gourmet"],
    "Appliances": ["Refrigerators", "Washing Machines", "Air Conditioners", "Microwaves", "Vacuum Cleaners", 
                  "Water Purifiers", "Dishwashers", "Fans", "Air Purifiers", "Geysers"]
}

BRANDS = {
    "Electronics": ["Samsung", "Apple", "Sony", "LG", "Xiaomi", "OnePlus", "Dell", "HP", "Lenovo", "Asus", 
                   "Bose", "JBL", "Canon", "Nikon", "Google", "Acer", "Huawei", "Microsoft", "Bosch", "Realme"],
    "Clothing": ["Levi's", "Zara", "H&M", "Nike", "Adidas", "Puma", "Allen Solly", "Louis Philippe", "Van Heusen", "Arrow", 
                "Tommy Hilfiger", "Calvin Klein", "Gap", "Raymond", "Peter England", "W", "Biba", "Forever 21", "UCB", "Wrangler"],
    "Footwear": ["Nike", "Adidas", "Puma", "Reebok", "Woodland", "Bata", "Clarks", "Skechers", "Lee Cooper", "Crocs", 
                "New Balance", "Asics", "Red Tape", "Hush Puppies", "Fila", "Metro", "Liberty", "Mochi", "Under Armour", "Converse"],
    "Home & Kitchen": ["Ikea", "HomeTown", "Prestige", "Cello", "Borosil", "Milton", "Bombay Dyeing", "Spaces", "FabIndia", "UMA", 
                      "Hawkins", "Pigeon", "Corelle", "Tupperware", "Wonderchef", "Hindware", "Urban Ladder", "Philips", "Bajaj", "Morphy Richards"],
    "Beauty & Personal Care": ["Lakme", "Maybelline", "MAC", "L'Oréal", "Himalaya", "Nivea", "Dove", "Biotique", "Garnier", "Revlon", 
                              "Forest Essentials", "VLCC", "The Body Shop", "Kiehl's", "Bath & Body Works", "Kama Ayurveda", "Gillette", "Pears", "Neutrogena", "Vaseline"],
    "Books & Stationery": ["Penguin", "HarperCollins", "Rupa", "Westland", "Oxford", "Camlin", "Reynolds", "Classmate", "Parker", "Waterman", 
                         "Faber-Castell", "Cello", "Casio", "Maped", "Staedtler", "Lexi", "Navneet", "Luxor", "Kokuyo", "Pidilite"],
    "Sports & Fitness": ["Nike", "Adidas", "Puma", "Reebok", "Yonex", "Cosco", "Decathlon", "Wilson", "Fitbit", "Garmin", 
                       "Under Armour", "Kookaburra", "Callaway", "Nivia", "Speedo", "Skechers", "Mizuno", "Columbia", "Slazenger", "Head"],
    "Toys & Baby": ["Fisher-Price", "Barbie", "Hot Wheels", "LEGO", "Nerf", "Funskool", "Pampers", "Huggies", "Johnson & Johnson", "Chicco", 
                  "MeeMee", "Mothercare", "Graco", "Mattel", "Hasbro", "Disney", "Marvel", "Pigeon", "Medela", "Himalaya Baby"],
    "Grocery": ["Amul", "Nestle", "Britannia", "Parle", "ITC", "Haldiram's", "Patanjali", "MDH", "Tata", "Kissan", 
               "Dabur", "Kellogg's", "MTR", "Cadbury", "Heinz", "Saffola", "Everest", "Del Monte", "Britannia", "Paper Boat"],
    "Appliances": ["Samsung", "LG", "Whirlpool", "Haier", "Godrej", "IFB", "Bosch", "Panasonic", "Voltas", "Blue Star", 
                  "Hitachi", "Daikin", "Carrier", "Bajaj", "Crompton", "Havells", "Kent", "Philips", "Eureka Forbes", "Symphony"]
}

# Descriptive words to make product titles and descriptions more realistic
ADJECTIVES = ["Premium", "Durable", "Stylish", "Modern", "Classic", "High-quality", "Ergonomic", 
              "Elegant", "Advanced", "Professional", "Compact", "Lightweight", "Comfortable", "Smart", 
              "Innovative", "Powerful", "Energy-efficient", "Versatile", "Portable", "Reliable", 
              "Multi-functional", "Sleek", "Robust", "Trendy", "Eco-friendly", "Luxury", "Handcrafted", 
              "Ultra", "Essential", "Superior"]

BENEFITS = ["with enhanced durability", "for everyday use", "designed for professionals", 
            "with advanced features", "with exceptional comfort", "for ultimate performance", 
            "with innovative technology", "for seamless experience", "with premium quality", 
            "for maximum efficiency", "with ergonomic design", "for stylish appearance", 
            "with smart connectivity", "for reliable performance", "with modern aesthetics", 
            "for compact storage", "with energy-saving features", "for versatile usage", 
            "with portable convenience", "for long-lasting use"]

# Price ranges by category
PRICE_RANGES = {
    "Electronics": (1999, 150000),
    "Clothing": (399, 9999),
    "Footwear": (499, 12999),
    "Home & Kitchen": (199, 50000),
    "Beauty & Personal Care": (99, 5999),
    "Books & Stationery": (49, 1999),
    "Sports & Fitness": (299, 29999),
    "Toys & Baby": (199, 15999),
    "Grocery": (10, 2499),
    "Appliances": (999, 100000)
}

# Features by category
FEATURES = {
    "Electronics": ["Wireless", "Bluetooth", "Touch Screen", "HD Display", "Fast Charging", "4K", "AI-Powered", 
                   "Water Resistant", "High Resolution", "Voice Control", "Dual Cameras", "Ultra-slim", "Long Battery Life", 
                   "Fingerprint Sensor", "Face Recognition", "Cloud Storage", "High Performance", "Noise Cancellation", "Memory Expansion"],
    "Clothing": ["Breathable Fabric", "Quick Dry", "Stretchable", "Wrinkle Free", "Stain Resistant", "UV Protection", 
                "Water Repellent", "Anti-bacterial", "Moisture Wicking", "Regular Fit", "Slim Fit", "Relaxed Fit", "Tapered", 
                "Slim Straight", "Classic Fit", "Loose Fit", "Pre-washed", "Oversized", "Vintage Look"],
    "Footwear": ["Memory Foam", "Anti-skid", "Shock Absorption", "Arch Support", "Breathable Mesh", "Cushioned Insole", 
                "Slip Resistant", "Lightweight", "Flexible Sole", "Water Resistant", "Quick Drying", "Orthopedic Design", 
                "Contoured Footbed", "Extra Wide", "Extra Grip", "Ankle Support", "Low-top", "High-top", "Mid-top"],
    "Home & Kitchen": ["BPA Free", "Dishwasher Safe", "Microwave Safe", "Energy Efficient", "Non-stick", "Stain Resistant", 
                      "Odor Resistant", "Heat Resistant", "Space-saving", "Easy to Clean", "Durable Construction", "Eco-friendly", 
                      "Multipurpose", "Stackable", "Adjustable", "Scratch Resistant", "Waterproof", "Foldable", "Temperature Control"],
    "Beauty & Personal Care": ["Paraben Free", "Cruelty Free", "Dermatologically Tested", "Hypoallergenic", "Oil-free", 
                             "Fragrance Free", "Non-comedogenic", "SPF Protection", "Long-lasting", "Waterproof", "All Skin Types", 
                             "Natural Ingredients", "Anti-aging", "Hydrating", "Quick Absorbing", "No Animal Testing", "Vegan"],
    "Books & Stationery": ["Hardcover", "Paperback", "Limited Edition", "Illustrated", "Acid-free Paper", "Smudge-proof", 
                          "Water-resistant", "Refillable", "Tear-resistant", "Smooth Writing", "Archival Quality", "Ruled", "Unruled", 
                          "Graph", "Dotted", "Spiral Bound", "Thread Bound", "Eco-friendly", "Non-toxic", "Educational"],
    "Sports & Fitness": ["Sweat-wicking", "Adjustable", "Anti-slip", "Impact Resistant", "Foldable", "Portable", "Digital Tracking", 
                        "Easy Assembly", "Space-saving", "Multi-level", "Extra Comfort", "High Endurance", "Weather Resistant", 
                        "Padded", "Lightweight", "Durable Construction", "Ergonomic Design", "Professional Grade", "Heavy-duty"],
    "Toys & Baby": ["Educational", "Interactive", "Battery-operated", "BPA-free", "Non-toxic", "Washable", "Age-appropriate", 
                   "Developmental", "STEM Learning", "Sensory Play", "Creative Play", "Role Play", "Musical", "Building Skills", 
                   "Hand-eye Coordination", "Problem Solving", "Soft Material", "Safe Edges", "Child-friendly"],
    "Grocery": ["Organic", "Natural", "Gluten-free", "Vegan", "Sugar-free", "Low-fat", "High-protein", "Fortified", "No preservatives", 
               "No artificial colors", "No artificial flavors", "GMO-free", "Locally Sourced", "Farm Fresh", "Sustainably Sourced", 
               "Eco-friendly Packaging", "Low Sodium", "Low Carb", "Keto-friendly"],
    "Appliances": ["Energy Efficient", "Smart Features", "Timer Function", "Auto Shut-off", "Digital Display", "Multiple Settings", 
                  "Programmable", "Quiet Operation", "Quick Heat/Cool", "Remote Controlled", "Voice Enabled", "App Control", 
                  "Child Lock", "Sleep Mode", "Energy Star Rated", "Inverter Technology", "Self Cleaning", "High Capacity", "Low Maintenance"]
}

def generate_product_id(category, index):
    """Generate unique product ID based on category and index"""
    category_code = ''.join([word[0] for word in category.split()])[:3].upper()
    return f"{category_code}{index:06d}"

def generate_title(category, subcategory, brand, features):
    """Generate realistic product title"""
    adjective = random.choice(ADJECTIVES)
    feature = random.choice(features[:5]) if random.random() > 0.3 else ""
    feature_text = f" {feature}" if feature else ""
    
    if random.random() > 0.7:  # Add model number sometimes
        model = f" {random.choice(['Pro', 'Ultra', 'Lite', 'Max', 'Plus', 'Elite', '2.0', 'XL', 'Mini'])} {random.randint(1, 15)}"
    else:
        model = ""
        
    return f"{brand} {adjective} {subcategory}{feature_text}{model}"

def generate_description(category, subcategory, title, features):
    """Generate detailed product description"""
    # Basic description
    adj1, adj2 = random.sample(ADJECTIVES, 2)
    benefit = random.choice(BENEFITS)
    
    # Select 3-5 features
    selected_features = random.sample(features, min(random.randint(3, 5), len(features)))
    features_text = ", ".join(selected_features)
    
    # Generate dynamic description with features
    description = (
        f"{title} - {adj1} {subcategory} {benefit}. "
        f"This {adj2} product offers {features_text}. "
        f"Perfect for anyone looking for quality and performance in a {subcategory.lower()}. "
        f"Made with high-quality materials to ensure durability and long-lasting use."
    )
    
    return description

def generate_diverse_products(count=5000):
    """Generate specified number of diverse products"""
    products = []
    
    # Calculate distribution across categories
    category_distribution = {}
    base_count = count // len(CATEGORIES)
    remainder = count % len(CATEGORIES)
    
    for category in CATEGORIES:
        category_distribution[category] = base_count + (1 if remainder > 0 else 0)
        remainder -= 1 if remainder > 0 else 0
    
    # Generate products for each category
    product_index = 1
    for category, allocation in category_distribution.items():
        min_price, max_price = PRICE_RANGES[category]
        brands = BRANDS[category]
        subcategories = CATEGORIES[category]
        category_features = FEATURES[category]
        
        for i in range(allocation):
            # Select brand and subcategory
            brand = random.choice(brands)
            subcategory = random.choice(subcategories)
            
            # Generate product details
            product_id = generate_product_id(category, product_index)
            title = generate_title(category, subcategory, brand, category_features)
            description = generate_description(category, subcategory, title, category_features)
            
            # Pricing
            current_price = round(random.uniform(min_price, max_price), -1)  # Round to nearest 10
            discount = random.choice([0, 0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5])  # More likely to have smaller or no discount
            original_price = round(current_price / (1 - discount) if discount > 0 else current_price, -1)
            
            # Ratings and availability
            rating = round(random.uniform(3.5, 5.0), 1)  # Most products have good ratings
            if rating > 4.8:  # Exceptional products are rare
                rating = 4.8
            num_ratings = int(random.triangular(10, 5000, 200))  # Most have moderate number of ratings
            is_available = random.random() > 0.05  # 95% of products are available
            
            # Create product
            products.append({
                "product_id": product_id,
                "title": title,
                "description": description,
                "category": category,
                "subcategory": subcategory,
                "brand": brand,
                "current_price": current_price,
                "original_price": original_price,
                "rating": rating,
                "num_ratings": num_ratings,
                "is_available": is_available
            })
            
            product_index += 1
    
    print(f"✅ Generated {len(products)} diverse products across {len(CATEGORIES)} categories")
    return products

def add_products_to_database(products):
    """Add products to the database"""
    print("🗃️ Adding products to search_system.db...")
    
    # Connect to SQLite database
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    # Make sure table exists
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
    
    # Start timing
    start_time = time.time()
    
    # Insert products in batches
    batch_size = 100
    total_batches = (len(products) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(products))
        batch = products[start_idx:end_idx]
        
        try:
            cursor.executemany(
                '''
                INSERT OR REPLACE INTO products 
                (product_id, title, description, category, subcategory, brand, 
                current_price, original_price, rating, num_ratings, is_available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                [
                    (
                        p["product_id"],
                        p["title"],
                        p["description"],
                        p["category"],
                        p["subcategory"],
                        p["brand"],
                        p["current_price"],
                        p["original_price"],
                        p["rating"],
                        p["num_ratings"],
                        1 if p["is_available"] else 0
                    )
                    for p in batch
                ]
            )
            conn.commit()
            
            # Progress update
            percent_complete = (batch_num + 1) / total_batches * 100
            elapsed_time = time.time() - start_time
            products_added = end_idx
            print(f"⏳ Progress: {percent_complete:.1f}% - Added {products_added}/{len(products)} products ({elapsed_time:.1f}s elapsed)")
            
        except Exception as e:
            print(f"❌ Error adding batch {batch_num+1}/{total_batches}: {e}")
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    
    # Count per category
    print("\n📊 Database Product Distribution:")
    cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC")
    category_counts = cursor.fetchall()
    
    for category, category_count in category_counts:
        print(f"  {category}: {category_count} products")
    
    # Close connection
    conn.close()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Added {count} total products to database in {elapsed:.2f} seconds")

def main():
    """Main function"""
    print("🚀 Generating diverse product dataset...")
    print("=" * 60)
    
    # Generate products
    products = generate_diverse_products(count=5000)
    
    # Add to database
    add_products_to_database(products)
    
    print("\n🎉 Product generation complete!")
    print("=" * 60)
    print("You can now search for products using the API.")

if __name__ == "__main__":
    main()
