"""
Search API v2 for Frontend Integration
Enhanced with Hybrid Search Capabilities
"""

from typing import List, Optional, Dict, Any
import time
import json
import os
import math
import time
import os
import json
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Database imports
from app.db.database import get_db

# Smart search service import
try:
    from app.services.smart_search_service import SmartSearchService
    SMART_SEARCH_AVAILABLE = True
except ImportError:
    SMART_SEARCH_AVAILABLE = False
    print("Warning: Smart search service not available")

# Add spell correction imports
try:
    from symspellpy import SymSpell, Verbosity
    SYMSPELL_AVAILABLE = True
except ImportError:
    SYMSPELL_AVAILABLE = False
    print("Warning: symspellpy not available, spell correction will be disabled")

# Request Models
class ClickTrackingPayload(BaseModel):
    query: str
    product_id: str
    position: int
    timestamp: Optional[str] = None

# Response Models
class ProductResult(BaseModel):
    id: str
    title: str
    description: str
    category: str
    subcategory: str = ""
    brand: str
    current_price: float  # Changed from 'price' to match JSON data
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    rating: float
    num_ratings: int  # Changed from 'reviews_count' to match JSON data
    availability: str = "in_stock"
    image_url: Optional[str] = None
    features: List[str] = []
    specifications: str = "{}"  # Changed to string to match JSON data
    relevance_score: float
    popularity_score: float
    business_score: float
    final_score: float
    # New ranking fields
    final_ranking_score: Optional[float] = None
    exact_match_bonus: Optional[float] = None
    brand_boost: Optional[float] = None

class SearchMetadata(BaseModel):
    query: str
    search_type: str = "hybrid"
    response_time_ms: float
    has_typo_correction: bool = False
    corrected_query: Optional[str] = None
    semantic_similarity: Optional[float] = None

class AggregationItem(BaseModel):
    name: str
    count: int

class SearchResponse(BaseModel):
    products: List[ProductResult]
    total_results: int
    page: int
    per_page: int
    total_pages: int
    filters_applied: Dict[str, Any] = {}
    search_metadata: SearchMetadata
    aggregations: Dict[str, List[AggregationItem]]

# Create routers
router = APIRouter(prefix="/api/v2", tags=["search"])
# Create a separate router for v1 endpoints (for compatibility)
v1_router = APIRouter(prefix="/api/v1", tags=["analytics"])

# Initialize smart search service
_smart_search_service = None

def get_smart_search_service() -> SmartSearchService:
    """Get or create smart search service instance"""
    global _smart_search_service
    if _smart_search_service is None and SMART_SEARCH_AVAILABLE:
        _smart_search_service = SmartSearchService()
    return _smart_search_service

# Load product data
PRODUCTS_DATA = []

def load_product_data():
    """Load product data from JSON file and database"""
    global PRODUCTS_DATA
    if PRODUCTS_DATA:  # Already loaded
        return PRODUCTS_DATA
        
    try:
        # First try to load from database (which has our 17K products)
        from app.db.database import get_db
        from app.db.models import Product
        from sqlalchemy.orm import Session
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Query all products from database
        products = db.query(Product).filter(Product.is_available == True).all()
        
        # Convert to dict format
        for product in products:
            tags = getattr(product, 'tags', None)
            features = tags.split(',') if tags and tags.strip() else []
            
            product_dict = {
                'id': product.product_id,
                'title': product.title,
                'description': product.description or '',
                'category': product.category,
                'subcategory': product.subcategory or '',
                'brand': product.brand,
                'current_price': product.current_price,
                'original_price': product.original_price,
                'discount_percent': product.discount_percent,
                'rating': product.rating,
                'num_ratings': product.num_ratings,
                'is_available': product.is_available,
                'specifications': product.specifications or '{}',
                'features': features,
                'image_url': product.images
            }
            PRODUCTS_DATA.append(product_dict)
        
        db.close()
        print(f"Loaded {len(PRODUCTS_DATA)} products from database for search v2")
        
    except Exception as e:
        print(f"Error loading from database: {e}")
        # Fallback to JSON file
        try:
            json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "products.json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    PRODUCTS_DATA = json.load(f)[:1000]  # Limit for demo
                    print(f"Loaded {len(PRODUCTS_DATA)} products from JSON for search v2")
        except Exception as e2:
            print(f"Error loading product data from JSON: {e2}")
            PRODUCTS_DATA = []
    
    return PRODUCTS_DATA

