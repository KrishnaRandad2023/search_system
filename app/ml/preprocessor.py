"""
Text Preprocessing for Flipkart Search System
Production-grade text preprocessing with advanced cleaning and normalization
"""

import re
import nltk
import unicodedata
import contractions
from typing import List, Dict, Optional, Set, Union
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize NLTK components - download if needed
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    logger.info("Downloading NLTK data...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class TextPreprocessor:
    """Production-grade text preprocessing with configurable steps"""
    
    def __init__(
        self,
        lowercase: bool = True,
        remove_punctuation: bool = True,
        expand_contractions: bool = True,
        remove_accents: bool = True,
        remove_stopwords: bool = True,
        lemmatize: bool = False,
        stem: bool = False,
        min_token_length: int = 2,
        custom_stopwords: Optional[Set[str]] = None
    ):
        """
        Initialize text preprocessor with configurable parameters
        
        Args:
            lowercase: Convert text to lowercase
            remove_punctuation: Remove punctuation marks
            expand_contractions: Expand contractions like "don't" to "do not"
            remove_accents: Remove accent marks
            remove_stopwords: Remove common stopwords
            lemmatize: Lemmatize words (convert to base form)
            stem: Apply stemming (reduce words to their root form)
            min_token_length: Minimum length of tokens to keep
            custom_stopwords: Additional stopwords to remove
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.expand_contractions = expand_contractions
        self.remove_accents = remove_accents
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.stem = stem
        self.min_token_length = min_token_length
        
        # Initialize NLP components
        self.stop_words = set(stopwords.words('english'))
        if custom_stopwords:
            self.stop_words.update(custom_stopwords)
            
        if self.lemmatize:
            self.lemmatizer = WordNetLemmatizer()
            
        if self.stem:
            self.stemmer = PorterStemmer()
            
        # E-commerce specific stopwords
        ecommerce_stopwords = {
            'buy', 'sell', 'price', 'offer', 'discount', 'shipping', 'free',
            'product', 'item', 'shop', 'store', 'online', 'delivery', 'order',
            'new', 'best', 'top', 'cheap', 'expensive', 'quality'
        }
        self.stop_words.update(ecommerce_stopwords)
            
        logger.info(f"TextPreprocessor initialized with {len(self.stop_words)} stopwords")
        
    def preprocess(self, text: str, tokenize: bool = False) -> Union[str, List[str]]:
        """
        Preprocess text by applying all configured steps
        
        Args:
            text: Input text to preprocess
            tokenize: Whether to return tokens or joined text
            
        Returns:
            Processed text as string or list of tokens
        """
        if not isinstance(text, str):
            if not text:
                return [] if tokenize else ""
            text = str(text)
            
        # Lowercase
        if self.lowercase:
            text = text.lower()
            
        # Expand contractions
        if self.expand_contractions:
            try:
                expanded = contractions.fix(text)
                text = str(expanded) if expanded is not None else text
            except Exception:
                # Fallback if contractions library has issues
                pass
            
        # Remove accents
        if self.remove_accents:
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
            
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', ' ', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', ' ', text)
            
        # Remove punctuation
        if self.remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
            
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        if self.remove_stopwords:
            tokens = [token for token in tokens if token.lower() not in self.stop_words]
            
        # Filter by token length
        tokens = [token for token in tokens if len(token) >= self.min_token_length]
        
        # Lemmatize
        if self.lemmatize:
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
        # Stem
        if self.stem:
            tokens = [self.stemmer.stem(token) for token in tokens]
            
        if tokenize:
            return tokens
        else:
            return ' '.join(tokens)
            
    def preprocess_query(self, query: str) -> str:
        """
        Special preprocessing for search queries
        
        Args:
            query: Search query text
            
        Returns:
            Processed query with less aggressive normalization
        """
        # Use lighter preprocessing for queries
        temp_stopwords = self.remove_stopwords
        temp_lemmatize = self.lemmatize
        temp_stem = self.stem
        
        # Don't remove stopwords or transform words for queries
        self.remove_stopwords = False
        self.lemmatize = False
        self.stem = False
        
        # Preprocess the query
        processed = self.preprocess(query)
        
        # Restore original settings
        self.remove_stopwords = temp_stopwords
        self.lemmatize = temp_lemmatize
        self.stem = temp_stem
        
        # Ensure we return a string for queries
        if isinstance(processed, list):
            return ' '.join(processed)
        return processed
            
    def preprocess_batch(self, texts: List[str], tokenize: bool = False) -> List[Union[str, List[str]]]:
        """Process a batch of texts"""
        return [self.preprocess(text, tokenize) for text in texts]
        
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords from text"""
        # Process with full stopword removal and normalization
        tokens = self.preprocess(text, tokenize=True)
        
        # Count token frequencies
        token_counts = {}
        for token in tokens:
            if token in token_counts:
                token_counts[token] += 1
            else:
                token_counts[token] = 1
                
        # Sort by frequency
        sorted_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N keywords
        return [token for token, _ in sorted_tokens[:top_n]]
        
    def extract_product_features(self, text: str) -> Dict[str, str]:
        """Extract product features from text using patterns"""
        features = {}
        
        # Common e-commerce feature patterns
        patterns = {
            'color': r'(?:color|colour)[\s:]+([a-zA-Z]+)',
            'size': r'(?:size)[\s:]+([a-zA-Z0-9]+)',
            'weight': r'(?:weight|mass)[\s:]+([0-9.]+\s*(?:kg|g|lbs|pounds|oz))',
            'dimensions': r'(?:dimensions|size)[\s:]+([0-9.]+\s*[x×]\s*[0-9.]+\s*[x×]\s*[0-9.]+\s*(?:cm|mm|in|inches|m))',
            'material': r'(?:material|made of)[\s:]+([a-zA-Z]+)',
        }
        
        # Extract features using regex
        for feature, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                features[feature] = match.group(1).strip()
                
        return features
        
    def normalize_brands(self, text: str, brand_dict: Dict[str, str]) -> str:
        """Normalize brand names using a mapping dictionary"""
        for variant, standard in brand_dict.items():
            text = re.sub(r'\b' + re.escape(variant) + r'\b', standard, text, flags=re.IGNORECASE)
            
        return text
        
    def normalize_categories(self, text: str, category_dict: Dict[str, str]) -> str:
        """Normalize category names using a mapping dictionary"""
        for variant, standard in category_dict.items():
            text = re.sub(r'\b' + re.escape(variant) + r'\b', standard, text, flags=re.IGNORECASE)
            
        return text
