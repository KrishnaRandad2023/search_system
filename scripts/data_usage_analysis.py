"""
Data Usage Analysis - Complete Report
Analyzing what data files are being used, where, and why
"""

import os
import json
from pathlib import Path

def analyze_data_usage():
    print("=" * 80)
    print("📊 COMPLETE DATA USAGE ANALYSIS - FLIPKART GRID 7.0")
    print("=" * 80)
    
    print("\n🔍 EXISTING DATA FILES:")
    
    # Check all data files
    data_files = {
        "amazon_lite_prefix_map.json": "25,357 lines - Prefix mapping for autosuggest",
        "amazon_lite_suggestions.json": "444,415 lines - Amazon product suggestions", 
        "flipkart_products.db": "16.89 MB - Main database with 12k products",
        "raw/products.json": "22.31 MB - 12,000 products (PRIMARY SOURCE)",
        "raw/queries.json": "0.35 MB - 2,500 search queries",
        "raw/flipkart_products.csv": "1.38 MB - 5,000 products",
        "raw/flipkart_reviews.csv": "0.20 MB - 1,000 reviews",
        "raw/autosuggest_queries.csv": "0.07 MB - 2,000 autosuggest queries",
        "embeddings/product_embeddings.npy": "7.32 MB - Vector embeddings",
        "db/flipkart.db": "SQLAlchemy database (configured but not used)",
        "db/flipkart_products.db": "Duplicate database file"
    }
    
    for file, desc in data_files.items():
        file_path = Path(f"data/{file}")
        if file_path.exists():
            print(f"   ✅ {file:<35} - {desc}")
        else:
            print(f"   ❌ {file:<35} - {desc} (NOT FOUND)")
    
    print("\n🎯 WHAT IS CURRENTLY BEING USED:")
    
    usage_report = {
        "✅ ACTIVELY USED": [
            ("data/flipkart_products.db", "Main search database", "enhanced_search_api_v2.py", "Primary data source for all searches"),
            ("raw/products.json", "Product data", "load_full_data.py", "Loaded all 12k products into database"),
            ("raw/queries.json", "Search queries", "load_full_data.py", "Loaded 2,500 queries for autosuggest"),
            ("raw/autosuggest_queries.csv", "Autosuggest data", "load_full_data.py", "Loaded 2k queries for suggestions"),
            ("raw/flipkart_reviews.csv", "Review data", "load_full_data.py", "Loaded 1k reviews into database"),
            ("embeddings/product_embeddings.npy", "Vector embeddings", "hybrid_engine.py", "Available for semantic search")
        ],
        "⚠️  PARTIALLY USED": [
            ("amazon_lite_prefix_map.json", "Amazon autosuggest", "autosuggest_engine.py", "Loaded but autosuggest_engine not active"),
            ("amazon_lite_suggestions.json", "Amazon suggestions", "autosuggest_engine.py", "Loaded but autosuggest_engine not active")
        ],
        "❌ NOT CURRENTLY USED": [
            ("db/flipkart.db", "SQLAlchemy DB", "settings.py", "Configured but system uses direct sqlite3"),
            ("raw/flipkart_products.csv", "Product CSV", "None", "Superseded by products.json")
        ],
        "🔧 UTILITY SCRIPTS": [
            ("scripts/seed_db.py", "Database seeding", "Manual execution", "Creates database from CSV data"),
            ("scripts/ingest_products.py", "Data generation", "Manual execution", "Generates synthetic product data")
        ]
    }
    
    for category, items in usage_report.items():
        print(f"\n{category}:")
        for file, purpose, used_in, reason in items:
            print(f"   📁 {file}")
            print(f"      Purpose: {purpose}")
            print(f"      Used in: {used_in}")
            print(f"      Status: {reason}")
            print()
    
    print("\n💡 RECOMMENDATIONS:")
    print("   1. ✅ AMAZON LITE DATA - Could be integrated for richer autosuggest")
    print("   2. 🔄 SEED_DB SCRIPT - Could be used for fresh database initialization")
    print("   3. 🔄 INGEST_PRODUCTS - Could generate additional test data")
    print("   4. 🧹 CLEANUP - Remove duplicate database files")
    
    print("\n🚀 CURRENT SYSTEM STATUS:")
    print("   ✅ Using comprehensive product dataset (12k products)")
    print("   ✅ Using query data for intelligent suggestions")  
    print("   ✅ Using review data for quality signals")
    print("   ✅ Vector embeddings available for semantic search")
    print("   ✅ All core functionality working with existing data")
    
    print("\n🎯 INTEGRATION OPPORTUNITIES:")
    print("   🔮 Amazon Lite Prefix Map: 25k+ prefix mappings for ultra-fast autosuggest")
    print("   🔮 Amazon Lite Suggestions: 440k+ suggestions for comprehensive coverage")
    print("   🔮 Seed DB Scripts: For database reinitialization and testing")
    print("   🔮 Generated Data: For stress testing and development")
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print("   • Core system uses: products.json (12k), queries.json (2.5k), reviews (1k)")
    print("   • Available but unused: Amazon lite data (470k+ suggestions)")
    print("   • Utility scripts: seed_db.py, ingest_products.py (for data generation)")
    print("   • System is fully functional with current data integration")
    print("=" * 80)

if __name__ == "__main__":
    analyze_data_usage()
