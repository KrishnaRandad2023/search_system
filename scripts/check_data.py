"""
Check existing data in the project
"""

import json
import pandas as pd
from pathlib import Path
import os

def check_file(file_path, file_type="unknown"):
    """Check if file exists and get its size"""
    path = Path(file_path)
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"✅ {file_type} exists ({size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ {file_type} not found")
        return False

def check_json_file(file_path, name="JSON"):
    """Check JSON file and its contents"""
    if not check_file(file_path, name):
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            print(f"  - Contains {len(data)} items")
            if data:
                print(f"  - First item keys: {list(data[0].keys())}")
        elif isinstance(data, dict):
            print(f"  - Contains {len(data)} keys")
            print(f"  - Keys: {list(data.keys())}")
        
        return data
    except Exception as e:
        print(f"  - Error reading {name}: {e}")
        return None

def check_csv_file(file_path, name="CSV"):
    """Check CSV file and its contents"""
    if not check_file(file_path, name):
        return
    
    try:
        df = pd.read_csv(file_path)
        print(f"  - Contains {len(df)} rows and {len(df.columns)} columns")
        print(f"  - Columns: {df.columns.tolist()[:5]}...")
        return df
    except Exception as e:
        print(f"  - Error reading {name}: {e}")
        return None

def main():
    print("=== Checking Existing Data ===\n")
    
    # Check raw data files
    data_dir = Path("data/raw")
    print("Raw data files:")
    
    products_json = check_json_file(data_dir / "products.json", "Products JSON")
    queries_json = check_json_file(data_dir / "queries.json", "Queries JSON")
    
    products_csv = check_csv_file(data_dir / "flipkart_products.csv", "Products CSV")
    reviews_csv = check_csv_file(data_dir / "flipkart_reviews.csv", "Reviews CSV")
    autosuggest_csv = check_csv_file(data_dir / "autosuggest_queries.csv", "Autosuggest CSV")
    
    # Check database
    print("\nDatabase:")
    check_file("data/flipkart_products.db", "SQLite database")
    
    # Check embeddings
    print("\nEmbeddings:")
    embeddings_dir = Path("data/embeddings")
    if embeddings_dir.exists():
        embedding_files = list(embeddings_dir.glob("*.npy"))
        print(f"✅ Embeddings directory exists with {len(embedding_files)} files")
        for file in embedding_files[:3]:
            check_file(file, f"Embedding file {file.name}")
    else:
        print("❌ Embeddings directory not found")
    
    print("\n=== Data Check Complete ===")

if __name__ == "__main__":
    main()
