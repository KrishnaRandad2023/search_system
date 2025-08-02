import sqlite3
import os

# Check available database files
print("Current directory:", os.getcwd())
print("Database files in current directory:")
for file in os.listdir():
    if file.endswith('.db'):
        print(f"- {file}")

# Try to connect to search_system.db
try:
    conn = sqlite3.connect('search_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('\nTables in search_system.db:')
    if tables:
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("No tables found")
    conn.close()
except Exception as e:
    print(f"Error connecting to search_system.db: {e}")

# Try to connect to flipkart_search.db if it exists
try:
    conn = sqlite3.connect('flipkart_search.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('\nTables in flipkart_search.db:')
    if tables:
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("No tables found")
    conn.close()
except Exception as e:
    print(f"Error connecting to flipkart_search.db: {e}")
