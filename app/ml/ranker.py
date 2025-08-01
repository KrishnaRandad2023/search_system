"""
ML Ranker for Flipkart Search System
Production-grade ML ranking model using XGBoost with optimized features
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from typing import List, Dict, Tuple, Any, Optional
import pickle
import os
import time
import logging
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLRanker:
    """Production-grade ML ranker for reordering search results"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        objective: str = 'rank:ndcg',
        num_boost_round: int = 100,
        learning_rate: float = 0.1,
    ):
        """
        Initialize ML ranker model
        
        Args:
            model_path: Path to saved model file (if None, model will be trained)
            objective: XGBoost learning objective
            num_boost_round: Number of boosting rounds
            learning_rate: Learning rate for model training
        """
        self.model = None
        self.is_trained = False
        self.scaler = StandardScaler()
        self.feature_names = None
        
        # Model hyperparameters
        self.params = {
            'objective': objective,
            'learning_rate': learning_rate,
            'max_depth': 6,
            'min_child_weight': 1,
            'gamma': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'eval_metric': ['ndcg@10'],
            'tree_method': 'hist',  # For faster training
            'random_state': 42
        }
        
        self.num_boost_round = num_boost_round
        
        # Load model if path provided
        if model_path and os.path.exists(model_path):
            self.load(model_path)
    
    def _extract_features(self, product_data: Dict) -> List[float]:
        """
        Extract features from product and search result data
        
        This extracts features in the same order as during training
        """
        features = []
        
        # Add semantic and lexical scores
        features.append(product_data.get('semantic_score', 0))
        features.append(product_data.get('lexical_score', 0))
        
        # Add product metadata features
        features.append(float(product_data.get('price', 0)))
        features.append(float(product_data.get('rating', 0)))
        
        # Add position bias feature (higher ranks get higher scores)
        features.append(1.0 / max(1, product_data.get('position', 1)))
        
        # Add match type features (one-hot)
        match_type = product_data.get('match_type', 'hybrid')
        features.append(1.0 if match_type == 'semantic' else 0.0)
        features.append(1.0 if match_type == 'lexical' else 0.0)
        features.append(1.0 if match_type == 'hybrid' else 0.0)
        
        return features
    
    def _create_training_data(
        self, 
        search_data: List[Dict], 
        click_data: Dict[str, Dict[str, float]]
    ) -> Tuple[np.ndarray, np.ndarray, List[str], np.ndarray]:
        """
        Create training data from search results and click data
        
        Args:
            search_data: List of search results with features
            click_data: Dict mapping query to dict of product_id -> relevance score
        
        Returns:
            X: Feature matrix
            y: Target labels
            qids: Query IDs for each row
            feature_names: Names of features
        """
        # Initialize data structures
        X_data = []
        y_data = []
        qids = []
        
        # Define feature names
        feature_names = [
            'semantic_score',
            'lexical_score',
            'price',
            'rating',
            'position_bias',
            'is_semantic_match',
            'is_lexical_match',
            'is_hybrid_match'
        ]
        
        # Process each search query and its results
        for search_entry in search_data:
            query = search_entry['query']
            results = search_entry['results']
            
            # Skip if no click data for this query
            if query not in click_data:
                continue
                
            query_clicks = click_data[query]
            
            # Process each result for this query
            for result in results:
                product_id = result['id']
                
                # Extract features
                features = self._extract_features(result)
                X_data.append(features)
                
                # Get relevance score (clicks or explicit rating)
                relevance = query_clicks.get(product_id, 0.0)
                y_data.append(relevance)
                
                # Add query ID (for group-based training)
                qids.append(query)
        
        # Convert to numpy arrays
        X = np.array(X_data, dtype=np.float32)
        y = np.array(y_data, dtype=np.float32)
        
        # Map query strings to integer IDs
        unique_qids = list(set(qids))
        qid_map = {qid: i for i, qid in enumerate(unique_qids)}
        qid_ints = np.array([qid_map[qid] for qid in qids], dtype=np.int32)
        
        return X, y, feature_names, qid_ints
    
    def train(
        self, 
        search_data: List[Dict], 
        click_data: Dict[str, Dict[str, float]],
        validation_fraction: float = 0.2
    ) -> Dict:
        """
        Train the ML ranking model
        
        Args:
            search_data: List of search results with features
            click_data: Dict mapping query to dict of product_id -> relevance score
            validation_fraction: Fraction of data to use for validation
        
        Returns:
            Dictionary with training metrics
        """
        logger.info("Preparing training data...")
        X, y, qids, feature_names = self._create_training_data(search_data, click_data)
        self.feature_names = feature_names
        
        if len(X) == 0:
            raise ValueError("No training data available")
            
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Number of unique queries: {len(set(qids))}")
        
        # Normalize features
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # Split into training and validation sets
        unique_qids = np.unique(qids)
        np.random.shuffle(unique_qids)
        n_val = max(1, int(len(unique_qids) * validation_fraction))
        val_qids = set(unique_qids[:n_val])
        
        # Create masks for train/val split
        train_mask = np.array([qid not in val_qids for qid in qids])
        val_mask = ~train_mask
        
        # Create training and validation datasets
        dtrain = xgb.DMatrix(
            X_scaled[train_mask], 
            label=y[train_mask],
            feature_names=feature_names
        )
        dtrain.set_group(np.bincount(qids[train_mask]))
        
        if np.any(val_mask):
            dval = xgb.DMatrix(
                X_scaled[val_mask], 
                label=y[val_mask],
                feature_names=feature_names
            )
            dval.set_group(np.bincount(qids[val_mask]))
            watchlist = [(dtrain, 'train'), (dval, 'val')]
        else:
            watchlist = [(dtrain, 'train')]
        
        # Train model
        logger.info("Training XGBoost ranking model...")
        start_time = time.time()
        
        self.model = xgb.train(
            self.params,
            dtrain,
            num_boost_round=self.num_boost_round,
            evals=watchlist,
            early_stopping_rounds=10,
            verbose_eval=10
        )
        
        self.is_trained = True
        
        # Calculate training time
        train_time = time.time() - start_time
        logger.info(f"Model training completed in {train_time:.2f}s")
        
        # Get feature importance
        feature_names = getattr(self.model, 'feature_names', None) or self.feature_names
        if feature_names:
            importance_dict = {
                feature: score for feature, score in zip(
                    feature_names,
                    self.model.get_score(importance_type='gain').values()
                )
            }
        else:
            importance_dict = {}
        
        top_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        logger.info("Top features by importance:")
        for feature, score in top_features[:5]:
            logger.info(f"- {feature}: {score:.4f}")
            
        # Return metrics
        metrics = {
            'num_samples': len(X),
            'num_queries': len(set(qids)),
            'train_ndcg': self.model.eval(dtrain).split(':')[1],
            'feature_importance': importance_dict,
            'best_iteration': self.model.best_iteration if hasattr(self.model, 'best_iteration') else self.num_boost_round,
            'training_time': train_time
        }
        
        if np.any(val_mask):
            metrics['val_ndcg'] = self.model.eval(dval).split(':')[1]
            
        return metrics
    
    def rerank(self, results: List[Dict]) -> List[Dict]:
        """
        Rerank search results using the ML model
        
        Args:
            results: List of search results to rerank
        
        Returns:
            Reranked list of search results
        """
        if not self.is_trained or not self.model:
            logger.warning("Model not trained. Returning original results.")
            return results
            
        if not results:
            return []
        
        # Extract features
        features = []
        for result in results:
            features.append(self._extract_features(result))
            
        # Convert to feature matrix
        X = np.array(features, dtype=np.float32)
        
        # Normalize features
        X_scaled = self.scaler.transform(X)
        
        # Create DMatrix for prediction
        dmatrix = xgb.DMatrix(X_scaled, feature_names=self.feature_names)
        
        # Get predictions
        scores = self.model.predict(dmatrix)
        
        # Sort results by ML scores
        scored_results = list(zip(results, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Update position and add ML score
        reranked_results = []
        for i, (result, ml_score) in enumerate(scored_results):
            result = result.copy()  # Make a copy to avoid modifying original
            result['position'] = i + 1
            result['ml_score'] = float(ml_score)
            reranked_results.append(result)
            
        return reranked_results
    
    def save(self, model_path: str) -> None:
        """Save model to file"""
        if not self.is_trained or not self.model:
            raise ValueError("Model not trained. Nothing to save.")
            
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save model data
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'params': self.params,
                'num_boost_round': self.num_boost_round
            }, f)
            
        logger.info(f"Model saved to {model_path}")
        
    def load(self, model_path: str) -> None:
        """Load model from file"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.params = data.get('params', self.params)
        self.num_boost_round = data.get('num_boost_round', self.num_boost_round)
        self.is_trained = True
        
        logger.info(f"Model loaded from {model_path}")


def generate_synthetic_training_data(
    product_df: pd.DataFrame,
    num_queries: int = 100
) -> Tuple[List[Dict], Dict[str, Dict[str, float]]]:
    """
    Generate synthetic training data for the ML ranker
    
    Args:
        product_df: DataFrame containing product information
        num_queries: Number of synthetic queries to generate
    
    Returns:
        search_data: List of search results with features
        click_data: Dict mapping query to dict of product_id -> relevance score
    """
    import random
    
    # Generate common e-commerce search queries
    categories = product_df['category'].unique().tolist()
    brands = product_df['brand'].unique().tolist()[:20]  # Take top brands
    
    query_templates = [
        "best {category}",
        "{brand} {category}",
        "cheap {category}",
        "high quality {category}",
        "{category} under {price}",
        "{brand} products",
        "{specific_product}",
    ]
    
    price_points = ["500", "1000", "2000", "5000", "10000"]
    
    # Generate queries
    queries = []
    for _ in range(num_queries):
        template = random.choice(query_templates)
        
        if "{category}" in template:
            template = template.replace("{category}", random.choice(categories))
            
        if "{brand}" in template:
            template = template.replace("{brand}", random.choice(brands))
            
        if "{price}" in template:
            template = template.replace("{price}", random.choice(price_points))
            
        if "{specific_product}" in template:
            # Pick a random product title
            product = product_df.sample(1).iloc[0]
            title_words = product['title'].split()[:3]  # Take first 3 words
            template = " ".join(title_words)
            
        queries.append(template)
    
    # Generate synthetic search results and click data
    search_data = []
    click_data = {}
    
    for query in queries:
        # Select random products as results
        results_count = random.randint(5, 20)
        result_products = product_df.sample(results_count)
        
        # Generate search results
        results = []
        for i, (_, product) in enumerate(result_products.iterrows()):
            # Calculate synthetic scores based on query-product match
            query_tokens = set(query.lower().split())
            title_tokens = set(str(product['title']).lower().split())
            overlap = len(query_tokens.intersection(title_tokens))
            
            semantic_score = 0.3 + 0.7 * random.random()  # Random score between 0.3 and 1
            lexical_score = min(1.0, 0.2 + 0.3 * overlap + 0.3 * random.random())
            
            # Adjust scores based on query-product relevance
            if query.lower().startswith("best"):
                semantic_score *= product['rating'] / 5.0
                
            if "cheap" in query.lower() or "under" in query.lower():
                # Higher score for lower price
                price_factor = max(0.1, 1.0 - (product['price'] / 10000))
                semantic_score *= 0.3 + 0.7 * price_factor
                
            if product['brand'].lower() in query.lower():
                semantic_score = min(1.0, semantic_score * 1.5)
                lexical_score = min(1.0, lexical_score * 1.5)
                
            # Determine match type
            if semantic_score > 0.7 and lexical_score > 0.7:
                match_type = 'hybrid'
            elif semantic_score > lexical_score:
                match_type = 'semantic'
            else:
                match_type = 'lexical'
                
            # Create result entry
            results.append({
                'id': product['product_id'],
                'title': product['title'],
                'description': product['description'],
                'category': product['category'],
                'brand': product['brand'],
                'price': product['price'],
                'rating': product['rating'],
                'semantic_score': semantic_score,
                'lexical_score': lexical_score,
                'combined_score': 0.6 * semantic_score + 0.4 * lexical_score,
                'position': i + 1,
                'match_type': match_type
            })
            
        # Sort results by combined score
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Update positions after sorting
        for i, result in enumerate(results):
            result['position'] = i + 1
            
        # Add to search data
        search_data.append({
            'query': query,
            'results': results
        })
        
        # Generate synthetic click data (position bias + relevance)
        query_clicks = {}
        
        # Simulate position bias (higher positions more likely to be clicked)
        for result in results:
            product_id = result['id']
            position = result['position']
            
            # Click probability decreases with position
            base_click_prob = max(0.05, 1.0 - 0.1 * position)
            
            # Relevance increases click probability
            relevance_factor = 0.5 + 0.5 * (result['combined_score'])
            
            # Product quality factor
            quality_factor = 0.5 + 0.5 * (result['rating'] / 5.0)
            
            # Final click probability
            click_prob = base_click_prob * relevance_factor * quality_factor
            
            # Convert to relevance score (0-4 scale for NDCG)
            if random.random() < click_prob:
                # Clicked: assign relevance score based on factors
                raw_score = relevance_factor * quality_factor * 4.0
                # Add some noise
                relevance = min(4.0, max(1.0, raw_score + random.uniform(-0.5, 0.5)))
                query_clicks[product_id] = relevance
        
        # Add to click data
        click_data[query] = query_clicks
    
    logger.info(f"Generated {len(search_data)} synthetic queries with results")
    logger.info(f"Generated click data for {len(click_data)} queries")
    
    return search_data, click_data
