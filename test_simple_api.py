"""
Test client for the simple API
"""

import requests
import json
import sys

# Constants
API_URL = "http://localhost:8001"

def search_products(query, limit=10, page=1):
    """Search products via the API using the v2 endpoint that the frontend expects"""
    response = requests.get(
        f"{API_URL}/api/v2/search",
        params={"q": query, "limit": limit, "page": page, "per_page": limit}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_product(product_id):
    """Get a product by ID"""
    response = requests.get(f"{API_URL}/api/products/{product_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_categories():
    """Get all categories"""
    response = requests.get(f"{API_URL}/api/categories")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_autosuggest(query, limit=10):
    """Get autosuggest recommendations using the endpoint the frontend expects"""
    response = requests.get(
        f"{API_URL}/api/v1/metadata/autosuggest",
        params={"q": query, "limit": limit}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_simple_api.py <command> [args]")
        print("Commands:")
        print("  search <query> [limit]")
        print("  product <product_id>")
        print("  categories")
        print("  autosuggest <query> [limit]")
        return
    
    command = sys.argv[1]
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Usage: python test_simple_api.py search <query> [limit]")
            return
        
        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        results = search_products(query, limit)
        if results:
            print(f"Found {results.get('total_results', 0)} results for '{query}':")
            print(f"Page {results.get('page', 1)} of {results.get('total_pages', 1)}")
            
            for i, product in enumerate(results.get('products', []), 1):
                print(f"\n{i}. {product.get('title', 'Unknown')}")
                print(f"   Brand: {product.get('brand', 'N/A')} | Category: {product.get('category', 'N/A')}")
                print(f"   Price: ₹{product.get('current_price', 0)} | Rating: {product.get('rating', 0)}")
    
    elif command == "product":
        if len(sys.argv) < 3:
            print("Usage: python test_simple_api.py product <product_id>")
            return
        
        product_id = sys.argv[2]
        product = get_product(product_id)
        if product:
            print(json.dumps(product, indent=2))
    
    elif command == "categories":
        categories = get_categories()
        if categories:
            print("Categories:")
            for category in categories['categories']:
                print(f"- {category}")
    
    elif command == "autosuggest":
        if len(sys.argv) < 3:
            print("Usage: python test_simple_api.py autosuggest <query> [limit]")
            return
        
        query = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        results = get_autosuggest(query, limit)
        if results:
            print(f"Autosuggest results for '{query}':")
            for i, suggestion in enumerate(results['suggestions'], 1):
                suggestion_type = suggestion.get('suggestion_type', 'unknown')
                text = suggestion.get('text', '')
                score = suggestion.get('score', 0)
                metadata = suggestion.get('metadata', {})
                
                print(f"{i}. {text} ({suggestion_type}, score: {score:.2f})")
                if metadata:
                    for key, value in metadata.items():
                        if value:
                            print(f"   {key}: {value}")
    
    else:
        print(f"Unknown command: {command}")
        print("Commands: search, product, categories, autosuggest")

if __name__ == "__main__":
    main()
