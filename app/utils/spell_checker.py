"""
Reusable Spell Correction Utility
Provides spell checking capabilities across all search endpoints
"""

from typing import Tuple, Optional, List
import os
import json

try:
    from symspellpy import SymSpell, Verbosity
    SYMSPELL_AVAILABLE = True
except ImportError:
    SYMSPELL_AVAILABLE = False
    print("Warning: symspellpy not available, spell correction will be disabled")

class SpellChecker:
    """Centralized spell checker for all search queries"""
    
    def __init__(self):
        self.spell_checker = None
        self.is_initialized = False
        self._initialize_spell_checker()
    
    def _initialize_spell_checker(self):
        """Initialize the spell checker with product vocabulary"""
        if not SYMSPELL_AVAILABLE:
            print("Spell checker disabled - symspellpy not available")
            return
        
        try:
            # Initialize SymSpell
            self.spell_checker = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
            
            # Load product data to build vocabulary
            self._build_vocabulary()
            self.is_initialized = True
            print(f"✅ Global spell checker initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize spell checker: {e}")
            self.spell_checker = None
    
    def _build_vocabulary(self):
        """Build spell check dictionary from product data"""
        try:
            # Try to load from JSON file (search_v2.py format)
            json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "products.json")
            
            word_counts = {}
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)[:1000]  # Limit for performance
                
                for product in products:
                    # Extract words from various fields
                    words = []
                    for field in ['title', 'brand', 'category', 'subcategory', 'description']:
                        if product.get(field):
                            words.extend(str(product[field]).lower().split())
                    
                    # Count word frequencies
                    for word in words:
                        # Clean word (remove special characters)
                        clean_word = ''.join(c for c in word if c.isalnum())
                        if len(clean_word) > 2:  # Skip very short words
                            word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
            
            # Add common e-commerce terms manually
            common_terms = {
                'phone': 50, 'mobile': 45, 'smartphone': 30,
                'laptop': 40, 'computer': 35, 'tablet': 25,
                'headphones': 30, 'earphones': 25, 'speaker': 20,
                'shoes': 35, 'footwear': 30, 'sneakers': 25,
                'shirt': 30, 'jeans': 28, 'dress': 25,
                'watch': 25, 'smart': 20, 'wireless': 18,
                'bluetooth': 15, 'gaming': 20, 'fitness': 18
            }
            
            # Merge common terms
            for term, count in common_terms.items():
                word_counts[term] = max(word_counts.get(term, 0), count)
            
            # Add words to spell checker
            for word, count in word_counts.items():
                if count >= 3:  # Only add words that appear multiple times
                    self.spell_checker.create_dictionary_entry(word, count)
            
            print(f"📚 Spell checker vocabulary built with {len([w for w, c in word_counts.items() if c >= 3])} words")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not build spell check vocabulary: {e}")
            # Add basic fallback vocabulary
            basic_words = ['phone', 'mobile', 'laptop', 'computer', 'shoes', 'shirt', 'jeans']
            for word in basic_words:
                self.spell_checker.create_dictionary_entry(word, 10)
    
    def check_and_correct(self, query: str, confidence_threshold: int = 5) -> Tuple[str, bool]:
        """
        Check spelling and return corrected query if needed
        
        Args:
            query: The input query to check
            confidence_threshold: Minimum word frequency to accept correction
            
        Returns:
            Tuple of (corrected_query, has_correction)
        """
        if not self.is_initialized or not self.spell_checker:
            return query, False
        
        try:
            words = query.lower().split()
            corrected_words = []
            has_correction = False
            
            for word in words:
                # Skip numbers, very short words, and special characters
                if word.isdigit() or len(word) < 3 or not word.isalpha():
                    corrected_words.append(word)
                    continue
                
                # Get spell suggestions
                suggestions = self.spell_checker.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
                
                if suggestions and suggestions[0].term != word:
                    # Only use correction if it's significantly more frequent
                    if suggestions[0].count >= confidence_threshold:
                        corrected_words.append(suggestions[0].term)
                        has_correction = True
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)
            
            corrected_query = ' '.join(corrected_words)
            return corrected_query, has_correction
            
        except Exception as e:
            print(f"Warning: Spell check error: {e}")
            return query, False
    
    def get_suggestions(self, word: str, max_suggestions: int = 3) -> List[str]:
        """Get spelling suggestions for a single word"""
        if not self.is_initialized or not self.spell_checker:
            return []
        
        try:
            suggestions = self.spell_checker.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            return [s.term for s in suggestions[:max_suggestions] if s.term != word]
        except:
            return []

# Global spell checker instance
_global_spell_checker = None

def get_spell_checker() -> SpellChecker:
    """Get the global spell checker instance"""
    global _global_spell_checker
    if _global_spell_checker is None:
        _global_spell_checker = SpellChecker()
    return _global_spell_checker

def check_spelling(query: str) -> Tuple[str, bool]:
    """
    Convenience function to check spelling of a query
    
    Returns:
        Tuple of (corrected_query, has_correction)
    """
    spell_checker = get_spell_checker()
    return spell_checker.check_and_correct(query)