# Initialize spell checker
SPELL_CHECKER = None
def init_spell_checker():
    """Initialize spell checker with product vocabulary"""
    global SPELL_CHECKER
    if SPELL_CHECKER is not None:  # Already initialized
        return SPELL_CHECKER
        
    if not SYMSPELL_AVAILABLE:
        return None
    
    products = load_product_data()  # Ensure products are loaded
    
    spell_checker = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    
    # Build dictionary from product data
    word_counts = {}
    for product in products:
        # Add words from title, brand, category
        words = []
        if product.get('title'):
            words.extend(product['title'].lower().split())
        if product.get('brand'):
            words.extend(product['brand'].lower().split())
        if product.get('category'):
            words.extend(product['category'].lower().split())
        if product.get('subcategory'):
            words.extend(product['subcategory'].lower().split())
            
        for word in words:
            # Clean word (remove special characters)
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 2:  # Skip very short words
                word_counts[word] = word_counts.get(word, 0) + 1
    
    # Add words to spell checker
    for word, count in word_counts.items():
        spell_checker.create_dictionary_entry(word, count)
    
    print(f"Spell checker initialized with {len(word_counts)} words")
    SPELL_CHECKER = spell_checker
    return spell_checker

def check_spelling(query: str) -> tuple[str, bool]:
    """Check spelling and return corrected query if needed"""
    spell_checker = init_spell_checker()  # Lazy initialization
    if not spell_checker:
        return query, False
    
    words = query.lower().split()
    corrected_words = []
    has_correction = False
    
    for word in words:
        # Skip numbers and very short words
        if word.isdigit() or len(word) < 3:
            corrected_words.append(word)
            continue
            
        # Get spell suggestions
        suggestions = spell_checker.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        
        if suggestions and suggestions[0].term != word:
            # Only use correction if it's significantly more frequent
            if suggestions[0].count > 5:  # Threshold for common words
                corrected_words.append(suggestions[0].term)
                has_correction = True
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    
    corrected_query = ' '.join(corrected_words)
    return corrected_query, has_correction

def parse_query_with_price(query: str) -> tuple[str, Optional[float], Optional[float]]:
    """Parse query to extract search terms and price constraints"""
    import re
    
    # Convert to lowercase for matching
    query_lower = query.lower().strip()
    
    # Initialize extracted values
    search_terms = query_lower
    min_price = None
    max_price = None
    
    # Patterns to match price expressions
    price_patterns = [
        # "under X", "below X", "less than X"
        (r'\b(?:under|below|less\s+than|<)\s*(\d+)\b', 'max'),
        # "above X", "over X", "more than X"  
        (r'\b(?:above|over|more\s+than|>)\s*(\d+)\b', 'min'),
        # "between X and Y", "X to Y"
        (r'\b(?:between|from)\s*(\d+)\s*(?:and|to|-)\s*(\d+)\b', 'range'),
        # "around X", "about X" (±20%)
        (r'\b(?:around|about|near)\s*(\d+)\b', 'around'),
    ]
    
    # Try to match price patterns
    for pattern, price_type in price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if price_type == 'max':
                max_price = float(match.group(1))
                # Remove the matched price expression from search terms
                search_terms = re.sub(pattern, '', query_lower).strip()
            elif price_type == 'min':
                min_price = float(match.group(1))
                search_terms = re.sub(pattern, '', query_lower).strip()
            elif price_type == 'range':
                min_price = float(match.group(1))
                max_price = float(match.group(2))
                # Ensure min <= max
                if min_price > max_price:
                    min_price, max_price = max_price, min_price
                search_terms = re.sub(pattern, '', query_lower).strip()
            elif price_type == 'around':
                center_price = float(match.group(1))
                # ±20% range
                min_price = center_price * 0.8
                max_price = center_price * 1.2  
                search_terms = re.sub(pattern, '', query_lower).strip()
            break
    
    # Clean up search terms - remove extra spaces and common words
    search_terms = re.sub(r'\s+', ' ', search_terms).strip()
    # Remove common price-related words that might remain
    search_terms = re.sub(r'\b(?:price|cost|rupees?|rs\.?|inr|₹)\b', '', search_terms).strip()
    
    return search_terms, min_price, max_price

