"""
Product Data Generation Script

This script generates sample product data for the Flipkart search system.
It creates realistic e-commerce product data with categories, prices, ratings, etc.
"""

import csv
import json
import random
import uuid
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from faker import Faker

# Initialize Faker
fake = Faker()

# Product categories and their subcategories
CATEGORIES = {
    "Electronics": {
        "Mobile Phones": ["Smartphones", "Feature Phones", "Mobile Accessories"],
        "Laptops": ["Gaming Laptops", "Business Laptops", "Ultrabooks"],
        "TVs": ["Smart TVs", "LED TVs", "OLED TVs"],
        "Audio": ["Headphones", "Speakers", "Earbuds"],
        "Cameras": ["DSLR", "Mirrorless", "Action Cameras"],
        "Gaming": ["Gaming Consoles", "Gaming Accessories", "PC Gaming"]
    },
    "Fashion": {
        "Men's Clothing": ["Shirts", "T-Shirts", "Jeans", "Formal Wear"],
        "Women's Clothing": ["Dresses", "Tops", "Jeans", "Ethnic Wear"],
        "Footwear": ["Casual Shoes", "Formal Shoes", "Sports Shoes", "Sandals"],
        "Accessories": ["Watches", "Bags", "Belts", "Sunglasses"]
    },
    "Home & Furniture": {
        "Furniture": ["Sofas", "Beds", "Dining Tables", "Chairs"],
        "Home Decor": ["Wall Art", "Lighting", "Rugs", "Curtains"],
        "Kitchen": ["Cookware", "Appliances", "Storage", "Dining"]
    },
    "Sports & Fitness": {
        "Fitness": ["Gym Equipment", "Yoga", "Cardio", "Weights"],
        "Sports": ["Cricket", "Football", "Badminton", "Tennis"],
        "Outdoor": ["Camping", "Cycling", "Running", "Swimming"]
    },
    "Books": {
        "Fiction": ["Romance", "Mystery", "Sci-Fi", "Fantasy"],
        "Non-Fiction": ["Biography", "Self-Help", "Business", "History"],
        "Academic": ["Engineering", "Medical", "Arts", "Science"]
    }
}

# Brand names for different categories
BRANDS = {
    "Electronics": ["Samsung", "Apple", "Sony", "LG", "OnePlus", "Xiaomi", "Realme", "Oppo", "Vivo"],
    "Fashion": ["Nike", "Adidas", "Puma", "Levi's", "H&M", "Zara", "Allen Solly", "Peter England"],
    "Home & Furniture": ["IKEA", "Godrej", "Durian", "Urban Ladder", "Pepperfry", "HomeTown"],
    "Sports & Fitness": ["Nike", "Adidas", "Reebok", "Decathlon", "Cosco", "Yonex"],
    "Books": ["Penguin", "Harper Collins", "Scholastic", "McGraw Hill", "Pearson"]
}

# Common product adjectives
ADJECTIVES = [
    "Premium", "Deluxe", "Pro", "Ultra", "Max", "Plus", "Elite", "Advanced",
    "Smart", "Wireless", "Portable", "Compact", "Heavy Duty", "Professional",
    "Lightweight", "Durable", "High Quality", "Budget", "Affordable"
]

def generate_product_title(category: str, subcategory: str, product_type: str, brand: str) -> str:
    """Generate realistic product title"""
    adjective = random.choice(ADJECTIVES) if random.random() > 0.3 else ""
    
    # Add some variation in title structure
    structures = [
        f"{brand} {adjective} {product_type}",
        f"{adjective} {brand} {product_type}",
        f"{brand} {product_type} {adjective}",
        f"{product_type} by {brand}"
    ]
    
    title = random.choice(structures).strip()
    
    # Add some specifications for electronics
    if category == "Electronics":
        if "Mobile" in subcategory:
            storage = random.choice(["64GB", "128GB", "256GB", "512GB"])
            ram = random.choice(["4GB", "6GB", "8GB", "12GB"])
            title += f" ({ram} RAM, {storage})"
        elif "Laptop" in subcategory:
            processor = random.choice(["Intel i5", "Intel i7", "AMD Ryzen 5", "AMD Ryzen 7"])
            title += f" ({processor})"
        elif "TV" in subcategory:
            size = random.choice(["32", "43", "55", "65", "75"])
            title += f" {size} inch"
    
    return title

def generate_product_description(title: str, category: str) -> str:
    """Generate product description"""
    base_desc = f"High-quality {title.lower()} perfect for your needs. "
    
    features = []
    if category == "Electronics":
        features = [
            "Latest technology", "Energy efficient", "User-friendly interface",
            "Durable build quality", "Excellent performance", "Great value for money"
        ]
    elif category == "Fashion":
        features = [
            "Comfortable fit", "Stylish design", "Premium material",
            "Perfect for daily wear", "Easy to maintain", "Trendy look"
        ]
    elif category == "Home & Furniture":
        features = [
            "Space-saving design", "Easy assembly", "Premium finish",
            "Durable construction", "Modern styling", "Great functionality"
        ]
    
    selected_features = random.sample(features, min(3, len(features)))
    description = base_desc + " Features: " + ", ".join(selected_features) + "."
    
    return description

