"""
Quick database check
"""
import sqlite3

conn = sqlite3.connect('data/flipkart_products.db')
cursor = conn.cursor()

# Check products count
cursor.execute('SELECT COUNT(*) FROM products')
print(f'Total products: {cursor.fetchone()[0]}')

# Check sample products
cursor.execute('SELECT title, category, current_price FROM products WHERE title IS NOT NULL LIMIT 10')
print('\nSample products:')
for row in cursor.fetchall():
    print(f'- {row[0]} ({row[1]}) - ₹{row[2]}')

# Check for smartphones specifically
cursor.execute("SELECT COUNT(*) FROM products WHERE title LIKE '%phone%' OR category LIKE '%phone%' OR title LIKE '%mobile%'")
print(f'\nProducts with phone/mobile: {cursor.fetchone()[0]}')

# Check categories
cursor.execute('SELECT DISTINCT category FROM products LIMIT 10')
print('\nCategories:')
for row in cursor.fetchall():
    print(f'- {row[0]}')

conn.close()
