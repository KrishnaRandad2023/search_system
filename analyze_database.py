"""
Database Analysis Tool for Flipkart Search System

This script analyzes the products in the search_system.db database
and provides useful statistics and sample queries.
"""

import sqlite3
import json
import os
from tabulate import tabulate
import matplotlib.pyplot as plt
import pandas as pd
import random

def count_products_by_category():
    """Count products by category"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC")
    rows = cursor.fetchall()
    
    print("\n📊 Products by Category:")
    print(tabulate(rows, headers=["Category", "Count"], tablefmt="grid"))
    
    conn.close()
    return rows

def count_products_by_subcategory(limit=20):
    """Count products by subcategory"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, subcategory, COUNT(*) as count 
        FROM products 
        GROUP BY category, subcategory 
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    
    print(f"\n📊 Top {limit} Subcategories:")
    print(tabulate(rows, headers=["Category", "Subcategory", "Count"], tablefmt="grid"))
    
    conn.close()
    return rows

def count_products_by_brand(limit=20):
    """Count products by brand"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT brand, COUNT(*) as count 
        FROM products 
        GROUP BY brand 
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    
    print(f"\n📊 Top {limit} Brands:")
    print(tabulate(rows, headers=["Brand", "Count"], tablefmt="grid"))
    
    conn.close()
    return rows

def price_distribution():
    """Analyze price distribution"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            category,
            MIN(current_price) as min_price,
            MAX(current_price) as max_price,
            AVG(current_price) as avg_price,
            COUNT(*) as count
        FROM products
        GROUP BY category
        ORDER BY avg_price DESC
    """)
    rows = cursor.fetchall()
    
    print("\n💰 Price Distribution by Category:")
    print(tabulate(rows, headers=["Category", "Min Price", "Max Price", "Avg Price", "Count"], tablefmt="grid"))
    
    conn.close()
    return rows

def sample_product_queries():
    """Run some sample queries to demonstrate search"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    # List of sample search terms
    search_terms = [
        "shoes", "laptop", "smartphone", "headphones", "t-shirt", 
        "watch", "camera", "furniture", "kitchen", "toys"
    ]
    
    print("\n🔍 Sample Search Results:")
    for term in search_terms:
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE title LIKE ? OR description LIKE ? OR category LIKE ? OR subcategory LIKE ?
        """, (f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'))
        count = cursor.fetchone()[0]
        
        print(f"• Search for '{term}': {count} products found")
        
        if count > 0:
            cursor.execute("""
                SELECT title, category, subcategory 
                FROM products 
                WHERE title LIKE ? OR description LIKE ? OR category LIKE ? OR subcategory LIKE ?
                LIMIT 3
            """, (f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'))
            samples = cursor.fetchall()
            
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. {sample[0]} - {sample[1]}, {sample[2]}")
            
            print()
    
    conn.close()

def sample_diverse_products():
    """Get sample products from each category"""
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    
    print("\n🔍 Sample Products from Each Category:")
    for category in categories:
        cursor.execute("""
            SELECT product_id, title, subcategory, brand, current_price, rating
            FROM products
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT 2
        """, (category,))
        samples = cursor.fetchall()
        
        print(f"\n• {category}:")
        for sample in samples:
            product_id, title, subcategory, brand, price, rating = sample
            print(f"  - {title}")
            print(f"    ID: {product_id} | {subcategory} by {brand} | ₹{price:.2f} | Rating: {rating}★")
    
    conn.close()

def export_sample_json(count=50):
    """Export a sample of products to JSON for review"""
    conn = sqlite3.connect('search_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products ORDER BY RANDOM() LIMIT ?", (count,))
    rows = cursor.fetchall()
    
    # Convert to list of dicts
    products = []
    for row in rows:
        product = {}
        for key in row.keys():
            product[key] = row[key]
        products.append(product)
    
    # Export to JSON
    with open('sample_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Exported {len(products)} random products to sample_products.json")
    conn.close()

def plot_category_distribution(category_data):
    """Plot category distribution as pie chart"""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(category_data, columns=['Category', 'Count'])
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(df['Count'], labels=df['Category'], autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Product Distribution by Category')
        plt.tight_layout()
        
        # Save figure
        plt.savefig('category_distribution.png')
        print("\n📊 Saved category distribution chart to category_distribution.png")
        
    except Exception as e:
        print(f"Could not generate chart: {e}")
        print("Make sure matplotlib and pandas are installed.")

def main():
    """Main function"""
    print("=" * 80)
    print("🔍 FLIPKART SEARCH SYSTEM - DATABASE ANALYSIS")
    print("=" * 80)
    
    # Connect to database
    try:
        conn = sqlite3.connect('search_system.db')
        cursor = conn.cursor()
        
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print("❌ Table 'products' does not exist in search_system.db")
            conn.close()
            return
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM products")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total Products: {total_count}")
        
        conn.close()
        
        # Run analyses
        category_data = count_products_by_category()
        count_products_by_subcategory()
        count_products_by_brand()
        price_distribution()
        sample_product_queries()
        sample_diverse_products()
        export_sample_json()
        
        # Generate chart if matplotlib and pandas are available
        try:
            plot_category_distribution(category_data)
        except ImportError:
            print("\nℹ️ Matplotlib and pandas are required for charts. Install with:")
            print("pip install matplotlib pandas")
        
        print("\n✅ Database analysis complete")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
