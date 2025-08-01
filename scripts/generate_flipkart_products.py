#!/usr/bin/env python3
"""
Flipkart-style Product Database Generator
Generates 10,000+ realistic products for the search system
"""

import sqlite3
import json
import random
from faker import Faker
from pathlib import Path
import uuid
from datetime import datetime, timedelta

fake = Faker('en_IN')  # Indian locale for authentic data

class FlipkartProductGenerator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
        
    def setup_database(self):
        """Create the products table with all necessary fields"""
        cursor = self.conn.cursor()
        
        # Drop table if exists to ensure clean slate
        cursor.execute("DROP TABLE IF EXISTS products")
        
        # Create comprehensive products table
        cursor.execute("""
            CREATE TABLE products (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                brand TEXT,
                category TEXT NOT NULL,
                subcategory TEXT,
                price DECIMAL(10,2) NOT NULL,
                original_price DECIMAL(10,2),
                discount_percentage INTEGER DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                is_in_stock BOOLEAN DEFAULT 1,
                description TEXT,
                specifications TEXT,
                image_urls TEXT,
                seller_name TEXT,
                seller_rating DECIMAL(3,2),
                is_flipkart_assured BOOLEAN DEFAULT 0,
                is_plus_product BOOLEAN DEFAULT 0,
                delivery_days INTEGER DEFAULT 5,
                tags TEXT,
                color TEXT,
                size TEXT,
                weight TEXT,
                dimensions TEXT,
                warranty TEXT,
                return_policy TEXT,
                ctr DECIMAL(5,4) DEFAULT 0.0,
                conversion_rate DECIMAL(5,4) DEFAULT 0.0,
                click_count INTEGER DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                wishlist_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better search performance
        cursor.execute("CREATE INDEX idx_title ON products(title)")
        cursor.execute("CREATE INDEX idx_category ON products(category)")
        cursor.execute("CREATE INDEX idx_brand ON products(brand)")
        cursor.execute("CREATE INDEX idx_price ON products(price)")
        cursor.execute("CREATE INDEX idx_rating ON products(rating)")
        cursor.execute("CREATE INDEX idx_stock ON products(is_in_stock)")
        
        self.conn.commit()
        
    def get_flipkart_categories(self):
        """Return realistic Flipkart categories and subcategories"""
        return {
            "Electronics": [
                "Mobiles", "Laptops", "Tablets", "Cameras", "Headphones", 
                "Speakers", "Smart Watches", "Gaming", "Audio", "Accessories"
            ],
            "Fashion": [
                "Men's Clothing", "Women's Clothing", "Kids' Clothing", 
                "Footwear", "Watches", "Bags", "Jewelry", "Sunglasses"
            ],
            "Home & Kitchen": [
                "Furniture", "Home Decor", "Kitchen Appliances", "Bedding", 
                "Bath", "Storage", "Lighting", "Garden"
            ],
            "Books": [
                "Fiction", "Non-Fiction", "Academic", "Children's Books", 
                "Comics", "Textbooks"
            ],
            "Sports & Fitness": [
                "Exercise Equipment", "Sports Gear", "Outdoor", "Cycling", 
                "Swimming", "Team Sports"
            ],
            "Beauty & Health": [
                "Skincare", "Makeup", "Hair Care", "Health Supplements", 
                "Personal Care", "Fragrance"
            ],
            "Grocery": [
                "Staples", "Beverages", "Snacks", "Personal Care", 
                "Baby Care", "Household Items"
            ],
            "Toys & Baby": [
                "Toys", "Baby Care", "Kids Fashion", "School Supplies", 
                "Baby Gear"
            ]
        }
        
    def get_brands_for_category(self, category: str):
        """Return realistic brands for each category"""
        brand_mapping = {
            "Electronics": [
                "Samsung", "Apple", "OnePlus", "Xiaomi", "Realme", "Oppo", "Vivo",
                "Sony", "LG", "Dell", "HP", "Lenovo", "Asus", "Acer", "Canon", "Nikon"
            ],
            "Fashion": [
                "Nike", "Adidas", "Puma", "Reebok", "Levi's", "H&M", "Zara", 
                "Uniqlo", "Van Heusen", "Allen Solly", "Peter England", "Arrow"
            ],
            "Home & Kitchen": [
                "IKEA", "Godrej", "Whirlpool", "LG", "Samsung", "Bosch", 
                "Prestige", "Butterfly", "Pigeon", "Milton"
            ],
            "Books": [
                "Penguin", "Harper Collins", "Scholastic", "Oxford", 
                "Cambridge", "McGraw Hill", "Pearson"
            ],
            "Sports & Fitness": [
                "Nike", "Adidas", "Puma", "Reebok", "Decathlon", "Yonex", 
                "Wilson", "Head", "Babolat"
            ],
            "Beauty & Health": [
                "L'Oreal", "Lakme", "Maybelline", "Revlon", "Nivea", 
                "Himalaya", "Patanjali", "Biotique"
            ],
            "Grocery": [
                "Nestle", "Britannia", "Parle", "ITC", "Hindustan Unilever", 
                "P&G", "Coca Cola", "PepsiCo"
            ],
            "Toys & Baby": [
                "Hasbro", "Mattel", "LEGO", "Fisher Price", "Johnson's", 
                "Pampers", "Huggies", "Chicco"
            ]
        }
        return brand_mapping.get(category, ["Generic", "Local Brand", "Store Brand"])
        
    def generate_product_title(self, category: str, subcategory: str, brand: str):
        """Generate realistic product titles"""
        
        title_templates = {
            "Electronics": {
                "Mobiles": [
                    f"{brand} {{model}} ({{storage}}GB, {{color}})",
                    f"{brand} {{model}} Smartphone with {{feature}}",
                    f"{brand} {{model}} 5G Mobile Phone"
                ],
                "Laptops": [
                    f"{brand} {{model}} Laptop ({{processor}}, {{ram}}GB RAM, {{storage}}GB SSD)",
                    f"{brand} {{model}} Gaming Laptop with {{gpu}}",
                    f"{brand} {{model}} Ultrabook"
                ],
                "Headphones": [
                    f"{brand} {{model}} Wireless Bluetooth Headphones",
                    f"{brand} {{model}} Noise Cancelling Headphones",
                    f"{brand} {{model}} Gaming Headset"
                ]
            },
            "Fashion": {
                "Men's Clothing": [
                    f"{brand} Men's {{type}} {{pattern}} {{color}}",
                    f"{brand} {{type}} for Men",
                    f"{brand} Casual {{type}}"
                ],
                "Footwear": [
                    f"{brand} {{type}} Shoes for {{gender}}",
                    f"{brand} {{color}} {{type}}",
                    f"{brand} Sports {{type}}"
                ]
            },
            "Home & Kitchen": {
                "Kitchen Appliances": [
                    f"{brand} {{appliance}} {{capacity}}L",
                    f"{brand} {{appliance}} with {{feature}}",
                    f"{brand} {{appliance}} - {{color}}"
                ]
            }
        }
        
        # Get template for this category/subcategory
        if category in title_templates and subcategory in title_templates[category]:
            template = random.choice(title_templates[category][subcategory])
        else:
            # Generic template
            template = f"{brand} {{adjective}} {{product_type}}"
            
        # Fill in template variables
        variables = {
            'model': f"{random.choice(['Pro', 'Max', 'Ultra', 'Plus', 'Lite', 'Air'])}{random.randint(10, 99)}",
            'storage': random.choice([64, 128, 256, 512, 1024]),
            'color': random.choice(['Black', 'White', 'Blue', 'Red', 'Gold', 'Silver']),
            'feature': random.choice(['Fast Charging', 'Triple Camera', 'AMOLED Display', 'Face Unlock']),
            'processor': random.choice(['Intel i5', 'Intel i7', 'AMD Ryzen 5', 'AMD Ryzen 7']),
            'ram': random.choice([8, 16, 32]),
            'gpu': random.choice(['NVIDIA RTX 3060', 'NVIDIA RTX 4060', 'AMD Radeon']),
            'type': random.choice(['Shirt', 'T-Shirt', 'Jeans', 'Jacket', 'Sneakers', 'Formal Shoes']),
            'pattern': random.choice(['Solid', 'Striped', 'Checkered', 'Printed']),
            'gender': random.choice(['Men', 'Women', 'Unisex']),
            'appliance': random.choice(['Microwave', 'Refrigerator', 'Washing Machine', 'Air Conditioner']),
            'capacity': random.choice([1.5, 2.0, 2.5, 5.0, 7.0, 10.0]),
            'adjective': random.choice(['Premium', 'Deluxe', 'Smart', 'Eco-Friendly', 'Professional']),
            'product_type': subcategory.split()[-1] if subcategory else 'Product'
        }
        
        try:
            return template.format(**variables)
        except KeyError:
            return f"{brand} {subcategory} - {random.choice(['Premium', 'Latest', 'Best Quality'])}"
            
    def generate_single_product(self, categories):
        """Generate a single realistic product"""
        
        # Select category and subcategory
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])
        
        # Select brand
        brands = self.get_brands_for_category(category)
        brand = random.choice(brands)
        
        # Generate basic info
        product_id = str(uuid.uuid4())[:8]
        title = self.generate_product_title(category, subcategory, brand)
        
        # Price logic - realistic pricing by category
        price_ranges = {
            "Electronics": (1000, 150000),
            "Fashion": (299, 15000),
            "Home & Kitchen": (500, 50000),
            "Books": (99, 2000),
            "Sports & Fitness": (300, 25000),
            "Beauty & Health": (150, 8000),
            "Grocery": (20, 2000),
            "Toys & Baby": (200, 10000)
        }
        
        min_price, max_price = price_ranges.get(category, (100, 5000))
        original_price = round(random.uniform(min_price, max_price), 2)
        
        # Discount logic
        discount_percentage = random.choices([0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70], 
                                           weights=[20, 15, 15, 12, 10, 8, 7, 5, 4, 3, 1])[0]
        price = round(original_price * (1 - discount_percentage / 100), 2)
        
        # Rating and reviews
        rating = round(random.triangular(3.0, 5.0, 4.2), 1)
        review_count = int(random.lognormvariate(4, 1.5))  # Realistic distribution
        
        # Stock and availability
        stock_quantity = random.choices(
            [0, random.randint(1, 10), random.randint(11, 100), random.randint(101, 1000)],
            weights=[5, 15, 50, 30]
        )[0]
        is_in_stock = stock_quantity > 0
        
        # Performance metrics (CTR, conversion, etc.)
        ctr = random.triangular(0.001, 0.1, 0.02)  # Realistic CTR
        conversion_rate = random.triangular(0.005, 0.3, 0.08)
        
        # Click and engagement metrics
        click_count = int(review_count * random.uniform(5, 15))
        order_count = int(click_count * conversion_rate)
        view_count = int(click_count * random.uniform(2, 8))
        wishlist_count = int(click_count * random.uniform(0.1, 0.3))
        
        # Additional attributes
        seller_names = ["SuperComNet", "RetailNet", "WS Retail", "Cloudtail India", "Appario Retail"]
        seller_name = random.choice(seller_names)
        seller_rating = round(random.triangular(3.5, 5.0, 4.3), 1)
        
        is_flipkart_assured = random.choice([True, False]) if random.random() > 0.3 else False
        is_plus_product = random.choice([True, False]) if random.random() > 0.7 else False
        
        delivery_days = random.choices([1, 2, 3, 5, 7, 10], weights=[10, 25, 30, 20, 10, 5])[0]
        
        # Generate description
        description = f"Buy {title} online at best price in India. {fake.text(max_nb_chars=200)}"
        
        # Tags for search
        tags = [category.lower(), subcategory.lower(), brand.lower()]
        if discount_percentage > 20:
            tags.append("sale")
        if rating >= 4.0:
            tags.append("bestseller")
        if is_flipkart_assured:
            tags.append("assured")
            
        return {
            'id': product_id,
            'title': title,
            'brand': brand,
            'category': category,
            'subcategory': subcategory,
            'price': price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'rating': rating,
            'review_count': review_count,
            'stock_quantity': stock_quantity,
            'is_in_stock': is_in_stock,
            'description': description,
            'specifications': json.dumps({"brand": brand, "category": category}),
            'image_urls': json.dumps([f"https://images.flipkart.com/{product_id}_1.jpg"]),
            'seller_name': seller_name,
            'seller_rating': seller_rating,
            'is_flipkart_assured': is_flipkart_assured,
            'is_plus_product': is_plus_product,
            'delivery_days': delivery_days,
            'tags': json.dumps(tags),
            'color': random.choice(['Black', 'White', 'Blue', 'Red', 'Multi']),
            'size': random.choice(['S', 'M', 'L', 'XL', 'Free Size', 'One Size']),
            'weight': f"{random.uniform(0.1, 5.0):.1f} kg",
            'dimensions': f"{random.randint(10, 50)}x{random.randint(10, 50)}x{random.randint(5, 30)} cm",
            'warranty': random.choice(['1 Year', '2 Years', '6 Months', 'No Warranty']),
            'return_policy': random.choice(['7 days', '10 days', '15 days', '30 days']),
            'ctr': round(ctr, 4),
            'conversion_rate': round(conversion_rate, 4),
            'click_count': click_count,
            'order_count': order_count,
            'view_count': view_count,
            'wishlist_count': wishlist_count
        }
        
    def generate_products(self, count: int = 10000):
        """Generate the specified number of products"""
        
        categories = self.get_flipkart_categories()
        
        print(f"🏭 Generating {count} Flipkart-style products...")
        
        # Prepare bulk insert
        cursor = self.conn.cursor()
        
        products = []
        for i in range(count):
            if i % 1000 == 0:
                print(f"Generated {i}/{count} products...")
                
            product = self.generate_single_product(categories)
            products.append(tuple(product.values()))
            
        # Bulk insert
        columns = list(self.generate_single_product(categories).keys())
        placeholders = ','.join(['?' for _ in columns])
        
        cursor.executemany(
            f"INSERT INTO products ({','.join(columns)}) VALUES ({placeholders})",
            products
        )
        
        self.conn.commit()
        print(f"✅ Successfully generated and inserted {count} products!")
        
        # Print summary statistics
        self.print_database_stats()
        
    def print_database_stats(self):
        """Print database statistics"""
        cursor = self.conn.cursor()
        
        # Total products
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        # Category distribution
        cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC")
        category_stats = cursor.fetchall()
        
        # Price ranges
        cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM products")
        price_min, price_max, price_avg = cursor.fetchone()
        
        # Rating distribution
        cursor.execute("SELECT AVG(rating), COUNT(*) FROM products WHERE rating >= 4.0")
        avg_rating, high_rated = cursor.fetchone()
        
        # Stock status
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_in_stock = 1")
        in_stock_count = cursor.fetchone()[0]
        
        print(f"\n📊 DATABASE STATISTICS")
        print(f"=" * 50)
        print(f"Total Products: {total_products:,}")
        print(f"Products In Stock: {in_stock_count:,}")
        print(f"Price Range: ₹{price_min:.2f} - ₹{price_max:.2f}")
        print(f"Average Price: ₹{price_avg:.2f}")
        print(f"Average Rating: {avg_rating:.2f}")
        print(f"High Rated Products (4.0+): {high_rated:,}")
        
        print(f"\n📈 CATEGORY DISTRIBUTION:")
        for category, count in category_stats:
            percentage = (count / total_products) * 100
            print(f"  {category}: {count:,} ({percentage:.1f}%)")
            
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    # Create database path
    db_path = Path(__file__).parent.parent / "data" / "db" / "flipkart_products.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate products
    generator = FlipkartProductGenerator(str(db_path))
    generator.generate_products(12000)  # Generate 12K products for good variety
    generator.close()
    
    print(f"\n🎉 Flipkart product database created at: {db_path}")
    print(f"Ready for your search system!")
