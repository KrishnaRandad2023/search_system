"""
ML Components Initialization and Health Check
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ml_components():
    """Check which ML components are available"""
    status = {
        "ml_service": False,
        "trie_autosuggest": False,
        "hybrid_engine": False,
        "ml_ranker": False,
        "spell_checker": False
    }
    
    # Check ML Service
    try:
        from app.services.ml_service import get_ml_service
        ml_service = get_ml_service()
        status["ml_service"] = True
        logger.info("✅ ML Service available")
        
        if ml_service.is_ml_available():
            logger.info("✅ ML components initialized")
        else:
            logger.info("⚠️ ML Service created but components not fully available")
            
    except Exception as e:
        logger.warning(f"❌ ML Service not available: {e}")
    
    # Check Trie Autosuggest
    try:
        from app.services.autosuggest_service import get_trie_autosuggest
        trie_autosuggest = get_trie_autosuggest()
        status["trie_autosuggest"] = True
        logger.info("✅ Trie Autosuggest available")
    except Exception as e:
        logger.warning(f"❌ Trie Autosuggest not available: {e}")
    
    # Check Hybrid Engine directly
    try:
        from app.search.hybrid_engine import HybridSearchEngine
        status["hybrid_engine"] = True
        logger.info("✅ Hybrid Search Engine class available")
    except Exception as e:
        logger.warning(f"❌ Hybrid Search Engine not available: {e}")
    
    # Check ML Ranker directly
    try:
        from app.ml.ranker import MLRanker
        status["ml_ranker"] = True
        logger.info("✅ ML Ranker class available")
    except Exception as e:
        logger.warning(f"❌ ML Ranker not available: {e}")
    
    # Check Spell Checker
    try:
        from app.utils.spell_checker import check_spelling
        status["spell_checker"] = True
        logger.info("✅ Spell Checker available")
    except Exception as e:
        logger.warning(f"❌ Spell Checker not available: {e}")
    
    return status

def initialize_ml_data():
    """Initialize any required ML data/models"""
    logger.info("Initializing ML data...")
    
    # Check for required data directories
    data_dir = Path("data")
    if not data_dir.exists():
        logger.warning("Data directory not found, creating...")
        data_dir.mkdir(exist_ok=True)
        (data_dir / "raw").mkdir(exist_ok=True)
        (data_dir / "embeddings").mkdir(exist_ok=True)
    
    # Check for products data
    products_file = data_dir / "raw" / "products.json"
    if not products_file.exists():
        logger.warning("Products data not found - some ML features may not work optimally")
    else:
        logger.info("✅ Products data found")
    
    logger.info("ML data initialization complete")

if __name__ == "__main__":
    print("🔍 Checking ML Components...")
    status = check_ml_components()
    
    print("\n📊 Component Status:")
    for component, available in status.items():
        icon = "✅" if available else "❌"
        print(f"  {icon} {component}: {'Available' if available else 'Not Available'}")
    
    print("\n🚀 Initializing ML Data...")
    initialize_ml_data()
    
    available_count = sum(status.values())
    total_count = len(status)
    
    print(f"\n📈 Summary: {available_count}/{total_count} components available")
    
    if available_count == total_count:
        print("🎉 All ML components are ready!")
    elif available_count > 0:
        print("⚠️ Some ML components available - system will work with graceful fallbacks")
    else:
        print("🔧 No ML components available - system will use basic functionality")
