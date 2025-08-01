"""
Flipkart Grid 7.0 Search API Usage Examples

This script demonstrates how to use the Flipkart Grid 7.0 Search API, showing various search scenarios
including basic search, filtered search, and autosuggest functionality.
"""
import requests
import json
import time
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

def pretty_print_json(data: Dict[str, Any]) -> None:
    """Print formatted JSON data"""
    print(json.dumps(data, indent=2))

def search(
    query: str, 
    category: Optional[str] = None,
    brands: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort: str = "relevance",
    page: int = 1,
    per_page: int = 24
) -> Dict[str, Any]:
    """
    Perform a search using the API
    
    Args:
        query: Search query text
        category: Optional category filter
        brands: Optional list of brand filters
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        min_rating: Optional minimum rating filter
        sort: Sort order (relevance, price_low_to_high, etc.)
        page: Page number
        per_page: Results per page
    
    Returns:
        Search results as a dictionary
    """
    # Build query parameters
    params = {
        "query": query,
        "page": page,
        "per_page": per_page,
        "sort": sort
    }
    
    # Add optional filters if provided
    if category:
        params["category"] = category
    
    if brands:
        params["brands"] = ",".join(brands)
    
    if min_price is not None:
        params["min_price"] = min_price
    
    if max_price is not None:
        params["max_price"] = max_price
    
    if min_rating is not None:
        params["min_rating"] = min_rating
    
    # Make API request
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/search", params=params)
    request_time = time.time() - start_time
    
    # Check for success
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Search successful: {len(results['products'])} results")
        print(f"⏱️ API request time: {request_time:.3f}s, Search time: {results['search_time_ms']/1000:.3f}s")
        return results
    else:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return {}

def get_suggestions(query: str, limit: int = 10) -> List[str]:
    """
    Get query suggestions for a partial query
    
    Args:
        query: Partial query text
        limit: Maximum number of suggestions
        
    Returns:
        List of query suggestions
    """
    params = {
        "query": query,
        "limit": limit
    }
    
    response = requests.get(f"{BASE_URL}/suggest", params=params)
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Got {len(results['suggestions'])} suggestions for '{query}'")
        return results["suggestions"]
    else:
        print(f"❌ Autosuggest failed: {response.status_code}")
        print(response.text)
        return []

def display_product_results(results: Dict[str, Any], show_scores: bool = False) -> None:
    """
    Display search results in a readable format
    
    Args:
        results: Search API response
        show_scores: Whether to show search scores
    """
    if not results or "products" not in results:
        print("No results to display")
        return
    
    print(f"\n📊 Search Results: {results['total_results']} total, Page {results['current_page']} of {results['total_pages']}")
    
    # Display products
    for i, product in enumerate(results["products"], 1):
        print(f"\n{i}. {product['name']}")
        print(f"   Brand: {product['brand']} | Category: {product['category']}")
        print(f"   Price: ₹{product['price']:.2f}" + (f" (MRP: ₹{product['mrp']:.2f}, {product['discount_percentage']}% off)" if product.get('mrp') else ""))
        print(f"   Rating: {product['rating']}★ ({product['rating_count']} reviews)")
        
        # Show offers if available
        if product.get('offers'):
            print(f"   Offers: {', '.join(product['offers'][:2])}" + (" + more" if len(product['offers']) > 2 else ""))
        
        # Show scores if requested
        if show_scores:
            print(f"   Scores: Semantic={product.get('semantic_score', 0):.3f}, "
                  f"Lexical={product.get('lexical_score', 0):.3f}, "
                  f"Combined={product.get('combined_score', 0):.3f}, "
                  f"Business={product.get('business_score', 0):.3f}")
    
    # Display filter information
    print("\n🔍 Available Filters:")
    
    # Categories
    if results["filters"]["categories"]:
        print("  Categories:")
        for cat in results["filters"]["categories"][:5]:
            print(f"    • {cat['name']} ({cat['count']})")
    
    # Brands
    if results["filters"]["brands"]:
        print("  Brands:")
        for brand in results["filters"]["brands"][:5]:
            print(f"    • {brand['name']} ({brand['count']})")
    
    # Price range
    price_range = results["filters"]["price_range"]
    print(f"  Price Range: ₹{price_range['min']:.2f} - ₹{price_range['max']:.2f}")
    
    # Rating counts
    if results["filters"]["rating_counts"]:
        print("  Ratings:")
        for stars, count in results["filters"]["rating_counts"].items():
            print(f"    • {stars}★: {count}")
    
    # Related searches
    if results.get("related_searches"):
        print("\n🔎 Related Searches:")
        for i, rel in enumerate(results["related_searches"], 1):
            print(f"  {i}. {rel}")

