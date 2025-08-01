"""
Tests for the text preprocessor component
"""

import pytest
import nltk
from app.ml.preprocessor import TextPreprocessor

# Ensure NLTK data is available for tests
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class TestTextPreprocessor:
    
    def test_init_default(self):
        preprocessor = TextPreprocessor()
        assert preprocessor.lowercase is True
        assert preprocessor.remove_punctuation is True
        assert preprocessor.expand_contractions is True
        assert preprocessor.remove_accents is True
        assert preprocessor.remove_stopwords is True
        assert preprocessor.lemmatize is False
        assert preprocessor.stem is False
        assert preprocessor.min_token_length == 2
        assert len(preprocessor.stop_words) > 0
    
    def test_init_custom(self):
        custom_stopwords = {'custom', 'words'}
        preprocessor = TextPreprocessor(
            lowercase=False,
            remove_stopwords=False,
            min_token_length=3,
            custom_stopwords=custom_stopwords
        )
        
        assert preprocessor.lowercase is False
        assert preprocessor.remove_stopwords is False
        assert preprocessor.min_token_length == 3
        assert 'custom' in preprocessor.stop_words
        assert 'words' in preprocessor.stop_words
    
    def test_preprocess_basic(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_punctuation=True,
            expand_contractions=True,
            remove_stopwords=False,
            lemmatize=False,
            stem=False
        )
        
        text = "Hello, world! This is a test."
        processed = preprocessor.preprocess(text)
        
        # Convert list to string for comparison
        processed_str = " ".join(processed) if isinstance(processed, list) else processed
        assert processed_str.lower() == processed_str  # Check lowercase
        assert "," not in processed_str  # Check punctuation removal
        assert "!" not in processed_str  # Check punctuation removal
        assert "." not in processed_str  # Check punctuation removal
    
    def test_preprocess_stopwords(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_punctuation=True,
            remove_stopwords=True,
            lemmatize=False,
            stem=False
        )
        
        text = "This is a sample text with some stopwords"
        processed = preprocessor.preprocess(text)
        
        # Common stopwords should be removed (processed is a list)
        assert "is" not in processed
        assert "a" not in processed
        assert "with" not in processed
        assert "some" not in processed
        
        # Content words should remain
        assert "sample" in processed
        assert "text" in processed
        assert "stopwords" in processed
    
    def test_preprocess_lemmatize(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_stopwords=False,
            lemmatize=True,
            stem=False
        )
        
        text = "Running faster than cars"
        processed = preprocessor.preprocess(text)
        
        # Should lemmatize verbs and nouns (processed is a list)
        assert "running" not in processed
        assert "run" in processed
        assert "car" in processed
    
    def test_preprocess_stem(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_stopwords=False,
            lemmatize=False,
            stem=True
        )
        
        text = "Running faster than cars"
        processed = preprocessor.preprocess(text)
        
        # Should stem words (processed is a list)
        assert "running" not in processed
        assert "run" in processed
        assert "fast" in processed
        assert "car" in processed
    
    def test_preprocess_tokenize(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_stopwords=True
        )
        
        text = "This is a sample text"
        tokens = preprocessor.preprocess(text, tokenize=True)
        
        assert isinstance(tokens, list)
        assert "sample" in tokens
        assert "text" in tokens
        assert "is" not in tokens  # stopword
        assert "a" not in tokens   # stopword
    
    def test_preprocess_batch(self):
        preprocessor = TextPreprocessor()
        
        texts = ["Text one", "Text two", "Text three"]
        processed = preprocessor.preprocess_batch(texts)
        
        assert len(processed) == 3
        assert all(isinstance(p, str) for p in processed)
    
    def test_extract_keywords(self):
        preprocessor = TextPreprocessor(remove_stopwords=True)
        
        text = "This is a long description about red cotton t-shirts that are comfortable and stylish"
        keywords = preprocessor.extract_keywords(text, top_n=3)
        
        assert len(keywords) <= 3
        assert all(isinstance(k, str) for k in keywords)
        assert "description" in keywords or "cotton" in keywords or "comfortable" in keywords
    
    def test_query_preprocessing(self):
        preprocessor = TextPreprocessor(
            lowercase=True,
            remove_punctuation=True,
            remove_stopwords=True,
            lemmatize=True
        )
        
        query = "Looking for red shirts"
        processed = preprocessor.preprocess_query(query)
        
        # For queries, we should keep stopwords and not lemmatize (processed is a list)
        assert "looking" in processed
        assert "for" in processed
        assert "red" in processed
        assert "shirts" in processed
    
    def test_extract_product_features(self):
        preprocessor = TextPreprocessor()
        
        text = "This red t-shirt has a size M and weighs 200g. The material is cotton."
        features = preprocessor.extract_product_features(text)
        
        assert "color" in features
        assert features["color"] == "red"
        assert "size" in features
        assert features["size"] == "M"
        assert "weight" in features
        assert "200g" in features["weight"]
        assert "material" in features
        assert features["material"] == "cotton"
