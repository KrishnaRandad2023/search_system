import sqlite3

conn = sqlite3.connect('data/flipkart_products.db')
cursor = conn.cursor()

cursor.execute("SELECT title, subcategory, current_price FROM products WHERE category = 'Electronics' LIMIT 10")
print('Electronics products:')
for row in cursor.fetchall():
    print(f'- {row[0]} ({row[1]}) - ₹{row[2]}')

conn.close()
