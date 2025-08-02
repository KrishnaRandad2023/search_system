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
            # Try to load from JSON file first (main dataset - 12,000 products)
            json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "products.json")
            
            word_counts = {}
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)[:5000]  # Use first 5000 for performance
                
                for product in products:
                    # Extract words from various fields
                    words = []
                    for field in ['title', 'brand', 'category', 'subcategory', 'description']:
                        if product.get(field):
                            words.extend(str(product[field]).lower().split())
                    
                    # Also extract from tags if available
                    if product.get('tags') and isinstance(product['tags'], list):
                        for tag in product['tags']:
                            words.extend(str(tag).lower().split())
                    
                    # Count word frequencies
                    for word in words:
                        # Clean word (remove special characters)
                        clean_word = ''.join(c for c in word if c.isalnum())
                        if len(clean_word) > 2:  # Skip very short words
                            word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
            
            # Also load from queries for common search terms
            queries_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "queries.json")
            if os.path.exists(queries_path):
                with open(queries_path, 'r', encoding='utf-8') as f:
                    queries = json.load(f)
                
                for query in queries:
                    query_text = query.get('query_text', '')
                    popularity = query.get('popularity', 1)
                    
                    for word in query_text.lower().split():
                        clean_word = ''.join(c for c in word if c.isalnum())
                        if len(clean_word) > 2:
                            # Weight by popularity
                            word_counts[clean_word] = word_counts.get(clean_word, 0) + popularity
            
            # Add common e-commerce terms manually (still useful)
            common_terms = {
                'phone': 100, 'mobile': 90, 'smartphone': 80,
                'laptop': 95, 'computer': 70, 'tablet': 50,
                'headphones': 60, 'earphones': 50, 'speaker': 40,
                'shoes': 70, 'footwear': 60, 'sneakers': 50,
                'shirt': 60, 'jeans': 55, 'dress': 50,
                'watch': 50, 'smart': 40, 'wireless': 35,
                'bluetooth': 30, 'gaming': 40, 'fitness': 35,
                'samsung': 80, 'apple': 85, 'oneplus': 70,
                'xiaomi': 65, 'realme': 60, 'oppo': 55,
                'vivo': 55, 'nokia': 50, 'motorola': 45
            }
            
            # Merge common terms
            for term, count in common_terms.items():
                word_counts[term] = max(word_counts.get(term, 0), count)
            
            # Add words to spell checker
            added_count = 0
            for word, count in word_counts.items():
                if count >= 2:  # Lower threshold since we have more data
                    self.spell_checker.create_dictionary_entry(word, count)
                    added_count += 1
            
            print(f"📚 Spell checker vocabulary built with {added_count} words from full dataset")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not build spell check vocabulary: {e}")
            # Add basic fallback vocabulary
            basic_words = ['phone', 'mobile', 'laptop', 'computer', 'shoes', 'shirt', 'jeans']
            for word in basic_words:
                self.spell_checker.create_dictionary_entry(word, 10)
    
    def check_and_correct(self, query: str, confidence_threshold: int = 2) -> Tuple[str, bool]:
        """
        Check spelling and return corrected query if needed - Enhanced for universal matching
        
        Args:
            query: The input query to check
            confidence_threshold: Minimum word frequency to accept correction (lowered for better coverage)
            
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
                
                # Skip common stop words that don't need correction
                stop_words = {'for', 'men', 'women', 'kids', 'the', 'and', 'with', 'under'}
                if word in stop_words:
                    corrected_words.append(word)
                    continue
                
                # Get spell suggestions with more aggressive matching
                suggestions = self.spell_checker.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
                
                if suggestions and suggestions[0].term != word:
                    # Use more lenient threshold for universal coverage
                    if suggestions[0].count >= confidence_threshold:
                        corrected_words.append(suggestions[0].term)
                        has_correction = True
                        continue
                
                # If no good spell correction found, try fuzzy matching with common plurals
                corrected_word = self._try_fuzzy_correction(word)
                if corrected_word != word:
                    corrected_words.append(corrected_word)
                    has_correction = True
                else:
                    corrected_words.append(word)
            
            corrected_query = ' '.join(corrected_words)
            return corrected_query, has_correction
            
        except Exception as e:
            print(f"Warning: Spell check error: {e}")
            return query, False
    
    def _try_fuzzy_correction(self, word: str) -> str:
        """
        Try fuzzy corrections for common patterns - Universal product matching
        
        Args:
            word: Word to correct
            
        Returns:
            Corrected word or original if no correction found
        """
        # Common typo patterns - universal approach
        common_corrections = {
            # Plural/singular corrections
            'jeins': 'jeans',
            'jein': 'jean', 
            'shoen': 'shoe',
            'sheos': 'shoes',
            'phoen': 'phone',
            'lapotop': 'laptop',
            'labtop': 'laptop',
            'tshirt': 't-shirt',
            'tshirts': 't-shirts',
            
            # Brand typos
            'samung': 'samsung',
            'samsang': 'samsung',
            'appel': 'apple',
            'sonny': 'sony',
            'nokya': 'nokia',
            
            # Category typos
            'moblie': 'mobile',
            'compuer': 'computer',
            'electronis': 'electronics',
            'clothng': 'clothing',
        }
        
        # Direct lookup
        if word in common_corrections:
            return common_corrections[word]
        
        # Try removing/adding 's' for plurals
        if word.endswith('s') and len(word) > 4:
            singular = word[:-1]
            if self._word_exists_in_vocab(singular):
                return singular
        elif not word.endswith('s'):
            plural = word + 's'
            if self._word_exists_in_vocab(plural):
                return word  # Keep original, but mark as valid
        
        return word
    
    def _word_exists_in_vocab(self, word: str) -> bool:
        """Check if a word exists in our vocabulary"""
        if not self.is_initialized or not self.spell_checker:
            return False
        try:
            # Check if word exists with exact match
            suggestions = self.spell_checker.lookup(word, Verbosity.CLOSEST, max_edit_distance=0)
            return len(suggestions) > 0 and suggestions[0].term == word
        except:
            return False
    
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