def generate_product_data(num_products: int = 5000) -> List[Dict[str, Any]]:
    """Generate sample product data"""
    products = []
    
    for i in range(num_products):
        # Select random category hierarchy
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(list(CATEGORIES[category].keys()))
        product_type = random.choice(CATEGORIES[category][subcategory])
        
        # Select brand
        brand = random.choice(BRANDS[category])
        
        # Generate product details
        product_id = f"FLP{str(uuid.uuid4())[:8].upper()}"
        title = generate_product_title(category, subcategory, product_type, brand)
        description = generate_product_description(title, category)
        
        # Generate pricing
        base_price = random.randint(500, 50000)
        discount = random.randint(5, 70)
        discounted_price = int(base_price * (100 - discount) / 100)
        
        # Generate ratings and reviews
        rating = round(random.uniform(3.0, 5.0), 1)
        num_ratings = random.randint(50, 10000)
        num_reviews = random.randint(10, int(num_ratings * 0.3))
        
        # Generate other attributes
        stock = random.randint(0, 500)
        is_bestseller = random.random() < 0.1  # 10% bestsellers
        is_new_arrival = random.random() < 0.05  # 5% new arrivals
        
        product = {
            "product_id": product_id,
            "title": title,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "product_type": product_type,
            "brand": brand,
            "price": discounted_price,
            "original_price": base_price,
            "discount_percentage": discount,
            "rating": rating,
            "num_ratings": num_ratings,
            "num_reviews": num_reviews,
            "stock": stock,
            "is_bestseller": is_bestseller,
            "is_new_arrival": is_new_arrival,
            "image_url": f"https://example.com/images/{product_id.lower()}.jpg",
            "created_at": fake.date_time_this_year().isoformat()
        }
        
        products.append(product)
    
    return products

def generate_autosuggest_data(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate autosuggest queries from product data"""
    queries = set()
    
    # Extract n-grams from product titles
    for product in products:
        title_words = product["title"].lower().split()
        
        # Add individual words
        for word in title_words:
            if len(word) > 2:
                queries.add(word)
        
        # Add 2-grams
        for i in range(len(title_words) - 1):
            bigram = f"{title_words[i]} {title_words[i+1]}"
            queries.add(bigram)
        
        # Add 3-grams
        for i in range(len(title_words) - 2):
            trigram = f"{title_words[i]} {title_words[i+1]} {title_words[i+2]}"
            queries.add(trigram)
        
        # Add category and brand names
        queries.add(product["category"].lower())
        queries.add(product["subcategory"].lower())
        queries.add(product["brand"].lower())
    
    # Convert to list with popularity scores
    autosuggest_data = []
    for query in queries:
        if len(query.strip()) > 2:
            # Simulate popularity based on query characteristics
            popularity = random.randint(100, 10000)
            if any(brand.lower() in query for brand in ["samsung", "apple", "nike"]):
                popularity *= 2  # Popular brands get higher scores
            
            autosuggest_data.append({
                "query": query.strip(),
                "popularity": popularity,
                "category": random.choice(list(CATEGORIES.keys())).lower()
            })
    
    # Sort by popularity and take top entries
    autosuggest_data.sort(key=lambda x: x["popularity"], reverse=True)
    return autosuggest_data[:2000]  # Top 2000 queries

def save_data_to_files(products: List[Dict[str, Any]], autosuggest_data: List[Dict[str, Any]]):
    """Save generated data to files"""
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save products to CSV
    products_df = pd.DataFrame(products)
    products_df.to_csv(data_dir / "flipkart_products.csv", index=False)
    print(f"✅ Saved {len(products)} products to {data_dir / 'flipkart_products.csv'}")
    
    # Save autosuggest data to CSV
    autosuggest_df = pd.DataFrame(autosuggest_data)
    autosuggest_df.to_csv(data_dir / "autosuggest_queries.csv", index=False)
    print(f"✅ Saved {len(autosuggest_data)} autosuggest queries to {data_dir / 'autosuggest_queries.csv'}")
    
    # Save sample reviews (simplified for now)
    reviews = []
    for i in range(1000):
        product_id = random.choice(products)["product_id"]
        review = {
            "review_id": f"REV{str(uuid.uuid4())[:8].upper()}",
            "product_id": product_id,
            "user_id": f"USER{random.randint(1000, 9999)}",
            "rating": random.randint(1, 5),
            "review_text": fake.text(max_nb_chars=200),
            "helpful_votes": random.randint(0, 50),
            "verified_purchase": random.choice([True, False]),
            "created_at": fake.date_time_this_year().isoformat()
        }
        reviews.append(review)
    
    reviews_df = pd.DataFrame(reviews)
    reviews_df.to_csv(data_dir / "flipkart_reviews.csv", index=False)
    print(f"✅ Saved {len(reviews)} reviews to {data_dir / 'flipkart_reviews.csv'}")

def main():
    """Main function to generate all data"""
    print("🔄 Generating sample product data...")
    
    # Generate products
    products = generate_product_data(num_products=5000)
    print(f"✅ Generated {len(products)} products")
    
    # Generate autosuggest data
    autosuggest_data = generate_autosuggest_data(products)
    print(f"✅ Generated {len(autosuggest_data)} autosuggest queries")
    
    # Save to files
    save_data_to_files(products, autosuggest_data)
    
    print("🎉 Data generation complete!")
    print("\nNext steps:")
    print("1. Run: python scripts/seed_db.py (to populate database)")
    print("2. Run: python scripts/generate_embeddings.py (to create vector embeddings)")

if __name__ == "__main__":
    main()
