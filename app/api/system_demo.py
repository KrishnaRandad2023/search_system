"""
System Demo API - Showcase enhanced features
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import json
from pathlib import Path
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/v1/demo", tags=["System Demo"])

@router.get("/enhancements")
async def show_enhancements() -> Dict[str, Any]:
    """Showcase all the enhancements made to the system"""
    
    # Load enhancement report
    try:
        import sys
        sys.path.append('scripts')
        from enhancement_report import get_enhancement_report
        report = get_enhancement_report()
    except:
        report = {"error": "Could not load enhancement report"}
    
    return {
        "message": "🎯 Flipkart Grid 7.0 - Enhanced Search System",
        "enhancement_summary": report,
        "key_improvements": [
            "🚀 Amazon Lite Data: 25k+ prefix mappings + 470k+ suggestions integrated",
            "🧠 Intelligent Autosuggest: Trie-based with spell correction & ML ranking",
            "🔧 Database Admin API: Safe operations with backup/restore",
            "🏗️ Schema Enhancement: Aligned models with actual database structure",
            "⚡ Performance: <1ms autosuggest response time",
            "🛡️ Safety First: All enhancements preserve existing functionality"
        ],
        "demo_endpoints": {
            "autosuggest": "/autosuggest/?q=apple&limit=5",
            "health_check": "/api/v1/admin/database/health",
            "system_demo": "/api/v1/demo/test-amazon-data"
        }
    }

@router.get("/test-amazon-data")
async def test_amazon_data_integration() -> Dict[str, Any]:
    """Test and demonstrate Amazon lite data integration"""
    
    results = {
        "test_timestamp": datetime.utcnow().isoformat(),
        "amazon_data_status": {},
        "sample_suggestions": {},
        "integration_proof": []
    }
    
    # Check Amazon files
    amazon_files = {
        "prefix_map": Path("data/amazon_lite_prefix_map.json"),
        "suggestions": Path("data/amazon_lite_suggestions.json")
    }
    
    for name, file_path in amazon_files.items():
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                results["amazon_data_status"][name] = {
                    "available": True,
                    "count": len(data),
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    "sample_keys": list(data.keys())[:5] if isinstance(data, dict) else "N/A"
                }
                
                # Get sample suggestions for popular brands
                if name == "suggestions" and isinstance(data, list):
                    brand_samples = {}
                    for item in data[:50]:  # Check first 50 items
                        if isinstance(item, str):
                            for brand in ['apple', 'samsung', 'nike', 'adidas']:
                                if brand in item.lower() and brand not in brand_samples:
                                    brand_samples[brand] = item
                    results["sample_suggestions"] = brand_samples
                    
            except Exception as e:
                results["amazon_data_status"][name] = {
                    "available": False,
                    "error": str(e)
                }
        else:
            results["amazon_data_status"][name] = {
                "available": False,
                "error": "File not found"
            }
    
    # Test autosuggest integration
    try:
        from app.services.autosuggest_service import TrieAutosuggest
        service = TrieAutosuggest('data/flipkart_products.db')
        
        test_queries = ['apple', 'samsung', 'nike']
        for query in test_queries:
            suggestions = service.get_suggestions(query, limit=3)
            results["integration_proof"].append({
                "query": query,
                "suggestions_found": len(suggestions),
                "sample_suggestions": [s.text for s in suggestions[:2]]
            })
            
    except Exception as e:
        results["integration_proof"] = [{"error": f"Could not test autosuggest: {e}"}]
    
    return results

@router.get("/performance-stats")
async def get_performance_stats() -> Dict[str, Any]:
    """Show performance statistics of enhanced system"""
    
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "database_performance": {},
        "autosuggest_performance": {},
        "memory_usage": {}
    }
    
    # Database stats
    try:
        db_path = Path("data/flipkart_products.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Measure query performance
            import time
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM products WHERE title LIKE '%apple%'")
            result = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            stats["database_performance"] = {
                "apple_products_found": result,
                "query_time_ms": round(query_time * 1000, 2),
                "database_size_mb": round(db_path.stat().st_size / (1024 * 1024), 2)
            }
            
            conn.close()
    except Exception as e:
        stats["database_performance"] = {"error": str(e)}
    
    # Autosuggest performance
    try:
        from app.services.autosuggest_service import TrieAutosuggest
        import time
        
        service = TrieAutosuggest('data/flipkart_products.db')
        
        # Measure autosuggest performance
        test_queries = ['a', 'ap', 'app', 'appl', 'apple']
        performance_results = []
        
        for query in test_queries:
            start_time = time.time()
            suggestions = service.get_suggestions(query, limit=5)
            end_time = time.time()
            
            performance_results.append({
                "query": query,
                "suggestions_count": len(suggestions),
                "response_time_ms": round((end_time - start_time) * 1000, 2)
            })
        
        stats["autosuggest_performance"] = {
            "test_results": performance_results,
            "average_response_time_ms": round(
                sum(r["response_time_ms"] for r in performance_results) / len(performance_results), 2
            )
        }
        
    except Exception as e:
        stats["autosuggest_performance"] = {"error": str(e)}
    
    return stats
