"""
Trie-based Autosuggest Service
Production-ready implementation with spell correction
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import re
from collections import defaultdict, Counter
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Suggestion:
    text: str
    score: float
    suggestion_type: str  # "product", "category", "brand", "trending", "corrected"
    metadata: Optional[Dict[str, Any]] = None

class TrieNode:
    """Node in the Trie structure"""
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.suggestions = []  # Store suggestions at this node
        self.frequency = 0

class TrieAutosuggest:
    """Production-grade Trie-based autosuggest with spell correction"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.root = TrieNode()
        self.db_path = db_path
        self.spell_checker = None
        self._initialize_spell_checker()
        self._build_trie()
    
    def _initialize_spell_checker(self):
        """Initialize spell checker if available"""
        try:
            from app.utils.spell_checker import check_spelling
            self.check_spelling = check_spelling
            logger.info("Spell checker initialized for autosuggest")
        except Exception as e:
            logger.warning(f"Spell checker not available for autosuggest: {e}")
            self.check_spelling = None
    
    def _build_trie(self):
        """Build Trie from product data"""
        try:
            if self.db_path and Path(self.db_path).exists():
                self._build_from_database()
            else:
                self._build_from_json()
            logger.info("Trie autosuggest built successfully")
        except Exception as e:
            logger.error(f"Failed to build Trie: {e}")
    
    def _build_from_database(self):
        """Build Trie from SQLite database"""
        if not self.db_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get product titles and their popularity from the full dataset
            cursor.execute("""
                SELECT title, rating, num_ratings, brand, category, subcategory, is_bestseller
                FROM products 
                WHERE is_available = 1 AND title IS NOT NULL
                ORDER BY num_ratings DESC, rating DESC
                LIMIT 10000
            """)
            
            for row in cursor.fetchall():
                title, rating, num_ratings, brand, category, subcategory, is_bestseller = row
                
                # Calculate frequency based on rating, reviews, and bestseller status
                base_frequency = int((rating or 0) * (num_ratings or 1))
                if is_bestseller:
                    base_frequency *= 2
                
                # Add product title
                self._insert(title.lower(), base_frequency, "product", {
                    "title": title,
                    "brand": brand,
                    "category": category,
                    "subcategory": subcategory
                })
                
                # Add brand
                if brand:
                    self._insert(brand.lower(), base_frequency // 2, "brand", {"brand": brand})
                
                # Add category and subcategory
                if category:
                    self._insert(category.lower(), base_frequency // 3, "category", {"category": category})
                if subcategory:
                    self._insert(subcategory.lower(), base_frequency // 4, "category", {"category": subcategory})
                
                # Add individual words from title
                words = re.findall(r'\b\w+\b', title.lower())
                for word in words:
                    if len(word) > 2:
                        self._insert(word, base_frequency // 5, "word", {"word": word})
            
            # Also load popular queries from the queries table
            cursor.execute("""
                SELECT query_text, popularity FROM queries 
                ORDER BY popularity DESC LIMIT 2500
            """)
            
            for query_text, popularity in cursor.fetchall():
                if query_text:
                    self._insert(query_text.lower(), popularity * 10, "trending", {
                        "query": query_text,
                        "popularity": popularity
                    })
            
            # Load autosuggest queries
            cursor.execute("""
                SELECT query, popularity, category FROM autosuggest_queries 
                ORDER BY popularity DESC LIMIT 2000
            """)
            
            for query, popularity, query_category in cursor.fetchall():
                if query:
                    self._insert(query.lower(), popularity * 5, "suggestion", {
                        "query": query,
                        "category": query_category,
                        "popularity": popularity
                    })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error building Trie from database: {e}")
    
    def _build_from_json(self):
        """Build Trie from JSON files (fallback)"""
        try:
            # Try to load from products.json
            products_file = Path("data/raw/products.json")
            if products_file.exists():
                with open(products_file, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                
                for product in products[:5000]:  # Limit for performance
                    title = product.get('name', '') or product.get('title', '')
                    brand = product.get('brand', '')
                    category = product.get('category', '')
                    rating = product.get('rating', 0)
                    
                    frequency = int(rating * 100) if rating else 1
                    
                    if title:
                        self._insert(title.lower(), frequency, "product", {
                            "title": title,
                            "brand": brand,
                            "category": category
                        })
                    
                    if brand:
                        self._insert(brand.lower(), frequency // 2, "brand", {"brand": brand})
                    
                    if category:
                        self._insert(category.lower(), frequency // 3, "category", {"category": category})
            
            # ENHANCEMENT: Load Amazon lite data for richer suggestions
            self._load_amazon_lite_data()
                        
        except Exception as e:
            logger.error(f"Error building Trie from JSON: {e}")
    
    def _load_amazon_lite_data(self):
        """Load Amazon lite data for enhanced autosuggest (SAFE ENHANCEMENT)"""
        try:
            # Load Amazon prefix mappings
            prefix_map_file = Path("data/amazon_lite_prefix_map.json")
            if prefix_map_file.exists():
                logger.info("Loading Amazon lite prefix mappings...")
                with open(prefix_map_file, 'r', encoding='utf-8') as f:
                    prefix_data = json.load(f)
                
                # Add top suggestions from prefix map (limit for performance)
                count = 0
                for prefix, suggestions in prefix_data.items():
                    if count >= 10000:  # Safety limit
                        break
                    
                    # Add the prefix itself
                    if len(prefix) > 2:  # Skip very short prefixes
                        self._insert(prefix.lower(), 50, "amazon_prefix", {
                            "text": prefix,
                            "source": "amazon_lite"
                        })
                    
                    # Add top suggestions for this prefix
                    for suggestion in suggestions[:3]:  # Top 3 suggestions only
                        if len(suggestion) > 2:
                            self._insert(suggestion.lower(), 75, "amazon_suggestion", {
                                "text": suggestion,
                                "source": "amazon_lite",
                                "prefix": prefix
                            })
                    count += 1
                
                logger.info(f"Loaded Amazon prefix mappings: {count} prefixes processed")
            
            # Load Amazon suggestions
            suggestions_file = Path("data/amazon_lite_suggestions.json")
            if suggestions_file.exists():
                logger.info("Loading Amazon lite suggestions...")
                with open(suggestions_file, 'r', encoding='utf-8') as f:
                    suggestions_data = json.load(f)
                
                # Add popular suggestions (limit for performance)
                count = 0
                for item in suggestions_data[:20000]:  # Safety limit: top 20k suggestions
                    prefixes = item.get('prefixes', [])
                    for prefix in prefixes[:5]:  # Top 5 prefixes per item
                        if len(prefix) > 2 and count < 15000:  # Double safety limit
                            self._insert(prefix.lower(), 60, "amazon_popular", {
                                "text": prefix,
                                "source": "amazon_suggestions"
                            })
                            count += 1
                
                logger.info(f"Loaded Amazon suggestions: {count} suggestions processed")
            
        except Exception as e:
            logger.warning(f"Could not load Amazon lite data (system will work without it): {e}")
            # System continues to work normally without Amazon data
    
    def _insert(self, text: str, frequency: int, suggestion_type: str, metadata: Dict):
        """Insert a suggestion into the Trie"""
        if not text or len(text) < 2:
            return
        
        node = self.root
        text = text.lower().strip()
        
        # Build path in Trie
        for char in text:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            
            # Add suggestion to intermediate nodes for prefix matching
            suggestion = Suggestion(
                text=text,
                score=frequency,
                suggestion_type=suggestion_type,
                metadata=metadata
            )
            
            # Keep only top suggestions at each node
            node.suggestions.append(suggestion)
            node.suggestions.sort(key=lambda x: x.score, reverse=True)
            node.suggestions = node.suggestions[:20]  # Limit per node
        
        # Mark end of word
        node.is_end = True
        node.frequency = max(node.frequency, frequency)
    
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[Suggestion]:
        """Get autosuggest suggestions for a query"""
        if not query or len(query) < 1:
            return []
        
        suggestions = []
        query_lower = query.lower().strip()
        
        # 1. Get Trie-based suggestions
        trie_suggestions = self._get_trie_suggestions(query_lower, max_suggestions)
        suggestions.extend(trie_suggestions)
        
        # 2. Add spell-corrected suggestions if available
        if self.check_spelling and len(query_lower) > 2:
            try:
                corrected_query, has_correction = self.check_spelling(query)
                if has_correction and corrected_query.lower() != query_lower:
                    corrected_suggestions = self._get_trie_suggestions(
                        corrected_query.lower(), 
                        max_suggestions // 2
                    )
                    # Mark as corrected
                    for sugg in corrected_suggestions:
                        sugg.suggestion_type = "corrected"
                        sugg.metadata = sugg.metadata or {}
                        sugg.metadata["original_query"] = query
                        sugg.metadata["corrected_from"] = corrected_query
                    suggestions.extend(corrected_suggestions)
            except Exception as e:
                logger.error(f"Spell correction error in autosuggest: {e}")
        
        # 3. Deduplicate and rank
        unique_suggestions = {}
        for sugg in suggestions:
            key = sugg.text.lower()
            if key not in unique_suggestions or sugg.score > unique_suggestions[key].score:
                unique_suggestions[key] = sugg
        
        # Sort by score and return top results
        final_suggestions = list(unique_suggestions.values())
        final_suggestions.sort(key=lambda x: x.score, reverse=True)
        
        return final_suggestions[:max_suggestions]
    
    def _get_trie_suggestions(self, query: str, max_suggestions: int) -> List[Suggestion]:
        """Get suggestions from Trie structure"""
        if not query:
            return []
        
        # Navigate to the prefix node
        node = self.root
        for char in query:
            if char not in node.children:
                return []  # Prefix not found
            node = node.children[char]
        
        # Collect suggestions from this node and children
        suggestions = []
        
        # Get suggestions stored at this node
        suggestions.extend(node.suggestions)
        
        # Get suggestions from child nodes (for completion)
        self._collect_from_children(node, suggestions, max_suggestions * 2)
        
        # Sort by score and return
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:max_suggestions]
    
    def _collect_from_children(self, node: TrieNode, suggestions: List[Suggestion], limit: int):
        """Recursively collect suggestions from child nodes"""
        if len(suggestions) >= limit:
            return
        
        for child in node.children.values():
            suggestions.extend(child.suggestions)
            if len(suggestions) < limit:
                self._collect_from_children(child, suggestions, limit)

# Global instance
_trie_autosuggest = None

def get_trie_autosuggest(db_path: Optional[str] = None) -> TrieAutosuggest:
    """Get global Trie autosuggest instance"""
    global _trie_autosuggest
    if _trie_autosuggest is None:
        _trie_autosuggest = TrieAutosuggest(db_path)
    return _trie_autosuggest
