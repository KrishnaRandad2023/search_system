import asyncio
import sys
sys.path.append('.')

async def test_hybrid_search():
    try:
        print('🔍 Testing Hybrid Search System...')
        print('=' * 50)
        
        # Import required components
        from app.services.smart_search_service import SmartSearchService
        from app.db.database import get_db
        from app.db.models import Product
        import sqlite3
        
        # Test database connection
        print('📊 Testing database connection...')
        try:
            conn = sqlite3.connect('search_system.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]
            print(f'✅ Database connected: {product_count} products found')
            conn.close()
        except Exception as e:
            print(f'❌ Database error: {e}')
            return
        
        # Initialize the hybrid search service
        print('🤖 Initializing SmartSearchService with hybrid capabilities...')
        search_service = SmartSearchService()
        print('✅ SmartSearchService initialized successfully')
        
        # Test search queries
        test_queries = [
            'smartphone',
            'laptop gaming',
            'headphones wireless',
            'mobile phone under 15000'
        ]
        
        print('🔍 Testing search queries...')
        for query in test_queries:
            print(f'\n📱 Testing query: "{query}"')
            try:
                # Test with hybrid enhancement enabled (default)
                results = await search_service.search_products(
                    query=query,
                    limit=5,
                    use_hybrid_enhancement=True
                )
                
                if results and 'products' in results and results['products']:
                    print(f'  ✅ Found {len(results["products"])} products with hybrid search')
                    for i, product in enumerate(results['products'][:3], 1):
                        title = product.get('title', 'Unknown')[:50]
                        price = product.get('price', 'N/A')
                        print(f'    {i}. {title}... - ₹{price}')
                else:
                    print('  ⚠️ No products found')
                    
            except Exception as e:
                print(f'  ❌ Error in search: {e}')
        
        # Test baseline vs hybrid comparison
        print('\n🔄 Testing Baseline vs Hybrid Enhancement...')
        test_query = 'smartphone'
        
        try:
            # Test baseline only
            baseline_results = await search_service.search_products(
                query=test_query,
                limit=3,
                use_hybrid_enhancement=False
            )
            
            # Test with hybrid enhancement
            hybrid_results = await search_service.search_products(
                query=test_query,
                limit=3,
                use_hybrid_enhancement=True
            )
            
            baseline_count = len(baseline_results.get('products', [])) if baseline_results else 0
            hybrid_count = len(hybrid_results.get('products', [])) if hybrid_results else 0
            
            print(f'  📊 Baseline search results: {baseline_count}')
            print(f'  🚀 Hybrid enhanced results: {hybrid_count}')
            
            if hybrid_count >= baseline_count:
                print('  ✅ Hybrid enhancement working correctly')
            else:
                print('  ⚠️ Hybrid enhancement may need adjustment')
                
        except Exception as e:
            print(f'  ❌ Error in comparison test: {e}')
        
        print('\n🎉 Hybrid Search System Test Complete!')
        print('=' * 50)
        
    except Exception as e:
        print(f'❌ Critical error in test: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_hybrid_search())
