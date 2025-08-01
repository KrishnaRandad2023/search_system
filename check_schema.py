import sqlite3

# Connect to database
conn = sqlite3.connect('data/flipkart_products.db')

print("Products table schema:")
for row in conn.execute('PRAGMA table_info(products)'):
    print(row)

print(f"\nNumber of products:")
for row in conn.execute('SELECT COUNT(*) FROM products'):
    print(f"Total products: {row[0]}")

print("\nFirst 3 products:")
try:
    for row in conn.execute('SELECT product_id, title, brand, category, current_price FROM products LIMIT 3'):
        print(row)
except Exception as e:
    print(f"Error: {e}")

print("\nTesting smartphone-related products:")
try:
    for row in conn.execute("SELECT product_id, title, brand FROM products WHERE title LIKE '%smartphone%' OR title LIKE '%mobile%' OR title LIKE '%phone%' LIMIT 5"):
        print(row)
except Exception as e:
    print(f"Error: {e}")

conn.close()
