"""
Query Analyzer Service - Advanced Query Understanding

This service provides:
1. Query intent analysis
2. Price range extraction
3. Category/product type identification
4. Brand recognition
5. Sentiment analysis
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Product, AutosuggestQuery, SearchLog

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Results of analyzing a search query"""
    original_query: str
    normalized_query: str
    query_type: str  # 'product', 'brand', 'category', 'price_range', 'mixed'
    entities: Dict[str, Any]  # Extracted entities like brand, product_type, etc.
    price_range: Optional[Tuple[Optional[float], Optional[float]]] = None  # min, max
    brands: List[str] = None  # type: ignore  # Will be initialized in post_init
    categories: List[str] = None  # type: ignore  # Will be initialized in post_init
    sentiment: str = "neutral"  # 'positive', 'negative', 'neutral'
    modifiers: List[str] = None  # type: ignore  # Will be initialized in post_init
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.brands is None:
            self.brands = []
        if self.categories is None:
            self.categories = []
        if self.modifiers is None:
            self.modifiers = []


class QueryAnalyzerService:
    """
    Advanced query understanding for ecommerce search
    - Pattern-based entity extraction
    - Price range detection
    - Brand and category recognition
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.patterns = self._load_patterns()
        self.brands = self._load_brands()
        self.categories = self._load_categories()
        self.common_price_ranges = self._load_price_ranges()
        self.modifier_terms = {
            'best': 10, 'top': 9, 'cheap': 8, 'budget': 7,
            'latest': 10, 'new': 8, 'high end': 9, 'premium': 10,
            'gaming': 9, 'professional': 8, 'entry level': 7
        }
        
        # Basic sentiment terms (could be expanded with ML models)
        self.positive_terms = {'best', 'great', 'excellent', 'good', 'top', 'premium', 'quality'}
        self.negative_terms = {'cheap', 'bad', 'worst', 'avoid', 'poor'}
        
        logger.info("QueryAnalyzerService initialized")
        
    def _load_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load regex patterns for query analysis"""
        patterns = {
            'price_range': [
                # "X under Y" pattern
                re.compile(r'(\w+)\s+under\s+(\d+)k?'),
                # "under X" pattern
                re.compile(r'under\s+(\d+)k?'),
                # "X-Y range" pattern
                re.compile(r'(\d+)k?\s*-\s*(\d+)k?'),
                # "less than X" pattern
                re.compile(r'less\s+than\s+(\d+)k?'),
                # "budget X" pattern
                re.compile(r'budget\s+(\w+)')
            ],
            'product_type': [
                re.compile(r'(mobile|phone|smartphone|laptop|tablet|camera|headphone|earphone|tv|watch)', re.IGNORECASE)
            ]
        }
        return patterns
    
    def _load_brands(self) -> List[str]:
        """Load known brand names - ideally from database"""
        # Default fallback if db not available
        default_brands = [
            'samsung', 'apple', 'xiaomi', 'oneplus', 'realme', 'vivo', 'oppo',
            'hp', 'dell', 'lenovo', 'asus', 'acer', 'msi', 'microsoft',
            'sony', 'lg', 'panasonic', 'boat', 'jbl', 'noise'
        ]
        
        if self.db:
            try:
                # Get brands from database
                brands = self.db.query(Product.brand).distinct().all()
                return [brand[0].lower() for brand in brands if brand[0]]
            except Exception as e:
                logger.error(f"Error loading brands from database: {e}")
                return default_brands
        else:
            return default_brands
    
    def _load_categories(self) -> List[str]:
        """Load product categories - ideally from database"""
        # Default fallback if db not available
        default_categories = [
            'mobile', 'laptop', 'electronics', 'audio', 'camera',
            'tv', 'appliance', 'wearable', 'tablet', 'accessory'
        ]
        
        if self.db:
            try:
                # Get categories from database
                categories = self.db.query(Product.category).distinct().all()
                return [cat[0].lower() for cat in categories if cat[0]]
            except Exception as e:
                logger.error(f"Error loading categories from database: {e}")
                return default_categories
        else:
            return default_categories
    
    def _load_price_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Define common price ranges for different product categories"""
        return {
            'budget_mobile': (0.0, 10000.0),
            'mid_range_mobile': (10000.0, 25000.0),
            'premium_mobile': (25000.0, 50000.0),
            'flagship_mobile': (50000.0, float('inf')),
            
            'budget_laptop': (0.0, 30000.0),
            'mid_range_laptop': (30000.0, 60000.0),
            'premium_laptop': (60000.0, 100000.0),
            'high_end_laptop': (100000.0, float('inf')),
            
            'budget_tv': (0.0, 20000.0),
            'mid_range_tv': (20000.0, 50000.0),
            'premium_tv': (50000.0, float('inf')),
            
            # Add more product categories as needed
        }
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Main method to analyze a search query
        Returns QueryAnalysis with extracted information
        """
        query_lower = query.lower().strip()
        
        # Initialize analysis object
        analysis = QueryAnalysis(
            original_query=query,
            normalized_query=query_lower,
            query_type="unknown",
            entities={},
        )
        
        # Extract price range
        price_range = self._extract_price_range(query_lower)
        if price_range:
            analysis.price_range = price_range
            analysis.entities['price_range'] = price_range
        
        # Extract product type/category
        categories = self._extract_categories(query_lower)
        if categories:
            analysis.categories = categories
            analysis.entities['categories'] = categories
        
        # Extract brands
        brands = self._extract_brands(query_lower)
        if brands:
            analysis.brands = brands
            analysis.entities['brands'] = brands
        
        # Extract modifier terms (best, cheap, etc.)
        modifiers = self._extract_modifiers(query_lower)
        if modifiers:
            analysis.modifiers = modifiers
            analysis.entities['modifiers'] = modifiers
        
        # Basic sentiment analysis
        analysis.sentiment = self._analyze_sentiment(query_lower)
        
        # Determine primary query type
        analysis.query_type = self._determine_query_type(analysis)
        
        return analysis
    
    def _extract_price_range(self, query: str) -> Optional[Tuple[Optional[float], Optional[float]]]:
        """Extract price range from query"""
        for pattern in self.patterns['price_range']:
            match = pattern.search(query)
            if match:
                if pattern.pattern == r'(\w+)\s+under\s+(\d+)k?':
                    # "X under Y" pattern
                    price_str = match.group(2)
                    max_price = float(price_str) * 1000 if price_str.endswith('k') else float(price_str)
                    return (None, max_price)
                    
                elif pattern.pattern == r'under\s+(\d+)k?':
                    # "under X" pattern
                    price_str = match.group(1)
                    max_price = float(price_str) * 1000 if 'k' in price_str else float(price_str)
                    return (None, max_price)
                    
                elif pattern.pattern == r'(\d+)k?\s*-\s*(\d+)k?':
                    # "X-Y range" pattern
                    min_str = match.group(1)
                    max_str = match.group(2)
                    min_price = float(min_str) * 1000 if 'k' in min_str else float(min_str)
                    max_price = float(max_str) * 1000 if 'k' in max_str else float(max_str)
                    return (min_price, max_price)
                    
                elif pattern.pattern == r'less\s+than\s+(\d+)k?':
                    # "less than X" pattern
                    price_str = match.group(1)
                    max_price = float(price_str) * 1000 if 'k' in price_str else float(price_str)
                    return (None, max_price)
                
                elif pattern.pattern == r'budget\s+(\w+)':
                    # "budget X" pattern
                    product_type = match.group(1)
                    budget_key = f"budget_{product_type}"
                    if budget_key in self.common_price_ranges:
                        return self.common_price_ranges[budget_key]
        
        return None
    
    def _extract_categories(self, query: str) -> List[str]:
        """Extract product categories from query"""
        found_categories = []
        
        # Check for categories from database
        for category in self.categories:
            if category in query:
                found_categories.append(category)
        
        # If no categories found, try pattern matching
        if not found_categories:
            for pattern in self.patterns['product_type']:
                matches = pattern.findall(query)
                if matches:
                    found_categories.extend(matches)
        
        return list(set(found_categories))
    
    def _extract_brands(self, query: str) -> List[str]:
        """Extract brand names from query"""
        found_brands = []
        
        # Simple word matching for brands
        for brand in self.brands:
            # Make sure we match whole words, not partial
            if re.search(r'\b' + brand + r'\b', query):
                found_brands.append(brand)
        
        return found_brands
    
    def _extract_modifiers(self, query: str) -> List[str]:
        """Extract modifier terms like 'best', 'cheap', etc."""
        found_modifiers = []
        
        for modifier in self.modifier_terms:
            if modifier in query:
                found_modifiers.append(modifier)
        
        return found_modifiers
    
    def _analyze_sentiment(self, query: str) -> str:
        """Simple rule-based sentiment analysis"""
        words = query.split()
        
        # Count positive and negative terms
        positive_count = sum(1 for word in words if word in self.positive_terms)
        negative_count = sum(1 for word in words if word in self.negative_terms)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _determine_query_type(self, analysis: QueryAnalysis) -> str:
        """Determine primary query type"""
        if analysis.brands and not analysis.categories:
            return "brand"
        elif analysis.categories and not analysis.brands:
            return "category"
        elif analysis.price_range and not analysis.brands and not analysis.categories:
            return "price_range"
        elif analysis.brands and analysis.categories:
            return "brand_category"
        elif analysis.price_range and (analysis.brands or analysis.categories):
            return "price_filtered"
        else:
            return "general"
    
    def generate_suggestions(self, query: str, max_suggestions: int = 10) -> List[Dict[str, Any]]:
        """Generate autosuggest items based on query analysis"""
        analysis = self.analyze_query(query)
        suggestions = []
        
        # Generate appropriate suggestions based on query type
        if analysis.query_type in ["brand", "brand_category"]:
            suggestions.extend(self._get_brand_category_suggestions(analysis))
        
        if analysis.query_type in ["category", "price_filtered", "general"]:
            suggestions.extend(self._get_category_suggestions(analysis))
        
        if analysis.price_range or "budget" in query.lower():
            suggestions.extend(self._get_price_range_suggestions(analysis))
        
        # Add modifier-based suggestions (best X, top Y, etc.)
        if analysis.modifiers or len(query.split()) <= 2:
            suggestions.extend(self._get_modifier_suggestions(analysis))
        
        # Sort by relevance/confidence and limit
        suggestions.sort(key=lambda x: x.get('score', 0), reverse=True)
        return suggestions[:max_suggestions]
    
    def _get_brand_category_suggestions(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """Generate brand + category suggestions"""
        suggestions = []
        
        # If only brand is specified, suggest common product categories
        if analysis.query_type == "brand" and analysis.brands:
            brand = analysis.brands[0]
            common_categories = ['mobile', 'laptop', 'tv', 'tablet', 'headphone']
            
            for category in common_categories:
                suggestion = {
                    'text': f"{brand} {category}",
                    'type': "brand_category",
                    'category': category,
                    'score': 0.9,
                }
                suggestions.append(suggestion)
        
        # If brand + category, suggest price ranges
        elif analysis.query_type == "brand_category":
            brand = analysis.brands[0]
            category = analysis.categories[0]
            
            # Common price ranges
            if category in ['mobile', 'phone', 'smartphone']:
                price_ranges = ["under 10k", "under 15k", "under 20k", "under 30k"]
            elif category in ['laptop', 'computer']:
                price_ranges = ["under 30k", "under 50k", "under 70k", "under 1 lakh"]
            else:
                price_ranges = ["under 10k", "under 20k", "under 50k"]
                
            for i, price_range in enumerate(price_ranges):
                suggestion = {
                    'text': f"{brand} {category} {price_range}",
                    'type': "price_filtered",
                    'category': category,
                    'score': 0.9 - (i * 0.05),  # Decreasing score for later suggestions
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_category_suggestions(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """Generate category-based suggestions"""
        suggestions = []
        
        if not analysis.categories:
            return suggestions
            
        category = analysis.categories[0]
        
        # Suggest popular brands in this category
        top_brands = self._get_top_brands_for_category(category)
        
        for i, brand in enumerate(top_brands):
            suggestion = {
                'text': f"{brand} {category}",
                'type': "brand_category",
                'category': category,
                'score': 0.85 - (i * 0.05),
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _get_price_range_suggestions(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """Generate price range suggestions"""
        suggestions = []
        
        categories = analysis.categories or ['mobile', 'laptop']  # Default categories if none specified
        
        for category in categories[:2]:  # Limit to 2 categories to avoid too many suggestions
            if category in ['mobile', 'phone', 'smartphone']:
                price_points = ['under 10k', 'under 15k', 'under 20k', 'under 30k']
            elif category in ['laptop', 'computer']:
                price_points = ['under 30k', 'under 50k', 'under 70k', 'under 1 lakh']
            else:
                price_points = ['under 20k', 'under 50k']
            
            # Add brands if specified
            prefix = f"{analysis.brands[0]} " if analysis.brands else ""
            
            for i, price in enumerate(price_points):
                suggestion = {
                    'text': f"{prefix}{category} {price}",
                    'type': "price_range",
                    'category': category,
                    'score': 0.8 - (i * 0.05),
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_modifier_suggestions(self, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """Generate suggestions with modifiers (best, top, etc.)"""
        suggestions = []
        
        if not analysis.categories and len(analysis.normalized_query.split()) <= 2:
            # Short query, could be looking for "best X" type suggestions
            modifiers = ['best', 'top', 'new']
            categories = ['mobile', 'laptop', 'tv', 'headphone']
            
            for modifier in modifiers[:1]:  # Just use first modifier to avoid too many suggestions
                for i, category in enumerate(categories):
                    suggestion = {
                        'text': f"{modifier} {category}",
                        'type': "modifier",
                        'category': category,
                        'score': 0.7 - (i * 0.05),
                    }
                    suggestions.append(suggestion)
        
        elif analysis.categories:
            # Already has category, add modifiers
            category = analysis.categories[0]
            modifiers = ['best', 'top', 'new', 'budget']
            
            prefix = f"{analysis.brands[0]} " if analysis.brands else ""
            
            for i, modifier in enumerate(modifiers):
                suggestion = {
                    'text': f"{modifier} {prefix}{category}",
                    'type': "modifier",
                    'category': category,
                    'score': 0.75 - (i * 0.05),
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_top_brands_for_category(self, category: str) -> List[str]:
        """Get top brands for a given category - ideally from database"""
        # Default mappings if database not available
        category_brand_map = {
            'mobile': ['samsung', 'apple', 'oneplus', 'xiaomi', 'vivo'],
            'laptop': ['hp', 'lenovo', 'dell', 'asus', 'apple'],
            'tv': ['samsung', 'lg', 'sony', 'mi', 'oneplus'],
            'headphone': ['boat', 'sony', 'jbl', 'noise', 'oneplus'],
            'camera': ['canon', 'nikon', 'sony', 'fujifilm', 'gopro'],
        }
        
        if self.db:
            try:
                # More sophisticated: Get top brands by popularity in this category
                top_brands = (self.db.query(Product.brand)
                             .filter(Product.category.ilike(f'%{category}%'))
                             .group_by(Product.brand)
                             .order_by(func.count(Product.id).desc())
                             .limit(5)
                             .all())
                if top_brands:
                    return [brand[0].lower() for brand in top_brands if brand[0]]
            except Exception as e:
                logger.error(f"Error getting top brands from database: {e}")
        
        # Fallback to defaults
        return category_brand_map.get(category.lower(), ['samsung', 'apple', 'xiaomi'])
    
    def update_query_database(self, query: str, user_id: Optional[str] = None, clicked: bool = False):
        """Update database with new query patterns - for learning"""
        if not self.db:
            logger.warning("Database not available, can't update query patterns")
            return
            
        try:
            # Analyze the query
            analysis = self.analyze_query(query)
            
            # Check if this query exists in the autosuggest table
            existing_query = self.db.query(AutosuggestQuery).filter(
                AutosuggestQuery.query.ilike(query)
            ).first()
            
            if existing_query:
                # Update popularity - use SQLAlchemy update pattern
                popularity_increase = 5 if clicked else 1
                self.db.query(AutosuggestQuery).filter(
                    AutosuggestQuery.id == existing_query.id
                ).update({
                    AutosuggestQuery.popularity: AutosuggestQuery.popularity + popularity_increase,
                    AutosuggestQuery.updated_at: datetime.now()
                })
            else:
                # Create new query entry
                category = analysis.categories[0] if analysis.categories else "general"
                new_query = AutosuggestQuery(
                    query=query,
                    popularity=5 if clicked else 1,
                    category=category,
                    is_product_name=analysis.query_type == "brand_category",
                    metadata={
                        "brands": analysis.brands,
                        "price_range": analysis.price_range,
                        "query_type": analysis.query_type,
                        "sentiment": analysis.sentiment
                    }
                )
                self.db.add(new_query)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating query database: {e}")
            self.db.rollback()


# Factory function for dependency injection
def get_query_analyzer() -> QueryAnalyzerService:
    """Get QueryAnalyzerService instance"""
    return QueryAnalyzerService(None)