def visualize_search_results(results: Dict[str, Any], query: str) -> None:
    """
    Create visualizations of search results
    
    Args:
        results: Search API response
        query: Search query text
    """
    if not results or "products" not in results:
        print("No results to visualize")
        return
    
    # Convert products to DataFrame
    products_df = pd.DataFrame([
        {
            "name": p["name"],
            "brand": p["brand"],
            "category": p["category"],
            "price": p["price"],
            "rating": p["rating"],
            "discount": p.get("discount_percentage", 0),
            "combined_score": p.get("combined_score", 0),
            "business_score": p.get("business_score", 0)
        }
        for p in results["products"]
    ])
    
    # Set up the figure
    plt.figure(figsize=(15, 10))
    plt.suptitle(f"Search Results Analysis: '{query}'", fontsize=16)
    
    # 1. Price distribution
    plt.subplot(2, 2, 1)
    sns.histplot(data=products_df, x="price", bins=10, kde=True)
    plt.title("Price Distribution")
    plt.xlabel("Price (₹)")
    plt.ylabel("Count")
    
    # 2. Rating distribution
    plt.subplot(2, 2, 2)
    sns.countplot(y=products_df["rating"].round(0).astype(int))
    plt.title("Rating Distribution")
    plt.xlabel("Count")
    plt.ylabel("Rating (★)")
    
    # 3. Top brands
    plt.subplot(2, 2, 3)
    brand_counts = products_df["brand"].value_counts().head(5)
    sns.barplot(x=brand_counts.values, y=brand_counts.index)
    plt.title("Top Brands")
    plt.xlabel("Count")
    plt.tight_layout()
    
    # 4. Price vs Rating scatter
    plt.subplot(2, 2, 4)
    sns.scatterplot(x="price", y="rating", hue="brand", data=products_df)
    plt.title("Price vs Rating")
    plt.xlabel("Price (₹)")
    plt.ylabel("Rating (★)")
    
    plt.tight_layout(rect=(0, 0.03, 1, 0.95))
    plt.show()

if __name__ == "__main__":
    print("=" * 80)
    print("Flipkart Grid 7.0 Search API Demo")
    print("=" * 80)
    
    # Test autosuggest
    print("\n🔍 Testing Autosuggest\n" + "-" * 40)
    suggestions = get_suggestions("smart")
    if suggestions:
        print("Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    
    # Test basic search
    print("\n🔍 Testing Basic Search\n" + "-" * 40)
    basic_results = search("smartphone", per_page=10)
    display_product_results(basic_results)
    
    # Test category filter
    print("\n🔍 Testing Category Filter\n" + "-" * 40)
    category_results = search("smartphone", category="Mobile Phones", per_page=10)
    display_product_results(category_results)
    
    # Test price filter
    print("\n🔍 Testing Price Filter\n" + "-" * 40)
    price_results = search("smartphone", min_price=15000, max_price=25000, per_page=10)
    display_product_results(price_results)
    
    # Test brand filter
    print("\n🔍 Testing Brand Filter\n" + "-" * 40)
    brand_results = search("smartphone", brands=["Samsung", "Xiaomi"], per_page=10)
    display_product_results(brand_results)
    
    # Test sorting
    print("\n🔍 Testing Price Sorting\n" + "-" * 40)
    sorted_results = search("smartphone", sort="price_low_to_high", per_page=10)
    display_product_results(sorted_results)
    
    # Test combined filters
    print("\n🔍 Testing Combined Filters\n" + "-" * 40)
    combined_results = search(
        "smartphone", 
        category="Mobile Phones",
        min_price=20000,
        max_price=30000,
        min_rating=4.0,
        sort="rating",
        per_page=10
    )
    display_product_results(combined_results, show_scores=True)
    
    # Visualize results
    print("\n📊 Creating Visualizations\n" + "-" * 40)
    try:
        visualize_search_results(combined_results, "smartphone")
    except Exception as e:
        print(f"Error creating visualizations: {str(e)}")
    
    print("\n✅ Demo completed successfully!")