def search_products(query: str, category: Optional[str] = None, brand: Optional[str] = None, 
                   min_price: Optional[float] = None, max_price: Optional[float] = None,
                   min_rating: Optional[float] = None) -> List[Dict]:
    """Enhanced search implementation with natural language price parsing and semantic search"""
    
    products = load_product_data()  # Ensure products are loaded
    
    # Parse query for price constraints if not explicitly provided
    if min_price is None and max_price is None:
        search_terms, parsed_min_price, parsed_max_price = parse_query_with_price(query)
        if parsed_min_price is not None:
            min_price = parsed_min_price
        if parsed_max_price is not None:
            max_price = parsed_max_price
        query_for_matching = search_terms
    else:
        query_for_matching = query.lower().strip()
    
    # Enhanced semantic search mappings for better shoe search
    semantic_mappings = {
        'shoes': ['footwear', 'sneakers', 'loafers', 'boots', 'sandals', 'flip-flops', 'fashion'],
        'shoe': ['footwear', 'sneakers', 'loafers', 'boots', 'sandals', 'flip-flops', 'fashion'],
        'sneakers': ['footwear', 'casual shoes', 'sports shoes', 'running shoes', 'fashion'],
        'loafers': ['footwear', 'formal shoes', 'casual shoes', 'fashion'],
        'boots': ['footwear', 'winter boots', 'leather boots', 'fashion'],
        'sandals': ['footwear', 'summer shoes', 'casual shoes', 'fashion'],
        'footwear': ['shoes', 'sneakers', 'loafers', 'boots', 'sandals', 'fashion'],
        'mobile': ['phone', 'smartphone', 'cell phone'],
        'laptop': ['computer', 'notebook', 'pc'],
        'tv': ['television', 'smart tv', 'led tv'],
    }
    
    # Build expanded search terms
    search_variants = [query_for_matching]
    query_words = query_for_matching.split()
    
    for word in query_words:
        if word in semantic_mappings:
            search_variants.extend(semantic_mappings[word])
            # Also add combinations with other words
            for other_word in query_words:
                if other_word != word:
                    for variant in semantic_mappings[word]:
                        search_variants.append(f"{variant} {other_word}")
                        search_variants.append(f"{other_word} {variant}")
    
    results = []
    
    for i, product in enumerate(products):
        score = 0.0
        max_variant_score = 0.0
        
        # Test all search variants to find the best match
        for variant in search_variants:
            variant_score = 0.0
            
            # Title matching
            title = product.get('title', '').lower()
            if variant in title:
                variant_score += 1.0
                if title.startswith(variant):
                    variant_score += 0.5
            
            # Category matching  
            product_category = product.get('category', '').lower()
            if variant in product_category:
                variant_score += 0.7
                
            # Subcategory matching - important for shoes
            product_subcategory = product.get('subcategory', '').lower()
            if variant in product_subcategory:
                variant_score += 0.8
                
            # Brand matching
            product_brand = product.get('brand', '').lower()
            if variant in product_brand:
                variant_score += 0.8
            
            # Description matching
            description = product.get('description', '').lower()
            if variant in description:
                variant_score += 0.3
                
            # Word-based matching for better results
            variant_words = variant.split()
            for word in variant_words:
                if len(word) > 2:  # Skip very short words
                    if word in title:
                        variant_score += 0.2
                    if word in product_category:
                        variant_score += 0.15
                    if word in product_subcategory:
                        variant_score += 0.2
                    if word in product_brand:
                        variant_score += 0.2
                    if word in description:
                        variant_score += 0.1
            
            # Keep the highest score from all variants
            max_variant_score = max(max_variant_score, variant_score)
        
        score = max_variant_score
        
        # Get product attributes for filtering (use original product data)
        title = product.get('title', '').lower()
        product_category = product.get('category', '').lower()
        product_subcategory = product.get('subcategory', '').lower()
        product_brand = product.get('brand', '').lower()
        description = product.get('description', '').lower()
            
        # Apply filters
        if category and category.lower() not in product_category:
            continue
        if brand and brand.lower() != product_brand:
            continue
        if min_price and product.get('current_price', 0) < min_price:
            continue
        if max_price and product.get('current_price', float('inf')) > max_price:
            continue
        if min_rating and product.get('rating', 0) < min_rating:
            continue
            
        if score > 0:
            # Calculate scores
            relevance_score = score
            popularity_score = product.get('rating', 0) * 0.2
            business_score = min(1.0, product.get('current_price', 0) / 10000)  # Normalize price
            final_score = relevance_score + popularity_score + business_score
            
            result = {
                **product,
                'id': str(i),
                'subcategory': product.get('subcategory', ''),
                'num_ratings': int(product.get('num_ratings', 100)),
                'availability': 'in_stock' if product.get('is_available', True) else 'out_of_stock',
                'features': product.get('features', []),
                'specifications': product.get('specifications', '{}'),
                'relevance_score': relevance_score,
                'popularity_score': popularity_score, 
                'business_score': business_score,
                'final_score': final_score
            }
            results.append(result)
    
    # Sort by final score
    results.sort(key=lambda x: x['final_score'], reverse=True)
    return results

