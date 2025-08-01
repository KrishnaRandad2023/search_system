"""
ML Package for Flipkart Grid 7.0 Search System
=============================================

This package contains machine learning components for the search system:

- MLRanker: XGBoost-based ranking model for reordering search results
- Preprocessor: Text preprocessing and feature extraction utilities
- Feature Engineering: Advanced feature extraction for ML models

Usage:
    from app.ml.ranker import MLRanker
    from app.ml.preprocessor import TextPreprocessor
"""

# Import core ML components for easier access
try:
    from .ranker import MLRanker
    from .preprocessor import TextPreprocessor
    
    __all__ = [
        'MLRanker',
        'TextPreprocessor',
    ]
    
except ImportError as e:
    # Graceful fallback if dependencies are missing
    import warnings
    warnings.warn(f"Some ML components could not be imported: {e}")
    __all__ = []
