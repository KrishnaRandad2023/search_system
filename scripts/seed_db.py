"""
Database Seeding Script

This script populates the database with generated product data.
"""

import asyncio
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import Base, get_db_url
from app.db.models import Product, AutosuggestQuery, Review

async def seed_database():
    """Seed database with sample data"""
    print("🌱 Seeding database...")
    
    # Create database engine
    db_url = get_db_url()
    engine = create_engine(db_url)
    
    # Drop all tables first to ensure schema is updated
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables dropped and recreated")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Load and insert products
        products_file = Path("data/raw/flipkart_products.csv")
        if products_file.exists():
            print("📦 Loading products data...")
            products_df = pd.read_csv(products_file)
            
            for _, row in products_df.iterrows():
                product = Product(
                    product_id=row["product_id"],
                    title=row["title"],
                    description=row["description"],
                    category=row["category"],
                    subcategory=row["subcategory"],
                    product_type=row["product_type"],
                    brand=row["brand"],
                    price=row["price"],
                    original_price=row["original_price"],
                    discount_percentage=row["discount_percentage"],
                    rating=row["rating"],
                    num_ratings=row["num_ratings"],
                    num_reviews=row["num_reviews"],
                    stock=row["stock"],
                    is_bestseller=row["is_bestseller"],
                    is_new_arrival=row["is_new_arrival"],
                    image_url=row["image_url"]
                )
                session.add(product)
            
            session.commit()
            print(f"✅ Inserted {len(products_df)} products")
        
        # Load and insert autosuggest queries
        autosuggest_file = Path("data/raw/autosuggest_queries.csv")
        if autosuggest_file.exists():
            print("🔍 Loading autosuggest data...")
            autosuggest_df = pd.read_csv(autosuggest_file)
            
            for _, row in autosuggest_df.iterrows():
                query = AutosuggestQuery(
                    query=row["query"],
                    popularity=row["popularity"],
                    category=row["category"]
                )
                session.add(query)
            
            session.commit()
            print(f"✅ Inserted {len(autosuggest_df)} autosuggest queries")
        
        # Load and insert reviews
        reviews_file = Path("data/raw/flipkart_reviews.csv")
        if reviews_file.exists():
            print("⭐ Loading reviews data...")
            reviews_df = pd.read_csv(reviews_file)
            
            for _, row in reviews_df.iterrows():
                review = Review(
                    review_id=row["review_id"],
                    product_id=row["product_id"],
                    user_id=row["user_id"],
                    rating=row["rating"],
                    review_text=row["review_text"],
                    helpful_votes=row["helpful_votes"],
                    verified_purchase=row["verified_purchase"]
                )
                session.add(review)
            
            session.commit()
            print(f"✅ Inserted {len(reviews_df)} reviews")
        
        print("🎉 Database seeding complete!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main function"""
    print("🗃️ Starting database seeding...")
    
    # Check if data files exist
    data_files = [
        "data/raw/flipkart_products.csv",
        "data/raw/autosuggest_queries.csv", 
        "data/raw/flipkart_reviews.csv"
    ]
    
    missing_files = [f for f in data_files if not Path(f).exists()]
    
    if missing_files:
        print("❌ Missing data files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease run: python scripts/ingest_products.py first")
        return
    
    # Run seeding
    asyncio.run(seed_database())

if __name__ == "__main__":
    main()
