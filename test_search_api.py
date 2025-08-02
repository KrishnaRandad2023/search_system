"""
Flipkart Search System - API Test Client

This script tests the search API with various queries to verify
that the diverse product data we added works correctly.
"""

import requests
import json
import time
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Configuration
API_URL = "http://localhost:8000/search"
QUERIES = [
    "shoes",
    "laptop",
    "smartphone",
    "headphones",
    "t-shirt",
    "furniture",
    "kitchen",
    "toys",
    "beauty products",
    "sports equipment",
    "camera",
    "watch",
    "home decor",
    "books",
    "baby products"
]

def test_search(query, limit=5):
    """Test search with the given query"""
    params = {
        "q": query,
        "limit": limit,
        "include_ml": "true"
    }
    
    try:
        start_time = time.time()
        response = requests.get(API_URL, params=params)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get("products", []))
            
            # Print results
            console = Console()
            
            # Create a nice header
            console.print(f"\n[bold blue]Search Results for [yellow]'{query}'[/yellow][/bold blue]")
            console.print(f"Found [bold green]{result_count}[/bold green] products in [bold cyan]{elapsed_time:.2f}ms[/bold cyan]")
            
            if result_count > 0:
                # Create a table
                table = Table(show_header=True, header_style="bold")
                table.add_column("Title", width=40)
                table.add_column("Category", width=20)
                table.add_column("Price", justify="right")
                table.add_column("Rating", justify="center")
                
                for product in data.get("products", [])[:limit]:
                    # Format price with currency symbol
                    price = f"₹{product.get('current_price', 0):,.2f}"
                    
                    # Format rating with stars
                    rating = product.get('rating', 0)
                    rating_str = f"{rating:.1f}★" if rating else "N/A"
                    
                    table.add_row(
                        product.get('title', 'N/A'), 
                        f"{product.get('category', 'N/A')} > {product.get('subcategory', 'N/A')}", 
                        price,
                        rating_str
                    )
                
                console.print(table)
            else:
                console.print("[bold red]No products found[/bold red]")
            
            return {
                "query": query,
                "status": "success",
                "result_count": result_count,
                "elapsed_time_ms": elapsed_time
            }
        else:
            rprint(f"[bold red]Error: {response.status_code}[/bold red]")
            rprint(response.text)
            return {
                "query": query,
                "status": "error",
                "status_code": response.status_code,
                "message": response.text
            }
    
    except Exception as e:
        rprint(f"[bold red]Exception: {str(e)}[/bold red]")
        return {
            "query": query,
            "status": "exception",
            "message": str(e)
        }

def main():
    """Main function to test all queries"""
    print("\n" + "=" * 80)
    print("🔍 FLIPKART SEARCH SYSTEM - API TEST")
    print("=" * 80)
    
    results = []
    
    # Test each query
    for query in QUERIES:
        result = test_search(query)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SEARCH PERFORMANCE SUMMARY")
    print("=" * 80)
    
    summary_data = []
    for result in results:
        if result["status"] == "success":
            summary_data.append([
                result["query"],
                result["result_count"],
                f"{result['elapsed_time_ms']:.2f}ms"
            ])
    
    print(tabulate(summary_data, headers=["Query", "Results", "Response Time"], tablefmt="grid"))
    
    # Success criteria
    successful_queries = sum(1 for r in results if r["status"] == "success" and r["result_count"] > 0)
    print(f"\n✅ {successful_queries}/{len(QUERIES)} queries returned results successfully")
    
    if successful_queries == len(QUERIES):
        print("\n🎉 All searches returned results successfully!")
        print("The diverse product data has been successfully integrated.")
    else:
        print("\n⚠️ Some searches did not return results.")

if __name__ == "__main__":
    main()
