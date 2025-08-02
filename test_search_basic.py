import asyncio
import sys
sys.path.append('.')

async def test_hybrid_search():
    try:
        print('🔍 Testing Hybrid Search System...')
        print('=' * 50)
        
        # Import required components
        import sqlite3
        
        # Test database connection
        print('📊 Testing database connection...')
        try:
            conn = sqlite3.connect('search_system.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]
            print(f'✅ Database connected: {product_count} products found')
            
            # Get a quick sample of products
            cursor.execute('SELECT product_id, title, current_price FROM products LIMIT 3')
            rows = cursor.fetchall()
            print('📦 Sample products:')
            for row in rows:
                print(f'  - {row[1]} (ID: {row[0]}, Price: ₹{row[2]})')
            
            conn.close()
        except Exception as e:
            print(f'❌ Database error: {e}')
            return
        
        # Initialize the search service
        print('\n🔍 Testing search functionality...')
        print('=' * 50)
        
        try:
            # First, test direct database search for baseline
            print('📊 Testing direct database search...')
            conn = sqlite3.connect('search_system.db')
            cursor = conn.cursor()
            
            search_term = 'smartphone'
            cursor.execute(f"SELECT product_id, title, current_price FROM products WHERE title LIKE '%{search_term}%' OR description LIKE '%{search_term}%' LIMIT 5")
            rows = cursor.fetchall()
            
            print(f'✅ Direct search for "{search_term}" found {len(rows)} products:')
            for row in rows:
                print(f'  - {row[1]} (ID: {row[0]}, Price: ₹{row[2]})')
            
            conn.close()
        except Exception as e:
            print(f'❌ Error in direct search: {e}')
        
        # Now check for the API endpoints
        print('\n🌐 Testing API endpoints...')
        print('=' * 50)
        
        try:
            from app.main import app
            print(f'✅ FastAPI application loaded: {app.title}')
            
            import importlib
            
            # Check search endpoints
            search_endpoints = [
                'app.api.search_v2',
                'app.api.hybrid_api'
            ]
            
            for endpoint in search_endpoints:
                try:
                    module = importlib.import_module(endpoint)
                    print(f'✅ Successfully imported {endpoint}')
                except Exception as e:
                    print(f'❌ Failed to import {endpoint}: {e}')
        
        except Exception as e:
            print(f'❌ Error checking API endpoints: {e}')
        
        print('\n🎉 Test Complete!')
        print('=' * 50)
        
    except Exception as e:
        print(f'❌ Critical error in test: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_hybrid_search())
