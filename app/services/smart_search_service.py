"""
Smart Search Service - Integrates NLP Query Analysis with Product Search

This service:
1. Uses our query analyzer to understand search intent
2. Applies intelligent filtering based on extracted entities
3. Provides better search results using NLP insights
4. Handles price ranges, brands, categories automatically
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.db.models import Product, SearchLog
from app.schemas.product import ProductResponse, SearchResponse
from app.services.query_analyzer_service import get_query_analyzer, QueryAnalyzerService
from app.utils.spell_checker import check_spelling

# Import ML service with safe fallback
try:
    from app.services.ml_service import get_ml_service
    ML_SERVICE_AVAILABLE = True
except ImportError:
    ML_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SmartSearchService:
    """
    Smart search service that uses NLP query analysis for better search results
    """
    
    def __init__(self):
        self.query_analyzer = get_query_analyzer()
        logger.info("SmartSearchService initialized")
    
    def search_products(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 20,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        brand: Optional[str] = None,
        sort_by: str = "relevance",
        in_stock: bool = True
    ) -> SearchResponse:
        """
        Smart search using NLP query analysis
        """
        start_time = datetime.utcnow()
        
        # Set database for query analyzer
        self.query_analyzer.db = db
        
        # Apply spell correction
        corrected_query, has_typo_correction = check_spelling(query)
        query_to_search = corrected_query if has_typo_correction else query
        
        # STEP 1: Analyze the query using our NLP analyzer
        analysis = self.query_analyzer.analyze_query(query_to_search)
        logger.info(f"Query analysis: {analysis.query_type}, entities: {analysis.entities}")
        
        # STEP 2: Extract filters from query analysis
        extracted_filters = self._extract_filters_from_analysis(analysis)
        
        # STEP 3: Apply extracted filters if not explicitly provided
        if not min_price and not max_price and analysis.price_range:
            min_price, max_price = analysis.price_range
            
        if not brand and analysis.brands:
            brand = analysis.brands[0]  # Use first brand found
            
        if not category and analysis.categories:
            category = analysis.categories[0]  # Use first category found
        
        # STEP 4: Build smart search query
        search_query = self._build_smart_search_query(
            db, analysis, query_to_search, in_stock
        )
        
        # STEP 5: Apply additional filters
        search_query = self._apply_filters(
            search_query, category, brand, min_price, max_price, min_rating
        )
        
        # STEP 6: Apply intelligent sorting
        search_query = self._apply_smart_sorting(search_query, sort_by, analysis)
        
        # STEP 7: Get results with pagination
        total_count = search_query.count()
        offset = (page - 1) * limit
        products = search_query.offset(offset).limit(limit).all()
        
        # STEP 8: Apply ML ranking if available
        if ML_SERVICE_AVAILABLE and len(products) > 1:
            products = self._apply_ml_ranking(products, query_to_search)
        
        # STEP 9: Calculate response time and log
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        self._log_search(db, query, total_count, response_time_ms, analysis)
        
        # STEP 10: Convert to response format
        product_responses = self._convert_to_response_format(products)
        
        return SearchResponse(
            query=query,
            corrected_query=corrected_query if has_typo_correction else None,
            products=product_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=(total_count + limit - 1) // limit,
            response_time_ms=response_time_ms,
            filters_applied={
                "category": category,
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
                "extracted_from_query": extracted_filters
            },
            query_analysis={
                "query_type": analysis.query_type,
                "sentiment": analysis.sentiment,
                "brands_detected": analysis.brands,
                "categories_detected": analysis.categories,
                "price_range_detected": analysis.price_range,
                "modifiers": analysis.modifiers
            }
        )
    
    def _extract_filters_from_analysis(self, analysis) -> Dict[str, Any]:
        """Extract filters from query analysis"""
        filters = {}
        
        if analysis.price_range:
            min_price, max_price = analysis.price_range
            filters["price_range"] = {"min": min_price, "max": max_price}
            
        if analysis.brands:
            filters["brands"] = analysis.brands
            
        if analysis.categories:
            filters["categories"] = analysis.categories
            
        if analysis.modifiers:
            filters["modifiers"] = analysis.modifiers
            
        return filters
    
    def _build_smart_search_query(self, db: Session, analysis, query: str, in_stock: bool):
        """Build search query based on NLP analysis"""
        base_query = db.query(Product).filter(Product.is_available == True)
        
        if in_stock:
            base_query = base_query.filter(Product.stock_quantity > 0)
        
        # Generate intelligent search terms based on analysis
        search_terms = self._generate_smart_search_terms(analysis, query)
        
        # Build search conditions
        search_conditions = []
        for term in search_terms:
            term_conditions = [
                Product.title.ilike(f"%{term}%"),
                Product.description.ilike(f"%{term}%"),
                Product.brand.ilike(f"%{term}%"),
                Product.category.ilike(f"%{term}%"),
                Product.subcategory.ilike(f"%{term}%")
            ]
            search_conditions.extend(term_conditions)
        
        if search_conditions:
            return base_query.filter(or_(*search_conditions))
        else:
            # Fallback to basic search
            return base_query.filter(
                or_(
                    Product.title.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    Product.brand.ilike(f"%{query}%"),
                    Product.category.ilike(f"%{query}%")
                )
            )
    
    def _generate_smart_search_terms(self, analysis, original_query: str) -> List[str]:
        """Generate intelligent search terms based on analysis"""
        terms = set([original_query.lower()])
        
        # Add detected brands
        for brand in analysis.brands:
            terms.add(brand.lower())
            
        # Add detected categories
        for category in analysis.categories:
            terms.add(category.lower())
            
        # Add modifier combinations
        if analysis.modifiers and analysis.categories:
            for modifier in analysis.modifiers:
                for category in analysis.categories:
                    terms.add(f"{modifier} {category}")
                    
        # Add brand + category combinations
        if analysis.brands and analysis.categories:
            for brand in analysis.brands:
                for category in analysis.categories:
                    terms.add(f"{brand} {category}")
        
        return list(terms)
    
    def _apply_filters(self, query, category, brand, min_price, max_price, min_rating):
        """Apply additional filters to the query"""
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
            
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
            
        if min_price is not None:
            query = query.filter(Product.current_price >= min_price)
            
        if max_price is not None:
            query = query.filter(Product.current_price <= max_price)
            
        if min_rating is not None:
            query = query.filter(Product.rating >= min_rating)
            
        return query
    
    def _apply_smart_sorting(self, query, sort_by: str, analysis):
        """Apply intelligent sorting based on query analysis"""
        if sort_by == "price_low":
            return query.order_by(Product.current_price.asc())
        elif sort_by == "price_high":
            return query.order_by(Product.current_price.desc())
        elif sort_by == "rating":
            return query.order_by(Product.rating.desc(), Product.num_ratings.desc())
        elif sort_by == "popularity":
            return query.order_by(Product.num_ratings.desc(), Product.rating.desc())
        else:  # relevance with sentiment analysis
            if analysis.sentiment == "positive":
                # For positive sentiment (best, top), prioritize high ratings
                return query.order_by(
                    Product.rating.desc(),
                    Product.is_bestseller.desc(),
                    Product.num_ratings.desc()
                )
            elif analysis.sentiment == "negative" or "budget" in analysis.modifiers:
                # For budget queries, prioritize price
                return query.order_by(
                    Product.current_price.asc(),
                    Product.rating.desc()
                )
            else:
                # Default relevance
                return query.order_by(
                    Product.is_bestseller.desc(),
                    Product.is_featured.desc(),
                    Product.rating.desc(),
                    Product.num_ratings.desc()
                )
    
    def _apply_ml_ranking(self, products, query: str):
        """Apply ML ranking if available"""
        try:
            ml_service = get_ml_service()
            if ml_service.is_ml_available():
                # Convert to dict format for ML service
                product_dicts = []
                for product in products:
                    product_dict = {
                        'title': product.title,
                        'brand': product.brand,
                        'category': product.category,
                        'price': product.current_price,
                        'rating': product.rating,
                        'num_ratings': product.num_ratings,
                        'is_bestseller': product.is_bestseller,
                        'stock': product.stock_quantity,
                        'discount_percentage': product.discount_percent or 0
                    }
                    product_dicts.append(product_dict)
                
                # Apply ML ranking
                ranked_products = ml_service.rank_products(product_dicts, query)
                
                # Create ML score mapping
                ml_scores = {}
                for i, ranked_product in enumerate(ranked_products):
                    if i < len(products):
                        ml_score = ranked_product.get('ml_score', 0.5)
                        ml_scores[products[i].product_id] = ml_score
                
                # Sort by ML scores
                products.sort(key=lambda p: ml_scores.get(p.product_id, 0.5), reverse=True)
                
        except Exception as e:
            logger.warning(f"ML ranking failed, using original order: {e}")
            
        return products
    
    def _convert_to_response_format(self, products) -> List[ProductResponse]:
        """Convert SQLAlchemy products to response format"""
        return [
            ProductResponse(
                product_id=product.product_id,
                title=product.title,
                description=product.description,
                category=product.category,
                subcategory=product.subcategory,
                brand=product.brand,
                price=product.current_price,
                original_price=product.original_price,
                discount_percentage=product.discount_percent,
                rating=product.rating,
                num_ratings=product.num_ratings,
                num_reviews=product.num_ratings,
                stock=product.stock_quantity,
                is_bestseller=product.is_bestseller,
                is_new_arrival=product.is_featured,
                image_url=product.images
            )
            for product in products
        ]
    
    def _log_search(self, db: Session, query: str, total_count: int, response_time_ms: float, analysis):
        """Log search query with analysis information"""
        try:
            search_log = SearchLog(
                query=query,
                results_count=total_count,
                response_time_ms=response_time_ms,
                metadata={
                    "query_type": analysis.query_type,
                    "sentiment": analysis.sentiment,
                    "brands_detected": analysis.brands,
                    "categories_detected": analysis.categories,
                    "price_range_detected": analysis.price_range,
                    "modifiers": analysis.modifiers
                }
            )
            db.add(search_log)
            db.commit()
        except Exception as e:
            logger.error(f"Could not log search query: {e}")


# Factory function for dependency injection
def get_smart_search_service() -> SmartSearchService:
    """Get SmartSearchService instance"""
    return SmartSearchService()
