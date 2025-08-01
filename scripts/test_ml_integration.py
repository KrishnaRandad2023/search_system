"""
Test the integrated ML components with sample data
"""

import asyncio
import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent.parent))

async def test_ml_integration():
    """Test our ML service integration"""
    print("🧪 Testing ML Integration...")
    
    # Test ML Service
    try:
        from app.services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        if ml_service.is_ml_available():
            print("✅ ML Service is available")
            
            # Test with sample products
            sample_products = [
                {
                    'title': 'HP Laptop 15-dy1036nr',
                    'brand': 'HP',
                    'category': 'Electronics',
                    'price': 599.99,
                    'rating': 4.2,
                    'num_ratings': 150,
                    'is_bestseller': False,
                    'stock': 10,
                    'discount_percentage': 15
                },
                {
                    'title': 'Dell Inspiron 3000',
                    'brand': 'Dell',
                    'category': 'Electronics',
                    'price': 449.99,
                    'rating': 4.0,
                    'num_ratings': 89,
                    'is_bestseller': True,
                    'stock': 5,
                    'discount_percentage': 20
                },
                {
                    'title': 'MacBook Air M1',
                    'brand': 'Apple',
                    'category': 'Electronics',
                    'price': 999.99,
                    'rating': 4.8,
                    'num_ratings': 500,
                    'is_bestseller': True,
                    'stock': 3,
                    'discount_percentage': 5
                }
            ]
            
            # Test ranking
            ranked_products = ml_service.rank_products(sample_products, "laptop hp")
            
            print("📊 Ranking Results:")
            for i, product in enumerate(ranked_products[:3]):
                score = product.get('ml_score', product.get('simple_score', 0))
                method = product.get('ranking_method', 'unknown')
                print(f"  {i+1}. {product['title']} - Score: {score:.3f} ({method})")
            
            print("✅ ML Ranking working!")
        else:
            print("⚠️ ML Service available but components not fully loaded")
            
    except Exception as e:
        print(f"❌ ML Service error: {e}")
    
    # Test Trie Autosuggest
    try:
        from app.services.autosuggest_service import get_trie_autosuggest
        trie_autosuggest = get_trie_autosuggest()
        
        # Test suggestions
        suggestions = trie_autosuggest.get_suggestions("lap", 5)
        
        print(f"\n🔍 Autosuggest Results for 'lap':")
        for sugg in suggestions:
            print(f"  - {sugg.text} ({sugg.suggestion_type}, score: {sugg.score:.2f})")
        
        if suggestions:
            print("✅ Trie Autosuggest working!")
        else:
            print("⚠️ Trie Autosuggest working but no suggestions (no data)")
            
    except Exception as e:
        print(f"❌ Trie Autosuggest error: {e}")
    
    # Test Spell Checker
    try:
        from app.utils.spell_checker import check_spelling
        
        corrected, has_correction = check_spelling("leptop")
        print(f"\n📝 Spell Correction Test:")
        print(f"  Original: 'leptop'")
        print(f"  Corrected: '{corrected}' (has_correction: {has_correction})")
        
        if has_correction:
            print("✅ Spell correction working!")
        else:
            print("⚠️ Spell correction available but no correction needed/found")
            
    except Exception as e:
        print(f"❌ Spell correction error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ml_integration())
