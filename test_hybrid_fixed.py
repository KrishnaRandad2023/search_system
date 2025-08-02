import requests

def test_hybrid_search(query, use_ml=True, ml_weight=None):
    print(f'\n🔍 Testing Hybrid Search: "{query}" (use_ml={use_ml}, ml_weight={ml_weight})')
    
    # Use POST request with JSON body for full hybrid search
    if use_ml:
        payload = {
            'query': query,
            'page': 1,
            'limit': 5,
            'use_ml': use_ml
        }
        
        if ml_weight is not None:
            payload['ml_weight'] = ml_weight
        
        try:
            response = requests.post('http://localhost:8000/api/v1/hybrid/search', json=payload)
        except Exception as e:
            print(f'❌ Error: {str(e)}')
            return
    else:
        # Use GET request for smart-only search
        params = {
            'query': query,
            'page': 1,
            'limit': 5
        }
        try:
            response = requests.get('http://localhost:8000/api/v1/hybrid/smart-search', params=params)
        except Exception as e:
            print(f'❌ Error: {str(e)}')
            return
    
    # Process response (common for both POST and GET)
    try:
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Search successful: {len(data.get("products", []))} results')
            print(f'   Method used: {data.get("query_analysis", {}).get("search_method", "unknown")}')
            print(f'   Response time: {data.get("response_time_ms", 0)}ms')
            
            if data.get('products'):
                print('\n   Top results:')
                for i, product in enumerate(data.get('products')[:3], 1):
                    print(f'   {i}. {product.get("name")} - ₹{product.get("price")}')
            
            print(f'\n   Query Analysis:')
            analysis = data.get('query_analysis', {})
            for key, value in analysis.items():
                if key not in ['search_method', 'search_time_ms']:
                    print(f'   - {key}: {value}')
                    
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    
    except Exception as e:
        print(f'❌ Error processing response: {str(e)}')

def test_hybrid_analyze(query):
    print(f'\n🧠 Testing Hybrid Analysis: "{query}"')
    
    try:
        response = requests.get(f'http://localhost:8000/api/v1/hybrid/analyze-simple?query={query}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Analysis successful')
            print(f'   Processing method: {data.get("processing_method", "unknown")}')
            print(f'   Response time: {data.get("response_time_ms", 0)}ms')
            print(f'   Hybrid confidence: {data.get("hybrid_confidence", 0)}')
            
            print('\n   Smart Analysis:')
            smart = data.get('smart_analysis', {})
            for key, value in smart.items():
                print(f'   - {key}: {value}')
            
            if data.get('ml_analysis'):
                print('\n   ML Analysis:')
                ml = data.get('ml_analysis', {})
                semantic_intent = ml.get('semantic_intent', {})
                print(f'   - semantic_category: {semantic_intent.get("semantic_category", "unknown")}')
                print(f'   - intent_strength: {semantic_intent.get("intent_strength", 0)}')
                print(f'   - semantic_confidence: {ml.get("semantic_confidence", 0)}')
                
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    
    except Exception as e:
        print(f'❌ Error: {str(e)}')

def test_hybrid_suggest(query):
    print(f'\n💡 Testing Hybrid Suggestions: "{query}"')
    
    try:
        response = requests.get(f'http://localhost:8000/api/v1/hybrid/autosuggest?query={query}&limit=6')
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Suggestions successful: {len(data.get("suggestions", []))} results')
            print(f'   Response time: {data.get("response_time_ms", 0)}ms')
            
            if data.get('suggestions'):
                print('\n   Suggestions:')
                for i, suggestion in enumerate(data.get('suggestions'), 1):
                    print(f'   {i}. {suggestion.get("text")} ({suggestion.get("type")}: {suggestion.get("popularity")})')
                    
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    
    except Exception as e:
        print(f'❌ Error: {str(e)}')

if __name__ == "__main__":
    print("🚀 Testing Hybrid ML Search System")
    print("=" * 50)
    
    # Test different queries with hybrid search
    test_hybrid_search('smartphone under 20000')
    test_hybrid_search('best laptop', use_ml=True)
    test_hybrid_search('wireless headphones', use_ml=True, ml_weight=0.8)
    
    # Test query analysis
    test_hybrid_analyze('apple iphone 13 pro max')
    
    # Test autosuggest
    test_hybrid_suggest('lap')
    
    print("\n" + "=" * 50)
    print("🎯 Hybrid ML Search System Testing Complete!")
