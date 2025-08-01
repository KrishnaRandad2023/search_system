"""
Advanced Autosuggest Engine for Flipkart Grid Search System
Uses the provided Amazon Lite models + custom Flipkart product suggestions
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import re
from collections import defaultdict, Counter
import time
from dataclasses import dataclass
from symspellpy import SymSpell, Verbosity
import editdistance

@dataclass
class SuggestionResult:
    """Structured suggestion result"""
    query: str
    score: float
    suggestion_type: str  # "product", "category", "brand", "trending", "corrected"
    metadata: Dict[str, Any]

class AdvancedAutosuggestEngine:
    """
    🔥 Industry-level autosuggest engine combining:
    - Your provided Amazon Lite models
    - Live Flipkart product data
    - Spell correction (SymSpell)
    - Trending queries
    - Context-aware suggestions
    """
    
    def __init__(self, data_dir: Path, db_path: str):
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        
        # Load existing models
        self.prefix_map = self._load_prefix_map()
        self.amazon_suggestions = self._load_amazon_suggestions()
        
        # Initialize spell checker
        self.spell_checker = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self._setup_spell_checker()
        
        # Build product-based suggestions
        self.product_suggestions = self._build_product_suggestions()
        self.category_suggestions = self._build_category_suggestions()
        self.brand_suggestions = self._build_brand_suggestions()
        
        # Trending and popular queries (simulated)
        self.trending_queries = self._build_trending_queries()
        
        print("🚀 Advanced Autosuggest Engine initialized!")
        print(f"   - Prefix mappings: {len(self.prefix_map):,}")
        print(f"   - Amazon suggestions: {len(self.amazon_suggestions):,}")
        print(f"   - Product suggestions: {len(self.product_suggestions):,}")
        print(f"   - Category suggestions: {len(self.category_suggestions):,}")
        print(f"   - Brand suggestions: {len(self.brand_suggestions):,}")
        
    def _load_prefix_map(self) -> Dict[str, List[str]]:
        """Load the Amazon Lite prefix map"""
        try:
            with open(self.data_dir / "amazon_lite_prefix_map.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load prefix map: {e}")
            return {}
            
    def _load_amazon_suggestions(self) -> List[Dict]:
        """Load Amazon Lite suggestions"""
        try:
            with open(self.data_dir / "amazon_lite_suggestions.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load Amazon suggestions: {e}")
            return []
            
    def _setup_spell_checker(self):
        """Setup SymSpell with product vocabulary"""
        # Add common English words
        dictionary_path = self.data_dir / "spell_dictionary.txt"
        
        # Create basic dictionary if it doesn't exist
        if not dictionary_path.exists():
            common_words = [
                "phone", "mobile", "laptop", "computer", "camera", "headphones",
                "shoes", "shirt", "jeans", "watch", "bag", "book", "toy",
                "kitchen", "home", "beauty", "health", "sports", "fitness",
                "samsung", "apple", "sony", "nike", "adidas", "amazon", "flipkart"
            ]
            
            with open(dictionary_path, 'w', encoding='utf-8') as f:
                for word in common_words:
                    f.write(f"{word} 1000\n")
        
        # Load dictionary
        if dictionary_path.exists():
            self.spell_checker.load_dictionary(str(dictionary_path), term_index=0, count_index=1)
            
    def _build_product_suggestions(self) -> Dict[str, List[Dict]]:
        """Build suggestions from actual product titles"""
        suggestions = defaultdict(list)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get popular products (high rating, good stock)
            cursor.execute("""
                SELECT title, brand, category, rating, review_count, click_count
                FROM products 
                WHERE is_in_stock = 1 AND rating >= 3.5
                ORDER BY (rating * review_count * click_count) DESC
                LIMIT 5000
            """)
            
            products = cursor.fetchall()
            
            for title, brand, category, rating, review_count, click_count in products:
                # Create suggestions from product title
                words = re.findall(r'\b\w+\b', title.lower())
                
                # Generate prefixes for each word
                for word in words:
                    if len(word) >= 3:  # Only meaningful words
                        for i in range(3, len(word) + 1):
                            prefix = word[:i]
                            suggestions[prefix].append({
                                "suggestion": title,
                                "type": "product",
                                "brand": brand,
                                "category": category,
                                "score": float(rating * (review_count + 1) * (click_count + 1)),
                                "metadata": {
                                    "rating": rating,
                                    "review_count": review_count,
                                    "click_count": click_count
                                }
                            })
                            
            conn.close()
            
            # Sort and limit suggestions for each prefix
            for prefix in suggestions:
                suggestions[prefix] = sorted(
                    suggestions[prefix], 
                    key=lambda x: x["score"], 
                    reverse=True
                )[:10]  # Top 10 per prefix
                
        except Exception as e:
            print(f"⚠️  Error building product suggestions: {e}")
            
        return dict(suggestions)
        
    def _build_category_suggestions(self) -> Dict[str, List[str]]:
        """Build category-based suggestions"""
        suggestions = defaultdict(list)
        
        categories = [
            "Electronics", "Fashion", "Home & Kitchen", "Books",
            "Sports & Fitness", "Beauty & Health", "Grocery", "Toys & Baby"
        ]
        
        subcategories = [
            "Mobiles", "Laptops", "Headphones", "Cameras",
            "Men's Clothing", "Women's Clothing", "Footwear", "Watches",
            "Kitchen Appliances", "Furniture", "Home Decor"
        ]
        
        all_categories = categories + subcategories
        
        for category in all_categories:
            words = category.lower().split()
            for word in words:
                if len(word) >= 3:
                    for i in range(3, len(word) + 1):
                        prefix = word[:i]
                        if category not in suggestions[prefix]:
                            suggestions[prefix].append(category)
                            
        return dict(suggestions)
        
    def _build_brand_suggestions(self) -> Dict[str, List[str]]:
        """Build brand-based suggestions"""
        suggestions = defaultdict(list)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get popular brands
            cursor.execute("""
                SELECT brand, COUNT(*) as product_count, AVG(rating) as avg_rating
                FROM products 
                WHERE brand IS NOT NULL
                GROUP BY brand
                HAVING product_count >= 5
                ORDER BY product_count DESC, avg_rating DESC
                LIMIT 200
            """)
            
            brands = cursor.fetchall()
            conn.close()
            
            for brand, count, rating in brands:
                if brand and len(brand) >= 2:
                    brand_lower = brand.lower()
                    for i in range(2, len(brand_lower) + 1):
                        prefix = brand_lower[:i]
                        if brand not in suggestions[prefix]:
                            suggestions[prefix].append(brand)
                            
        except Exception as e:
            print(f"⚠️  Error building brand suggestions: {e}")
            
        return dict(suggestions)
        
    def _build_trending_queries(self) -> List[str]:
        """Build trending/popular queries (simulated for demo)"""
        return [
            "iphone 15", "samsung galaxy", "laptop", "headphones", "nike shoes",
            "air conditioner", "washing machine", "books", "toys", "beauty products",
            "kitchen appliances", "mobile covers", "bluetooth speaker", "smartwatch",
            "gaming laptop", "running shoes", "winter clothes", "home decor"
        ]
        
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[SuggestionResult]:
        """
        Get comprehensive suggestions for a query
        """
        if not query or len(query.strip()) < 2:
            return self._get_trending_suggestions(max_suggestions)
            
        query = query.strip().lower()
        all_suggestions = []
        
        # 1. Exact prefix matches from your Amazon model
        amazon_suggestions = self._get_amazon_suggestions(query)
        all_suggestions.extend(amazon_suggestions)
        
        # 2. Product-based suggestions
        product_suggestions = self._get_product_suggestions(query)
        all_suggestions.extend(product_suggestions)
        
        # 3. Category suggestions
        category_suggestions = self._get_category_suggestions(query)
        all_suggestions.extend(category_suggestions)
        
        # 4. Brand suggestions
        brand_suggestions = self._get_brand_suggestions(query)
        all_suggestions.extend(brand_suggestions)
        
        # 5. Spell correction suggestions
        if len(all_suggestions) < 3:  # Only if we don't have enough
            corrected_suggestions = self._get_spell_corrected_suggestions(query)
            all_suggestions.extend(corrected_suggestions)
            
        # 6. Fuzzy matching for typos
        fuzzy_suggestions = self._get_fuzzy_suggestions(query)
        all_suggestions.extend(fuzzy_suggestions)
        
        # Remove duplicates and rank
        unique_suggestions = self._deduplicate_and_rank(all_suggestions)
        
        return unique_suggestions[:max_suggestions]
        
    def _get_amazon_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get suggestions from Amazon Lite model"""
        suggestions = []
        
        # Check prefix map
        if query in self.prefix_map:
            for suggestion in self.prefix_map[query][:5]:  # Top 5
                suggestions.append(SuggestionResult(
                    query=suggestion,
                    score=0.9,  # High score for exact matches
                    suggestion_type="amazon_model",
                    metadata={"source": "amazon_prefix_map"}
                ))
                
        return suggestions
        
    def _get_product_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get product-based suggestions"""
        suggestions = []
        
        for prefix_len in range(len(query), max(2, len(query) - 3), -1):
            prefix = query[:prefix_len]
            if prefix in self.product_suggestions:
                for prod_suggest in self.product_suggestions[prefix][:3]:
                    score = 0.8 * (prefix_len / len(query))  # Longer match = higher score
                    suggestions.append(SuggestionResult(
                        query=prod_suggest["suggestion"],
                        score=score,
                        suggestion_type="product",
                        metadata=prod_suggest["metadata"]
                    ))
                break
                
        return suggestions
        
    def _get_category_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get category-based suggestions"""
        suggestions = []
        
        for prefix_len in range(len(query), max(2, len(query) - 2), -1):
            prefix = query[:prefix_len]
            if prefix in self.category_suggestions:
                for category in self.category_suggestions[prefix][:2]:
                    score = 0.7 * (prefix_len / len(query))
                    suggestions.append(SuggestionResult(
                        query=category,
                        score=score,
                        suggestion_type="category",
                        metadata={"type": "category"}
                    ))
                break
                
        return suggestions
        
    def _get_brand_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get brand-based suggestions"""
        suggestions = []
        
        for prefix_len in range(len(query), max(2, len(query) - 2), -1):
            prefix = query[:prefix_len]
            if prefix in self.brand_suggestions:
                for brand in self.brand_suggestions[prefix][:2]:
                    score = 0.75 * (prefix_len / len(query))
                    suggestions.append(SuggestionResult(
                        query=brand,
                        score=score,
                        suggestion_type="brand",
                        metadata={"type": "brand"}
                    ))
                break
                
        return suggestions
        
    def _get_spell_corrected_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get spell-corrected suggestions"""
        suggestions = []
        
        # Get spell corrections
        spell_suggestions = self.spell_checker.lookup(query, Verbosity.CLOSEST, max_edit_distance=2)
        
        for suggestion in spell_suggestions[:2]:  # Top 2 corrections
            if suggestion.term != query:  # Only if it's actually a correction
                suggestions.append(SuggestionResult(
                    query=suggestion.term,
                    score=0.6,
                    suggestion_type="corrected",
                    metadata={
                        "original_query": query,
                        "edit_distance": suggestion.distance,
                        "frequency": suggestion.count
                    }
                ))
                
        return suggestions
        
    def _get_fuzzy_suggestions(self, query: str) -> List[SuggestionResult]:
        """Get fuzzy matching suggestions for typos"""
        suggestions = []
        
        # Check for fuzzy matches in trending queries
        for trending_query in self.trending_queries:
            distance = editdistance.eval(query, trending_query.lower())
            max_distance = max(2, len(query) // 3)
            
            if distance <= max_distance and distance > 0:
                score = 0.5 * (1 - distance / len(trending_query))
                suggestions.append(SuggestionResult(
                    query=trending_query,
                    score=score,
                    suggestion_type="fuzzy",
                    metadata={
                        "original_query": query,
                        "edit_distance": distance
                    }
                ))
                
        return suggestions[:2]  # Top 2 fuzzy matches
        
    def _get_trending_suggestions(self, max_suggestions: int) -> List[SuggestionResult]:
        """Get trending suggestions for empty query"""
        suggestions = []
        
        for i, trending_query in enumerate(self.trending_queries[:max_suggestions]):
            score = 1.0 - (i * 0.1)  # Decreasing score
            suggestions.append(SuggestionResult(
                query=trending_query,
                score=score,
                suggestion_type="trending",
                metadata={"rank": i + 1}
            ))
            
        return suggestions
        
    def _deduplicate_and_rank(self, suggestions: List[SuggestionResult]) -> List[SuggestionResult]:
        """Remove duplicates and rank suggestions"""
        seen = set()
        unique_suggestions = []
        
        # Sort by score first
        suggestions.sort(key=lambda x: x.score, reverse=True)
        
        for suggestion in suggestions:
            query_key = suggestion.query.lower().strip()
            if query_key not in seen:
                seen.add(query_key)
                unique_suggestions.append(suggestion)
                
        return unique_suggestions
        
    def get_autocomplete_data(self, prefix: str) -> Dict[str, Any]:
        """Get structured autocomplete data for API response"""
        suggestions = self.get_suggestions(prefix, max_suggestions=8)
        
        return {
            "query": prefix,
            "suggestions": [
                {
                    "text": s.query,
                    "type": s.suggestion_type,
                    "score": s.score,
                    "metadata": s.metadata
                }
                for s in suggestions
            ],
            "total_suggestions": len(suggestions),
            "response_time_ms": 0  # To be filled by API
        }

# Test the engine
if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    db_path = str(data_dir / "db" / "flipkart_products.db")
    
    # Initialize engine
    engine = AdvancedAutosuggestEngine(data_dir, db_path)
    
    # Test queries
    test_queries = ["iph", "samsu", "laptop", "nike", ""]
    
    print("\n🧪 TESTING AUTOSUGGEST ENGINE")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        suggestions = engine.get_suggestions(query, max_suggestions=5)
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion.query} ({suggestion.suggestion_type}, score: {suggestion.score:.2f})")
            
    print("\n✅ Autosuggest engine test completed!")
