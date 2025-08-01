"""
🔥 Business Logic Scoring Engine for Flipkart Grid Search System

Implements comprehensive business scoring that considers:
- Stock availability
- CTR (Click-Through Rate) 
- Price competitiveness
- Ratings & reviews
- Business metrics (conversions, revenue)
- Promotional boosts
- Personalization factors
"""

import sqlite3
import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

@dataclass
class BusinessScore:
    """Business scoring result"""
    product_id: str
    base_relevance_score: float
    business_score: float
    final_score: float
    scoring_breakdown: Dict[str, float]
    boost_factors: Dict[str, float]

class BusinessScoringEngine:
    """
    Advanced business logic scoring engine that boosts search results based on:
    1. Stock & Availability
    2. Click-through rates & user engagement  
    3. Price competitiveness
    4. Rating & review quality
    5. Revenue & conversion optimization
    6. Promotional campaigns
    7. Seller performance
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Configurable scoring weights
        self.weights = {
            'stock_boost': 2.0,           # Heavy penalty for out-of-stock
            'ctr_boost': 1.5,             # High CTR products get boost
            'rating_boost': 1.3,          # Quality products boost
            'price_competitiveness': 1.2,  # Competitive pricing boost
            'conversion_boost': 1.4,       # High-converting products
            'review_volume_boost': 1.1,    # Social proof boost  
            'seller_performance': 1.1,     # Trusted sellers
            'promotional_boost': 1.6,      # Sale/discount boost
            'flipkart_assured': 1.2,       # Flipkart assured boost
            'plus_product': 1.1,           # Plus products boost
            'delivery_speed': 1.1,         # Fast delivery boost
            'recency_boost': 1.05          # Newer products slight boost
        }
        
        # Cache for performance
        self._category_price_stats = {}
        self._category_ctr_stats = {}
        
        print("🚀 Business Scoring Engine initialized!")
        
    def score_products(self, product_ids: List[str], base_scores: Dict[str, float], 
                      user_context: Optional[Dict] = None) -> List[BusinessScore]:
        """
        Apply business scoring to products
        
        Args:
            product_ids: List of product IDs to score
            base_scores: Dict mapping product_id to base relevance score
            user_context: Optional user context for personalization
            
        Returns:
            List of BusinessScore objects sorted by final score
        """
        
        if not product_ids:
            return []
            
        # Get product data
        products_data = self._get_products_data(product_ids)
        
        # Calculate business scores
        business_scores = []
        
        for product in products_data:
            product_id = product['id']
            base_score = base_scores.get(product_id, 0.5)
            
            # Calculate individual scoring components
            scoring_breakdown = self._calculate_scoring_breakdown(product, user_context)
            
            # Calculate boost factors
            boost_factors = self._calculate_boost_factors(product, scoring_breakdown)
            
            # Calculate final business score
            business_score = self._calculate_business_score(scoring_breakdown)
            
            # Combine with base relevance score
            final_score = self._calculate_final_score(base_score, business_score, boost_factors)
            
            business_scores.append(BusinessScore(
                product_id=product_id,
                base_relevance_score=base_score,
                business_score=business_score,
                final_score=final_score,
                scoring_breakdown=scoring_breakdown,
                boost_factors=boost_factors
            ))
            
        # Sort by final score
        business_scores.sort(key=lambda x: x.final_score, reverse=True)
        
        return business_scores
        
    def _get_products_data(self, product_ids: List[str]) -> List[Dict]:
        """Get product data from database"""
        
        if not product_ids:
            return []
            
        placeholders = ','.join(['?' for _ in product_ids])
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # For dict-like access
        cursor = conn.cursor()
        
        query = f"""
            SELECT * FROM products 
            WHERE id IN ({placeholders})
        """
        
        cursor.execute(query, product_ids)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return products
        
    def _calculate_scoring_breakdown(self, product: Dict, user_context: Optional[Dict]) -> Dict[str, float]:
        """Calculate individual scoring components"""
        
        breakdown = {}
        
        # 1. Stock & Availability Score
        breakdown['stock_score'] = self._calculate_stock_score(product)
        
        # 2. CTR Score  
        breakdown['ctr_score'] = self._calculate_ctr_score(product)
        
        # 3. Rating & Review Score
        breakdown['rating_score'] = self._calculate_rating_score(product)
        
        # 4. Price Competitiveness Score
        breakdown['price_score'] = self._calculate_price_score(product)
        
        # 5. Conversion Score
        breakdown['conversion_score'] = self._calculate_conversion_score(product)
        
        # 6. Seller Performance Score
        breakdown['seller_score'] = self._calculate_seller_score(product)
        
        # 7. Promotional Score
        breakdown['promotional_score'] = self._calculate_promotional_score(product)
        
        # 8. Delivery Score
        breakdown['delivery_score'] = self._calculate_delivery_score(product)
        
        # 9. Freshness Score
        breakdown['freshness_score'] = self._calculate_freshness_score(product)
        
        # 10. Brand Trust Score
        breakdown['brand_score'] = self._calculate_brand_score(product)
        
        return breakdown
        
    def _calculate_stock_score(self, product: Dict) -> float:
        """Calculate stock availability score"""
        
        if not product.get('is_in_stock', False):
            return 0.0  # Out of stock = 0 score
            
        stock_qty = product.get('stock_quantity', 0)
        
        if stock_qty <= 0:
            return 0.1  # Low stock warning
        elif stock_qty <= 5:
            return 0.6  # Low stock
        elif stock_qty <= 20:
            return 0.8  # Medium stock
        else:
            return 1.0  # High stock
            
    def _calculate_ctr_score(self, product: Dict) -> float:
        """Calculate CTR-based score"""
        
        ctr = product.get('ctr', 0.0)
        
        if ctr <= 0:
            return 0.3  # No CTR data
            
        # Normalize CTR (typical e-commerce CTR is 2-5%)
        normalized_ctr = min(ctr / 0.05, 1.0)  # Cap at 5% CTR
        
        return 0.3 + (0.7 * normalized_ctr)  # Scale from 0.3 to 1.0
        
    def _calculate_rating_score(self, product: Dict) -> float:
        """Calculate rating & review quality score"""
        
        rating = product.get('rating', 0.0)
        review_count = product.get('review_count', 0)
        
        if rating <= 0:
            return 0.3  # No rating
            
        # Base rating score (0-5 scale -> 0-1 scale)
        rating_score = rating / 5.0
        
        # Review volume boost (more reviews = more trust)
        if review_count <= 0:
            volume_boost = 0.7  # No reviews penalty
        elif review_count <= 10:
            volume_boost = 0.8
        elif review_count <= 50:
            volume_boost = 0.9
        elif review_count <= 100:
            volume_boost = 0.95
        else:
            volume_boost = 1.0
            
        return rating_score * volume_boost
        
    def _calculate_price_score(self, product: Dict) -> float:
        """Calculate price competitiveness score"""
        
        price = product.get('price', 0)
        original_price = product.get('original_price', price)
        category = product.get('category', '')
        
        if price <= 0:
            return 0.1
            
        # Discount factor
        discount_pct = product.get('discount_percentage', 0)
        discount_boost = 1.0 + (discount_pct / 100) * 0.3  # 30% boost for 100% discount
        
        # Price competitiveness within category
        category_stats = self._get_category_price_stats(category)
        if category_stats:
            avg_price = category_stats['avg_price']
            if price <= avg_price * 0.8:  # 20% below average
                price_competitiveness = 1.0
            elif price <= avg_price:
                price_competitiveness = 0.8
            elif price <= avg_price * 1.2:
                price_competitiveness = 0.6
            else:
                price_competitiveness = 0.4
        else:
            price_competitiveness = 0.7  # Default if no category data
            
        return min(price_competitiveness * discount_boost, 1.0)
        
    def _calculate_conversion_score(self, product: Dict) -> float:
        """Calculate conversion rate score"""
        
        conversion_rate = product.get('conversion_rate', 0.0)
        
        if conversion_rate <= 0:
            return 0.3
            
        # Normalize conversion rate (typical e-commerce conversion is 2-5%)
        normalized_conversion = min(conversion_rate / 0.05, 1.0)
        
        return 0.3 + (0.7 * normalized_conversion)
        
    def _calculate_seller_score(self, product: Dict) -> float:
        """Calculate seller performance score"""
        
        seller_rating = product.get('seller_rating', 0.0)
        is_flipkart_assured = product.get('is_flipkart_assured', False)
        
        if is_flipkart_assured:
            return 1.0  # Flipkart assured = maximum trust
            
        if seller_rating <= 0:
            return 0.5  # Unknown seller
            
        return seller_rating / 5.0  # Convert 5-point scale to 0-1
        
    def _calculate_promotional_score(self, product: Dict) -> float:
        """Calculate promotional boost score"""
        
        discount_pct = product.get('discount_percentage', 0)
        is_plus_product = product.get('is_plus_product', False)
        
        score = 0.5  # Base score
        
        # Discount boost
        if discount_pct >= 50:
            score += 0.5  # Major sale
        elif discount_pct >= 30:
            score += 0.3  # Good discount
        elif discount_pct >= 10:
            score += 0.1  # Minor discount
            
        # Plus product boost
        if is_plus_product:
            score += 0.2
            
        return min(score, 1.0)
        
    def _calculate_delivery_score(self, product: Dict) -> float:
        """Calculate delivery speed score"""
        
        delivery_days = product.get('delivery_days', 7)
        
        if delivery_days <= 1:
            return 1.0  # Same day delivery
        elif delivery_days <= 2:
            return 0.9  # Next day delivery
        elif delivery_days <= 3:
            return 0.8  # 2-3 days
        elif delivery_days <= 5:
            return 0.7  # Standard delivery
        else:
            return 0.5  # Slow delivery
            
    def _calculate_freshness_score(self, product: Dict) -> float:
        """Calculate product freshness/recency score"""
        
        # For demo, assume all products are relatively fresh
        # In production, you'd use actual creation dates
        return 0.8  # Default freshness score
        
    def _calculate_brand_score(self, product: Dict) -> float:
        """Calculate brand trust score"""
        
        brand = product.get('brand', '').lower()
        
        # Premium brands get higher scores
        premium_brands = {
            'apple': 1.0, 'samsung': 0.95, 'sony': 0.9, 'lg': 0.85,
            'nike': 0.9, 'adidas': 0.9, 'puma': 0.8,
            'dell': 0.85, 'hp': 0.8, 'lenovo': 0.8
        }
        
        return premium_brands.get(brand, 0.6)  # Default brand score
        
    def _calculate_boost_factors(self, product: Dict, scoring_breakdown: Dict[str, float]) -> Dict[str, float]:
        """Calculate boost factors for final scoring"""
        
        boosts = {}
        
        # Stock boost/penalty
        if scoring_breakdown['stock_score'] <= 0.1:
            boosts['stock_penalty'] = 0.1  # Heavy penalty for out of stock
        else:
            boosts['stock_boost'] = 1.0 + (scoring_breakdown['stock_score'] * 0.2)
            
        # High CTR boost
        if scoring_breakdown['ctr_score'] >= 0.8:
            boosts['ctr_boost'] = 1.3
        else:
            boosts['ctr_boost'] = 1.0
            
        # High rating boost
        if scoring_breakdown['rating_score'] >= 0.8:
            boosts['rating_boost'] = 1.2
        else:
            boosts['rating_boost'] = 1.0
            
        # Promotional boost
        if product.get('discount_percentage', 0) >= 30:
            boosts['promotional_boost'] = 1.4
        else:
            boosts['promotional_boost'] = 1.0
            
        # Flipkart assured boost
        if product.get('is_flipkart_assured', False):
            boosts['assured_boost'] = 1.3
        else:
            boosts['assured_boost'] = 1.0
            
        return boosts
        
    def _calculate_business_score(self, scoring_breakdown: Dict[str, float]) -> float:
        """Calculate overall business score from components"""
        
        # Weighted average of all components
        weights = {
            'stock_score': 0.25,      # Most important
            'ctr_score': 0.15,
            'rating_score': 0.15,
            'price_score': 0.12,
            'conversion_score': 0.10,
            'seller_score': 0.08,
            'promotional_score': 0.05,
            'delivery_score': 0.05,
            'freshness_score': 0.03,
            'brand_score': 0.02
        }
        
        business_score = 0.0
        for component, weight in weights.items():
            business_score += scoring_breakdown.get(component, 0.5) * weight
            
        return business_score
        
    def _calculate_final_score(self, base_score: float, business_score: float, 
                             boost_factors: Dict[str, float]) -> float:
        """Calculate final combined score"""
        
        # Combine base relevance with business score
        combined_score = (base_score * 0.6) + (business_score * 0.4)
        
        # Apply boost factors
        for boost_name, boost_value in boost_factors.items():
            if 'penalty' in boost_name:
                combined_score *= boost_value  # Apply penalty
            else:
                combined_score *= min(boost_value, 2.0)  # Cap boosts at 2x
                
        return min(combined_score, 1.0)  # Cap final score at 1.0
        
    def _get_category_price_stats(self, category: str) -> Optional[Dict]:
        """Get cached price statistics for category"""
        
        if category in self._category_price_stats:
            return self._category_price_stats[category]
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price
                FROM products 
                WHERE category = ? AND is_in_stock = 1
            """, (category,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                stats = {
                    'avg_price': result[0],
                    'min_price': result[1], 
                    'max_price': result[2]
                }
                self._category_price_stats[category] = stats
                return stats
                
        except Exception as e:
            print(f"Error getting category price stats: {e}")
            
        return None
        
    def get_score_explanation(self, business_score: BusinessScore) -> Dict[str, Any]:
        """Get human-readable explanation of the score"""
        
        return {
            "product_id": business_score.product_id,
            "final_score": round(business_score.final_score, 3),
            "base_relevance": round(business_score.base_relevance_score, 3),
            "business_score": round(business_score.business_score, 3),
            "top_factors": sorted(
                business_score.scoring_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "active_boosts": {
                k: v for k, v in business_score.boost_factors.items() 
                if v > 1.0
            }
        }

# Test the scoring engine
if __name__ == "__main__":
    from pathlib import Path
    
    db_path = str(Path(__file__).parent.parent.parent / "data" / "db" / "flipkart_products.db")
    
    # Initialize scoring engine
    scoring_engine = BusinessScoringEngine(db_path)
    
    # Test with some products
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products LIMIT 10")
    product_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Create dummy base scores
    base_scores = {pid: 0.7 for pid in product_ids}
    
    # Score products
    scored_products = scoring_engine.score_products(product_ids, base_scores)
    
    print("\n🧪 TESTING BUSINESS SCORING ENGINE")
    print("=" * 60)
    
    for i, scored_product in enumerate(scored_products[:5], 1):
        explanation = scoring_engine.get_score_explanation(scored_product)
        print(f"\n{i}. Product {scored_product.product_id}")
        print(f"   Final Score: {explanation['final_score']}")
        print(f"   Base Score: {explanation['base_relevance']}")  
        print(f"   Business Score: {explanation['business_score']}")
        print(f"   Top Factors: {explanation['top_factors'][:3]}")
        
    print("\n✅ Business scoring engine test completed!")