def advanced_ranking(results: List[Dict], query: str, sort_by: str = "relevance") -> List[Dict]:
    """
    Advanced ranking algorithm that combines multiple signals
    """
    if not results:
        return results
    
    query_words = query.lower().split()
    
    for result in results:
        # Enhanced relevance scoring
        title_lower = result.get('title', '').lower()
        brand_lower = result.get('brand', '').lower()
        category_lower = result.get('category', '').lower()
        
        # 1. Exact phrase matching bonus
        if query.lower() in title_lower:
            result['exact_match_bonus'] = 2.0
        elif any(word in title_lower for word in query_words):
            result['exact_match_bonus'] = 1.0
        else:
            result['exact_match_bonus'] = 0.0
            
        # 2. Brand popularity boost
        brand_popularity = {
            'apple': 1.5, 'samsung': 1.4, 'oneplus': 1.3, 'xiaomi': 1.2,
            'nike': 1.4, 'adidas': 1.4, 'puma': 1.2, 'reebok': 1.1,
            'sony': 1.3, 'bose': 1.3, 'jbl': 1.2, 'boat': 1.1,
            'lg': 1.2, 'whirlpool': 1.1, 'godrej': 1.1
        }
        result['brand_boost'] = brand_popularity.get(brand_lower, 1.0)
        
        # 3. Price-quality ratio
        price = result.get('current_price', 0)
        rating = result.get('rating', 0)
        if price > 0 and rating > 0:
            # Higher rating with reasonable price gets boost
            result['price_quality_ratio'] = (rating / 5.0) * (1.0 / (1.0 + price / 10000))
        else:
            result['price_quality_ratio'] = 0.5
            
        # 4. Customer validation score
        num_ratings = result.get('num_ratings', 0)
        if num_ratings > 1000:
            result['validation_score'] = 1.5
        elif num_ratings > 100:
            result['validation_score'] = 1.2
        elif num_ratings > 10:
            result['validation_score'] = 1.0
        else:
            result['validation_score'] = 0.8
            
        # 5. Availability boost
        is_available = result.get('is_available', True)
        stock_quantity = result.get('stock_quantity', 0)
        if is_available and stock_quantity > 10:
            result['availability_boost'] = 1.2
        elif is_available:
            result['availability_boost'] = 1.0
        else:
            result['availability_boost'] = 0.5
            
        # 6. Discount attractiveness
        original_price = result.get('original_price', price)
        if original_price > price:
            discount_percent = ((original_price - price) / original_price) * 100
            if discount_percent > 30:
                result['discount_boost'] = 1.3
            elif discount_percent > 15:
                result['discount_boost'] = 1.1
            else:
                result['discount_boost'] = 1.0
        else:
            result['discount_boost'] = 1.0
            
        # Calculate final ranking score
        base_relevance = result.get('relevance_score', 0)
        base_popularity = result.get('popularity_score', 0)
        base_business = result.get('business_score', 0)
        
        # Combine all factors with proper weights
        final_ranking_score = (
            base_relevance * 0.3 +
            base_popularity * 0.2 +
            base_business * 0.1 +
            result.get('exact_match_bonus', 0) * 0.15 +
            result.get('brand_boost', 1.0) * 0.1 +
            result.get('price_quality_ratio', 0.5) * 0.05 +
            result.get('validation_score', 1.0) * 0.05 +
            result.get('availability_boost', 1.0) * 0.03 +
            result.get('discount_boost', 1.0) * 0.02
        )
        
        result['final_ranking_score'] = final_ranking_score
    
    # Sort based on the requested sort method
    if sort_by == "price_low":
        results.sort(key=lambda x: x.get('current_price', float('inf')))
    elif sort_by == "price_high":
        results.sort(key=lambda x: x.get('current_price', 0), reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda x: (x.get('rating', 0), x.get('num_ratings', 0)), reverse=True)
    elif sort_by == "popularity":
        results.sort(key=lambda x: x.get('num_ratings', 0), reverse=True)
    elif sort_by == "newest":
        # For now, use a mix of factors since we don't have launch date
        results.sort(key=lambda x: (x.get('final_ranking_score', 0), x.get('num_ratings', 0)), reverse=True)
    else:  # relevance (default)
        results.sort(key=lambda x: x['final_ranking_score'], reverse=True)
    
    return results

