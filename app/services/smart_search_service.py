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

# Import hybrid search with safe fallback
try:
    from app.search.hybrid_engine import HybridSearchEngine, load_or_create_search_engine
    from app.services.hybrid_ml_service import get_hybrid_ml_service
    HYBRID_SEARCH_AVAILABLE = True
except ImportError:
    HYBRID_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class SmartSearchService:
    """
    Enhanced smart search service that combines:
    1. NLP query analysis (existing, reliable)
    2. FAISS+BM25 hybrid search (advanced semantic search)
    3. Fallback mechanisms for safety
    """
    
    def __init__(self):
        self.query_analyzer = get_query_analyzer()
        
        # Initialize hybrid search if available
        self.hybrid_search_engine = None
        self.hybrid_ml_service = None
        
        if HYBRID_SEARCH_AVAILABLE:
            try:
                self.hybrid_ml_service = get_hybrid_ml_service()
                logger.info("✅ Hybrid ML service initialized for enhanced search")
            except Exception as e:
                logger.warning(f"Hybrid ML service initialization failed: {e}")
                
        logger.info("SmartSearchService initialized with hybrid enhancement capabilities")
    
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
        in_stock: bool = True,
        use_hybrid_enhancement: bool = True
    ) -> SearchResponse:
        """
        Enhanced smart search that combines:
        1. NLP query analysis (existing reliable approach)
        2. FAISS+BM25 hybrid search enhancement (optional)
        """
        start_time = datetime.utcnow()
        
        # Set database for query analyzer
        self.query_analyzer.db = db

        # Apply spell correction - but skip for shoe-related queries to avoid bad corrections
        shoe_keywords = ['shoe', 'shoes', 'sneaker', 'sneakers', 'footwear', 'loafer', 'loafers', 'boot', 'boots', 'sandal', 'sandals']
        is_shoe_query = any(keyword in query.lower() for keyword in shoe_keywords)
        
        if is_shoe_query:
            # Skip spell correction for shoe queries to avoid "shoes for men" -> "phones top mens" issue
            corrected_query, has_typo_correction = query, False
        else:
            corrected_query, has_typo_correction = check_spelling(query)
        
        query_to_search = corrected_query if has_typo_correction else query        # STEP 1: Get baseline results using existing NLP approach (reliable)
        baseline_results = self._get_baseline_search_results(
            db, query_to_search, page, limit, category, min_price, max_price, 
            min_rating, brand, sort_by, in_stock
        )
        
        # STEP 2: Enhance with hybrid search if available and requested
        enhanced_results = baseline_results
        hybrid_used = False
        
        if use_hybrid_enhancement and HYBRID_SEARCH_AVAILABLE and self.hybrid_ml_service:
            try:
                enhanced_results = self._apply_hybrid_enhancement(
                    db, query_to_search, baseline_results, page, limit
                )
                hybrid_used = True
                logger.info(f"✅ Hybrid enhancement applied for query: {query_to_search}")
            except Exception as e:
                logger.warning(f"Hybrid enhancement failed, using baseline: {e}")
                enhanced_results = baseline_results
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Update response metadata
        enhanced_results.response_time_ms = response_time_ms
        enhanced_results.has_typo_correction = has_typo_correction
        enhanced_results.corrected_query = corrected_query if has_typo_correction else None
        
        # Add search approach metadata to query_analysis
        if enhanced_results.query_analysis:
            enhanced_results.query_analysis["search_metadata"] = {
                "baseline_search": "NLP Query Analysis",
                "hybrid_enhancement_used": hybrid_used,
                "fallback_reason": None if hybrid_used else "Hybrid not available or disabled"
            }
        
        return enhanced_results
    
    def _get_baseline_search_results(
        self,
        db: Session,
        query: str,
        page: int,
        limit: int,
        category: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        min_rating: Optional[float],
        brand: Optional[str],
        sort_by: str,
        in_stock: bool
    ) -> SearchResponse:
        """Get baseline search results using existing NLP approach (RELIABLE)"""
        
        # STEP 1: Analyze the query using our NLP analyzer
        analysis = self.query_analyzer.analyze_query(query)
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
            db, analysis, query, in_stock
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
            products = self._apply_ml_ranking(products, query)
        
        # STEP 9: Log search
        self._log_search(db, query, total_count, 0, analysis)
        
        # STEP 10: Convert to response format
        product_responses = self._convert_to_response_format(products)
        
        return SearchResponse(
            query=query,
            products=product_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=(total_count + limit - 1) // limit,
            response_time_ms=0,  # Will be set later
            has_typo_correction=False,  # Will be set later
            corrected_query=None,  # Will be set later
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
    
    def _apply_hybrid_enhancement(
        self,
        db: Session,
        query: str,
        baseline_results: SearchResponse,
        page: int,
        limit: int
    ) -> SearchResponse:
        """Apply FAISS+BM25 hybrid enhancement to baseline results"""
        
        try:
            # Check if hybrid ML service is available
            if not self.hybrid_ml_service:
                logger.warning("Hybrid ML service not available")
                return baseline_results
                
            # Get hybrid search results using the ML service
            hybrid_response = self.hybrid_ml_service.search_products(
                db=db,
                query=query,
                page=page,
                limit=limit * 2,  # Get more results for better merging
                use_ml=True,
                ml_weight=0.4  # 40% ML, 60% baseline
            )
            
            # Merge baseline and hybrid results intelligently
            enhanced_products = self._merge_search_results(
                baseline_results.products,
                hybrid_response.products,
                query
            )
            
            # Take only the requested limit
            enhanced_products = enhanced_products[:limit]
            
            # Create enhanced response
            enhanced_results = SearchResponse(
                query=baseline_results.query,
                products=enhanced_products,
                total_count=max(baseline_results.total_count, hybrid_response.total_count),
                page=page,
                limit=limit,
                total_pages=(max(baseline_results.total_count, hybrid_response.total_count) + limit - 1) // limit,
                response_time_ms=0,  # Will be set later
                has_typo_correction=baseline_results.has_typo_correction,
                corrected_query=baseline_results.corrected_query,
                filters_applied=baseline_results.filters_applied,
                query_analysis=baseline_results.query_analysis
            )
            
            # Note: We can't add custom attributes to Pydantic models
            # So we'll add the metadata to the query_analysis field
            if enhanced_results.query_analysis:
                enhanced_results.query_analysis["hybrid_metadata"] = {
                    "baseline_count": len(baseline_results.products),
                    "hybrid_count": len(hybrid_response.products),
                    "merged_count": len(enhanced_products),
                    "enhancement_method": "FAISS+BM25+NLP"
                }
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Hybrid enhancement failed: {e}")
            return baseline_results
    
    def _merge_search_results(
        self,
        baseline_products: List[ProductResponse],
        hybrid_products: List[ProductResponse],
        query: str
    ) -> List[ProductResponse]:
        """Intelligently merge baseline and hybrid search results"""
        
        # Create lookup dictionaries using product_id
        baseline_dict = {p.product_id: p for p in baseline_products}
        hybrid_dict = {p.product_id: p for p in hybrid_products}
        
        # Start with baseline results (proven to work)
        merged_results = []
        seen_ids = set()
        
        # Add baseline results first (reliable)
        for product in baseline_products:
            merged_results.append(product)
            seen_ids.add(product.product_id)
        
        # Add unique hybrid results that aren't in baseline
        for product in hybrid_products:
            if product.product_id not in seen_ids:
                merged_results.append(product)
                seen_ids.add(product.product_id)
        
        # Sort by a combination of relevance scores if available
        try:
            # Simple scoring: prioritize baseline results, then hybrid
            for i, product in enumerate(merged_results):
                if product.product_id in baseline_dict:
                    # Higher score for baseline results (more reliable)
                    score = 1.0 - (i * 0.01)
                else:
                    # Lower score for hybrid-only results
                    score = 0.5 - (i * 0.01)
                
                # Store score in a way that doesn't break the schema
                # We'll use the existing rating field or add to query analysis later
                pass
                
        except Exception as e:
            logger.warning(f"Result scoring failed: {e}")
        
        return merged_results
        
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
