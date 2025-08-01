import sqlite3
from app.db.database import get_db
from app.db.models import Product
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Test direct database connection
print("=== Direct SQLite Test ===")
conn = sqlite3.connect('data/flipkart_products.db')
cursor = conn.cursor()
result = cursor.execute("SELECT id, product_id, title, brand FROM products LIMIT 3").fetchall()
print("Direct query results:")
for row in result:
    print(row)
conn.close()

# Test SQLAlchemy connection
print("\n=== SQLAlchemy Test ===")
try:
    engine = create_engine("sqlite:///./data/flipkart_products.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Try simple query
    result = db.query(Product).first()
    if result:
        print(f"SQLAlchemy result: {result.id}, {result.product_id}, {result.title}")
    else:
        print("No results from SQLAlchemy")
    
    # Try count
    count = db.query(Product).count()
    print(f"Product count: {count}")
    
except Exception as e:
    print(f"SQLAlchemy error: {e}")
finally:
    db.close()