def calculate_aggregations(products: List[Dict]) -> Dict[str, List[AggregationItem]]:
    """Calculate search aggregations"""
    categories = {}
    brands = {}
    price_ranges = {"0-1000": 0, "1000-5000": 0, "5000-20000": 0, "20000+": 0}
    ratings = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    
    for product in products:
        # Categories
        category = product.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
        
        # Brands
        brand = product.get('brand', 'Unknown')
        brands[brand] = brands.get(brand, 0) + 1
        
        # Price ranges
        price = product.get('current_price', 0)
        if price < 1000:
            price_ranges["0-1000"] += 1
        elif price < 5000:
            price_ranges["1000-5000"] += 1
        elif price < 20000:
            price_ranges["5000-20000"] += 1
        else:
            price_ranges["20000+"] += 1
            
        # Ratings
        rating = int(product.get('rating', 0))
        if rating in ratings:
            ratings[rating] += 1
    
    return {
        "categories": [AggregationItem(name=k, count=v) for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]],
        "brands": [AggregationItem(name=k, count=v) for k, v in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]],
        "price_ranges": [AggregationItem(name=k, count=v) for k, v in price_ranges.items() if v > 0],
        "ratings": [AggregationItem(name=str(k), count=v) for k, v in ratings.items() if v > 0]
    }

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    page: int = Query(default=1, description="Page number", ge=1),
    per_page: int = Query(default=20, description="Results per page", le=100),
    sort_by: str = Query(default="relevance", description="Sort by"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    min_price: Optional[float] = Query(default=None, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, description="Maximum price"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating"),
    use_hybrid: bool = Query(default=True, description="Enable hybrid search enhancement"),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Enhanced search with hybrid capabilities:
    1. Uses proven NLP-based search as baseline (reliable)
    2. Enhances with FAISS+BM25 semantic search when available
    3. Falls back gracefully if hybrid search fails
    """
    start_time = time.time()
    
    try:
        # Try to use enhanced smart search service first
        if SMART_SEARCH_AVAILABLE and use_hybrid:
            try:
                smart_service = get_smart_search_service()
                if smart_service:
                    # Use enhanced smart search with hybrid capabilities
                    smart_results = smart_service.search_products(
                        db=db,
                        query=q,
                        page=page,
                        limit=per_page,
                        category=category,
                        brand=brand,
                        min_price=min_price,
                        max_price=max_price,
                        min_rating=min_rating,
                        sort_by=sort_by,
                        use_hybrid_enhancement=True
                    )
                    
                    # Convert to frontend format
                    return _convert_smart_response_to_v2(smart_results, start_time)
                    
            except Exception as e:
                print(f"Smart search failed, falling back to simple search: {e}")
        
        # Fallback to original JSON-based search
        # Check for spelling corrections - but skip for shoe-related queries to avoid bad corrections
        shoe_keywords = ['shoe', 'shoes', 'sneaker', 'sneakers', 'footwear', 'loafer', 'loafers', 'boot', 'boots', 'sandal', 'sandals']
        is_shoe_query = any(keyword in q.lower() for keyword in shoe_keywords)
        
        if is_shoe_query:
            # Skip spell correction for shoe queries to avoid "shoes for men" -> "phones top mens" issue
            corrected_query, has_correction = q, False
        else:
            corrected_query, has_correction = check_spelling(q)
        
        search_query = corrected_query if has_correction else q
        
        # Search products using the corrected query
        all_results = search_products(search_query, category, brand, min_price, max_price, min_rating)
        
        # If no results with corrected query, try original query
        if has_correction and len(all_results) == 0:
            all_results = search_products(q, category, brand, min_price, max_price, min_rating)
            has_correction = False  # Don't show correction if it didn't help
            corrected_query = q
        
        # Apply advanced ranking algorithm using the effective search query
        all_results = advanced_ranking(all_results, search_query, sort_by)
        
        # Pagination
        total_results = len(all_results)
        total_pages = math.ceil(total_results / per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = all_results[start_idx:end_idx]
        
        # Convert to ProductResult objects
        products = []
        for result in page_results:
            products.append(ProductResult(**result))
        
        # Calculate aggregations from all results
        aggregations = calculate_aggregations(all_results)
        
        response_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            products=products,
            total_results=total_results,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            filters_applied={
                "category": category,
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating
            },
            search_metadata=SearchMetadata(
                query=q,
                search_type="simple_fallback",
                response_time_ms=round(response_time, 2),
                has_typo_correction=has_correction,
                corrected_query=corrected_query if has_correction else None
            ),
            aggregations=aggregations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


def _convert_smart_response_to_v2(smart_response, start_time) -> SearchResponse:
    """Convert SmartSearchService response to SearchResponse v2 format"""
    
    # Convert products
    products = []
    for product in smart_response.products:
        products.append(ProductResult(
            id=product.product_id,
            title=product.title,
            description=product.description or "",
            category=product.category,
            subcategory=product.subcategory or "",
            brand=product.brand,
            current_price=product.price,
            original_price=getattr(product, 'original_price', None),
            discount_percent=getattr(product, 'discount_percentage', None),
            rating=product.rating or 0.0,
            num_ratings=product.num_ratings,
            availability="in_stock" if product.stock > 0 else "out_of_stock",
            image_url=product.image_url,
            features=[],
            specifications="{}",
            relevance_score=1.0,
            popularity_score=0.8,
            business_score=0.7,
            final_score=0.9
        ))
    
    response_time = (time.time() - start_time) * 1000
    
    # Determine search type based on metadata
    search_type = "hybrid_enhanced"
    if hasattr(smart_response, 'query_analysis') and smart_response.query_analysis:
        if smart_response.query_analysis.get('search_metadata', {}).get('hybrid_enhancement_used'):
            search_type = "hybrid_enhanced"
        else:
            search_type = "nlp_baseline"
    
    # Create simple aggregations
    aggregations = {
        "categories": [],
        "brands": [],
        "price_ranges": []
    }
    
    return SearchResponse(
        products=products,
        total_results=smart_response.total_count,
        page=smart_response.page,
        per_page=smart_response.limit,
        total_pages=smart_response.total_pages,
        filters_applied=smart_response.filters_applied or {},
        search_metadata=SearchMetadata(
            query=smart_response.query,
            search_type=search_type,
            response_time_ms=round(response_time, 2),
            has_typo_correction=smart_response.has_typo_correction,
            corrected_query=smart_response.corrected_query
        ),
        aggregations=aggregations
    )


# Click tracking endpoint (v1 compatibility)
@v1_router.post("/track-click")
async def track_click(payload: ClickTrackingPayload):
    """
    Track product click events for analytics and ranking improvement
    
    This endpoint handles click tracking data from the frontend.
    """
    try:
        # For now, just log the click event
        # In production, you would store this in a database
        print(f"Click tracked: Query='{payload.query}', Product={payload.product_id}, Position={payload.position}, Time={payload.timestamp}")
        
        # Could add database storage here:
        # await store_click_event(payload)
        
        return {"status": "success", "message": "Click tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Click tracking error: {str(e)}")
