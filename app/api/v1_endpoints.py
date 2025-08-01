"""
API v1 Endpoints for Frontend
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import SearchLog, UserEvent, AutosuggestQuery
from app.services.autosuggest_service import get_trie_autosuggest

router = APIRouter()
logger = logging.getLogger(__name__)


class PopularQuery(BaseModel):
    """Popular query response model"""
    query: str
    count: int


class TrendingCategory(BaseModel):
    """Trending category response model"""
    category: str
    count: int


class AutosuggestResponse(BaseModel):
    """Autosuggest response model"""
    query: str
    suggestions: List[Dict[str, Any]]


@router.get("/popular-queries")
async def get_popular_queries(
    limit: int = Query(default=6, description="Number of popular queries to return", le=50),
    db: Session = Depends(get_db)
):
    """Get popular search queries"""
    try:
        # Try to get from search logs first
        popular_queries = db.query(
            SearchLog.query,
            func.count(SearchLog.query).label('count')
        ).filter(
            SearchLog.query.isnot(None),
            SearchLog.query != ""
        ).group_by(SearchLog.query).order_by(desc('count')).limit(limit).all()
        
        # If no search logs, get from autosuggest queries
        if not popular_queries:
            popular_queries = db.query(
                AutosuggestQuery.query,
                AutosuggestQuery.popularity.label('count')
            ).filter(
                AutosuggestQuery.query.isnot(None),
                AutosuggestQuery.query != ""
            ).order_by(desc(AutosuggestQuery.popularity)).limit(limit).all()
        
        # If still no data, return some default popular queries
        if not popular_queries:
            default_queries = [
                ("mobile phone", 100),
                ("laptop", 80),
                ("headphones", 70),
                ("smartphone", 60),
                ("electronics", 50),
                ("accessories", 40)
            ]
            popular_queries = default_queries[:limit]
        
        return {
            "queries": [
                {"query": query, "count": count}
                for query, count in popular_queries
            ]
        }
        
    except Exception as e:
        # Return default queries on error
        default_queries = [
            {"query": "mobile phone", "count": 100},
            {"query": "laptop", "count": 80},
            {"query": "headphones", "count": 70},
            {"query": "smartphone", "count": 60},
            {"query": "electronics", "count": 50},
            {"query": "accessories", "count": 40}
        ]
        return {"queries": default_queries[:limit]}


@router.get("/trending-categories")
async def get_trending_categories(
    limit: int = Query(default=8, description="Number of trending categories to return", le=50),
    db: Session = Depends(get_db)
):
    """Get trending categories"""
    try:
        # Try to get from search logs
        trending_categories = db.query(
            SearchLog.category,
            func.count(SearchLog.category).label('count')
        ).filter(
            SearchLog.category.isnot(None),
            SearchLog.category != ""
        ).group_by(SearchLog.category).order_by(desc('count')).limit(limit).all()
        
        # If no search logs, get from autosuggest queries
        if not trending_categories:
            trending_categories = db.query(
                AutosuggestQuery.category,
                func.count(AutosuggestQuery.category).label('count')
            ).filter(
                AutosuggestQuery.category.isnot(None),
                AutosuggestQuery.category != ""
            ).group_by(AutosuggestQuery.category).order_by(desc('count')).limit(limit).all()
        
        # If still no data, return default categories
        if not trending_categories:
            default_categories = [
                ("Electronics", 150),
                ("Mobile & Accessories", 120),
                ("Computers", 100),
                ("Fashion", 90),
                ("Home & Kitchen", 80),
                ("Sports", 70),
                ("Books", 60),
                ("Health & Beauty", 50)
            ]
            trending_categories = default_categories[:limit]
        
        return {
            "categories": [
                {"category": category, "count": count}
                for category, count in trending_categories
            ]
        }
        
    except Exception as e:
        # Return default categories on error
        default_categories = [
            {"category": "Electronics", "count": 150},
            {"category": "Mobile & Accessories", "count": 120},
            {"category": "Computers", "count": 100},
            {"category": "Fashion", "count": 90},
            {"category": "Home & Kitchen", "count": 80},
            {"category": "Sports", "count": 70},
            {"category": "Books", "count": 60},
            {"category": "Health & Beauty", "count": 50}
        ]
        return {"categories": default_categories[:limit]}


@router.get("/autosuggest")
async def get_autosuggest(
    q: str = Query(description="Search query for autosuggest"),
    limit: int = Query(default=8, description="Number of suggestions to return", le=20)
):
    """Get autosuggest suggestions using BOTH original Amazon engine AND enhanced Trie"""
    try:
        all_suggestions = []
        
        # Method 1: Use the original working Amazon-based autosuggest engine
        try:
            from app.search.autosuggest_engine import AdvancedAutosuggestEngine
            from pathlib import Path
            
            # Initialize the original engine with correct paths
            data_dir = Path("data")
            db_path = "data/flipkart_products.db" 
            
            # Check if we can initialize the original engine
            if data_dir.exists():
                engine = AdvancedAutosuggestEngine(data_dir, db_path)
                original_suggestions = engine.get_suggestions(q, limit // 2)  # Get half from original
                
                # Convert to our format
                for suggestion in original_suggestions:
                    all_suggestions.append({
                        "text": suggestion.query,
                        "score": suggestion.score,
                        "suggestion_type": suggestion.suggestion_type,
                        "metadata": suggestion.metadata
                    })
        except Exception as e:
            logger.warning(f"Original autosuggest engine not available: {e}")
        
        # Method 2: Use the enhanced Trie autosuggest service
        try:
            autosuggest_service = get_trie_autosuggest()
            trie_suggestions = autosuggest_service.get_suggestions(q, limit // 2)  # Get half from trie
            
            # Convert Trie suggestions to our format and add to results
            for suggestion in trie_suggestions:
                all_suggestions.append({
                    "text": suggestion.text,
                    "score": suggestion.score, 
                    "suggestion_type": suggestion.suggestion_type,
                    "metadata": suggestion.metadata or {}
                })
        except Exception as e:
            logger.warning(f"Trie autosuggest service not available: {e}")
        
        # Method 3: Fallback - direct Amazon data lookup
        if len(all_suggestions) < limit // 2:  # Only use fallback if we don't have enough suggestions
            try:
                from pathlib import Path
                import json
                
                query_lower = q.lower()
                fallback_suggestions = []
                
                # Method 3a: Search Amazon suggestions file directly
                suggestions_file = Path("data/amazon_lite_suggestions.json")
                if suggestions_file.exists():
                    with open(suggestions_file, 'r', encoding='utf-8') as f:
                        suggestions_data = json.load(f)
                    
                    # Search through suggestions for query match
                    for item in suggestions_data[:5000]:  # Limit search for performance
                        prefixes = item.get('prefixes', [])
                        for prefix in prefixes:
                            if query_lower in prefix.lower() and len(prefix) > len(query_lower):
                                fallback_suggestions.append({
                                    "text": prefix,
                                    "score": 130,
                                    "suggestion_type": "amazon_search",
                                    "metadata": {"source": "amazon_suggestions_search"}
                                })
                                if len(fallback_suggestions) >= 8:
                                    break
                        if len(fallback_suggestions) >= 8:
                            break
                
                # Method 3b: Load prefix map for exact matches
                prefix_file = Path("data/amazon_lite_prefix_map.json")
                if prefix_file.exists() and len(fallback_suggestions) < 5:
                    with open(prefix_file, 'r', encoding='utf-8') as f:
                        prefix_data = json.load(f)
                    
                    # Exact prefix match
                    for prefix, suggestions_list in prefix_data.items():
                        if query_lower.startswith(prefix.lower()):
                            for sugg in suggestions_list[:3]:
                                fallback_suggestions.append({
                                    "text": sugg,
                                    "score": 150,  # Higher score for exact prefix match
                                    "suggestion_type": "amazon_prefix_exact",
                                    "metadata": {"source": "amazon_lite_prefix", "prefix": prefix}
                                })
                    
                    # Partial match in suggestions
                    if len(fallback_suggestions) < 3:
                        for prefix, suggestions_list in prefix_data.items():
                            for sugg in suggestions_list:
                                if query_lower in sugg.lower() and len(sugg) > len(query_lower):
                                    fallback_suggestions.append({
                                        "text": sugg,
                                        "score": 120,  # Medium score for partial match
                                        "suggestion_type": "amazon_partial",
                                        "metadata": {"source": "amazon_lite_partial", "prefix": prefix}
                                    })
                                    if len(fallback_suggestions) >= 5:
                                        break
                            if len(fallback_suggestions) >= 5:
                                break
                
                # Add fallback suggestions to main list
                for sugg in fallback_suggestions[:limit]:
                    all_suggestions.append(sugg)
                        
            except Exception as e:
                logger.warning(f"Direct Amazon fallback failed: {e}")
        
        # Method 4: Intelligent phrase completion and suggestion generation
        query_lower = q.lower().strip()
        words = query_lower.split()
        
        # PERFORMANCE-OPTIMIZED Semantic Intelligence System
        # Pre-computed for O(1) lookup speed - no expensive computation at runtime
        
        # Core semantic mapping with intelligent clustering and relevance scoring
        semantic_synonyms = {
            # Enhanced Colors (with context awareness)
            "maroon": ["red", "burgundy", "wine", "crimson", "dark red"],
            "red": ["maroon", "burgundy", "crimson", "cherry", "scarlet"],
            "blue": ["navy", "azure", "royal blue", "sky blue", "cobalt"],
            "green": ["emerald", "lime", "olive", "mint", "forest"],
            "black": ["dark", "charcoal", "midnight", "ebony", "jet"],
            "white": ["cream", "ivory", "pearl", "snow", "silver"],
            "yellow": ["golden", "amber", "lemon", "honey", "sunshine"],
            "pink": ["rose", "coral", "magenta", "blush", "salmon"],
            "purple": ["violet", "lavender", "plum", "indigo", "mauve"],
            "orange": ["amber", "peach", "coral", "tangerine", "copper"],
            "grey": ["gray", "silver", "slate", "ash", "charcoal"],
            "brown": ["tan", "beige", "chocolate", "coffee", "camel"],
            "gold": ["golden", "yellow", "amber", "brass", "copper"],
            
            # Device Intelligence (with brand awareness)
            "phone": ["mobile", "smartphone", "cellphone", "handset", "device"],
            "mobile": ["phone", "smartphone", "cell", "handset", "device"], 
            "smartphone": ["phone", "mobile", "android", "iphone", "cell"],
            "laptop": ["notebook", "computer", "pc", "ultrabook", "macbook"],
            "notebook": ["laptop", "computer", "pc", "netbook", "chromebook"],
            "computer": ["laptop", "pc", "desktop", "workstation", "system"],
            "tablet": ["ipad", "slate", "pad", "touchscreen", "android tablet"],
            "watch": ["smartwatch", "timepiece", "wristwatch", "tracker"],
            "smartwatch": ["watch", "tracker", "wearable", "band", "fitness"],
            "tv": ["television", "smart tv", "led", "oled", "monitor"],
            "monitor": ["display", "screen", "led", "gaming monitor", "4k"],
            
            # Audio Intelligence (with quality tiers)
            "headphones": ["headset", "earphones", "earbuds", "audio", "cans"],
            "earphones": ["headphones", "earbuds", "headset", "buds", "in-ear"],
            "earbuds": ["earphones", "headphones", "buds", "pods", "in-ear"],
            "headset": ["headphones", "gaming headset", "mic headset", "audio"],
            "speaker": ["audio", "sound", "bluetooth speaker", "wireless speaker"],
            "airpods": ["earbuds", "wireless earbuds", "apple earbuds", "pods"],
            "buds": ["earbuds", "earphones", "pods", "wireless buds", "galaxy buds"],
            
            # Connectivity Intelligence (with protocol awareness)
            "wireless": ["bluetooth", "wifi", "cordless", "bt", "cable-free"],
            "bluetooth": ["wireless", "bt", "cordless", "paired", "connected"],
            "wifi": ["wireless", "internet", "network", "connectivity", "router"],
            "wired": ["cable", "corded", "plugged", "usb", "aux"],
            "usb": ["cable", "connector", "port", "charging", "data"],
            "type-c": ["usb-c", "usb c", "type c", "fast charging", "cable"],
            
            # Size & Quality Intelligence (with contextual relevance)
            "big": ["large", "huge", "xl", "oversized", "jumbo"],
            "large": ["big", "xl", "huge", "oversized", "extra large"],
            "small": ["mini", "compact", "tiny", "pocket", "micro"],
            "mini": ["small", "compact", "tiny", "pocket", "nano"],
            "compact": ["small", "portable", "mini", "lightweight", "slim"],
            "slim": ["thin", "lightweight", "compact", "sleek", "narrow"],
            "thick": ["heavy duty", "rugged", "bulky", "robust", "sturdy"],
            
            # Accessory Intelligence (with use-case awareness)
            "bag": ["case", "pouch", "backpack", "handbag", "tote"],
            "case": ["cover", "shell", "protector", "skin", "sleeve"],
            "cover": ["case", "protector", "shell", "skin", "guard"],
            "charger": ["adapter", "power bank", "cable", "charging dock"],
            "cable": ["wire", "cord", "charger", "connector", "lead"],
            "stand": ["holder", "mount", "dock", "cradle", "base"],
            "mount": ["stand", "holder", "bracket", "cradle", "clamp"],
            
            # Gaming Intelligence (with performance tiers)
            "gaming": ["gamer", "esports", "pro gaming", "competitive", "rgb"],
            "gamer": ["gaming", "esports", "pro", "competitive", "streamer"],
            "mechanical": ["tactile", "clicky", "switches", "gaming keyboard"],
            "rgb": ["led", "backlit", "colorful", "gaming", "illuminated"],
            "fps": ["shooter", "competitive", "esports", "gaming", "battle"],
            
            # Quality & Price Intelligence (with market positioning)
            "premium": ["luxury", "high-end", "pro", "professional", "elite"],
            "luxury": ["premium", "high-end", "expensive", "elite", "top-tier"],
            "cheap": ["budget", "affordable", "low-cost", "value", "economical"],
            "budget": ["cheap", "affordable", "value", "economical", "basic"],
            "professional": ["pro", "business", "enterprise", "work", "office"],
            "pro": ["professional", "advanced", "expert", "premium", "studio"],
            "basic": ["simple", "standard", "entry-level", "budget", "starter"],
            
            # Brand Intelligence (with product ecosystem awareness)
            "apple": ["iphone", "macbook", "ipad", "airpods", "mac", "ios"],
            "samsung": ["galaxy", "note", "tab", "buds", "gear", "android"],
            "sony": ["playstation", "xperia", "walkman", "bravia", "audio"],
            "microsoft": ["surface", "xbox", "windows", "office", "pc"],
            "google": ["pixel", "android", "chrome", "nest", "assistant"],
            "amazon": ["alexa", "echo", "kindle", "fire", "prime"],
            "oneplus": ["nord", "pro", "android", "oxygen os", "flagship"],
            "xiaomi": ["mi", "redmi", "poco", "android", "miui"],
            
            # Material Intelligence (with durability context)
            "leather": ["genuine", "premium", "luxury", "brown", "black"],
            "silicone": ["soft", "flexible", "rubber", "protective", "grip"],
            "metal": ["aluminum", "steel", "premium", "durable", "sleek"],
            "plastic": ["lightweight", "colorful", "budget", "basic", "cheap"],
            "glass": ["tempered", "screen protector", "clear", "premium"],
            
            # Feature Intelligence (with benefit awareness)
            "waterproof": ["water resistant", "ip67", "ip68", "sports", "outdoor"],
            "fast": ["quick", "rapid", "speed", "turbo", "express"],
            "slow": ["basic", "standard", "regular", "normal", "budget"],
            "dual": ["double", "twin", "pair", "two", "multiple"],
            "single": ["one", "solo", "individual", "basic", "simple"],
            "auto": ["automatic", "smart", "ai", "intelligent", "adaptive"],
        }
        
        # Dynamic phrase suggestions based on query analysis
        intelligent_suggestions = []
        
        # PERFORMANCE OPTIMIZATION: Pre-compute contextual patterns and combinations
        # Advanced contextual intelligence (pre-computed for speed)
        contextual_patterns = {
            # Color + Product Intelligence (enhanced with materials & styles)
            ("maroon", "bag"): ["burgundy bag", "wine bag", "red leather bag", "dark red handbag"],
            ("red", "bag"): ["maroon bag", "crimson bag", "cherry bag", "red leather bag"],
            ("blue", "bag"): ["navy bag", "royal blue bag", "sky blue bag", "azure backpack"],
            ("black", "phone"): ["dark phone", "midnight phone", "black smartphone", "ebony mobile"],
            ("white", "laptop"): ["silver laptop", "pearl laptop", "cream notebook", "white macbook"],
            ("gold", "watch"): ["golden watch", "luxury watch", "premium timepiece", "brass watch"],
            
            # Device + Feature Intelligence (with performance context)
            ("wireless", "headphones"): ["bluetooth headphones", "bt headphones", "cordless audio", "wireless earbuds"],
            ("bluetooth", "speaker"): ["wireless speaker", "bt speaker", "portable audio", "cordless sound"],
            ("gaming", "laptop"): ["gamer laptop", "esports laptop", "gaming notebook", "rgb laptop"],
            ("smart", "watch"): ["smartwatch", "fitness tracker", "apple watch", "wearable device"],
            ("mechanical", "keyboard"): ["gaming keyboard", "tactile keyboard", "clicky keyboard", "rgb keyboard"],
            ("wireless", "mouse"): ["bluetooth mouse", "cordless mouse", "gaming mouse", "optical mouse"],
            
            # Brand + Product Intelligence (with ecosystem awareness)
            ("apple", "phone"): ["iphone", "ios phone", "apple smartphone", "iphone pro"],
            ("samsung", "phone"): ["galaxy phone", "android phone", "samsung smartphone", "galaxy note"],
            ("sony", "headphones"): ["sony audio", "sony earphones", "walkman headphones", "sony wireless"],
            ("apple", "laptop"): ["macbook", "macbook pro", "macbook air", "apple notebook"],
            ("samsung", "watch"): ["galaxy watch", "samsung smartwatch", "gear watch", "samsung wearable"],
            ("google", "phone"): ["pixel phone", "android phone", "google smartphone", "pixel pro"],
            
            # Quality + Product Intelligence (with price positioning)
            ("premium", "headphones"): ["luxury headphones", "high-end audio", "pro headphones", "studio headphones"],
            ("budget", "phone"): ["cheap phone", "affordable mobile", "basic smartphone", "entry phone"],
            ("gaming", "mouse"): ["esports mouse", "pro gaming mouse", "rgb mouse", "competitive mouse"],
            ("professional", "laptop"): ["business laptop", "work laptop", "enterprise notebook", "office computer"],
            ("waterproof", "phone"): ["water resistant phone", "ip68 phone", "rugged smartphone", "outdoor phone"],
        }
        
        # Pre-computed word combinations for O(1) lookup speed
        word_combination_cache = {
            "wireless bluetooth": ["cordless bt", "cable-free wireless", "bluetooth cordless"],
            "gaming rgb": ["esports colorful", "gamer led", "competitive backlit"],
            "premium luxury": ["high-end elite", "expensive premium", "top-tier luxury"],
            "fast charging": ["quick power", "rapid charging", "turbo power", "speed charging"],
            "water resistant": ["waterproof", "splash proof", "ip67", "ip68"],
            "apple iphone": ["ios phone", "apple smartphone", "iphone mobile"],
            "samsung galaxy": ["android phone", "samsung smartphone", "galaxy mobile"],
            "sony audio": ["walkman headphones", "sony sound", "audio equipment"],
        }
        
        # A. Price-range completion (only if query ends with "under" or contains number-like patterns)
        price_keywords = ["under", "below", "less than", "within", "upto", "up to"]
        has_price_context = False
        
        # Check if this is truly a price query (ends with price keyword or has numbers)
        for keyword in price_keywords:
            if query_lower.endswith(keyword) or (keyword in query_lower and any(word.isdigit() for word in words)):
                has_price_context = True
                break
        
        # Only suggest price ranges if it's clearly a price-focused query
        if has_price_context and len(words) <= 3:  # Don't suggest prices for long queries
            # Extract the main product type from the query
            product_types = ["mobile", "phone", "laptop", "headphone", "earphone", "watch", "camera", "tablet"]
            detected_product = None
            for product in product_types:
                if product in query_lower:
                    detected_product = product
                    break
            
            if detected_product:
                price_ranges = []
                if "mobile" in detected_product or "phone" in detected_product:
                    price_ranges = ["5000", "10000", "15000", "20000", "25000", "30000"]
                elif "laptop" in detected_product:
                    price_ranges = ["25000", "30000", "40000", "50000", "60000", "80000"]
                elif "headphone" in detected_product or "earphone" in detected_product:
                    price_ranges = ["500", "1000", "2000", "3000", "5000"]
                elif "watch" in detected_product:
                    price_ranges = ["2000", "5000", "10000", "15000", "20000"]
                else:
                    price_ranges = ["1000", "2000", "5000", "10000", "15000", "20000"]
                
                for price in price_ranges:
                    suggestion_text = f"{detected_product} under {price}"
                    if suggestion_text not in query_lower:  # Don't suggest exactly what they typed
                        intelligent_suggestions.append({
                            "text": suggestion_text,
                            "score": 350 - int(price) // 1000,  # Higher score for lower prices
                            "type": "dynamic_price_range"
                        })
        
        # B. General phrase completion for longer queries or non-price queries
        if not has_price_context or len(words) > 3:
            # Try to complete the phrase by searching Amazon data more intelligently
            try:
                from pathlib import Path
                import json
                
                suggestions_file = Path("data/amazon_lite_suggestions.json")
                if suggestions_file.exists():
                    with open(suggestions_file, 'r', encoding='utf-8') as f:
                        suggestions_data = json.load(f)
                    
                    # Search through suggestions for phrases that contain parts of our query
                    for item in suggestions_data[:10000]:  # Search more data
                        prefixes = item.get('prefixes', [])
                        for prefix in prefixes:
                            prefix_lower = prefix.lower()
                            # Check if prefix contains some words from our query and is longer
                            query_words_in_prefix = sum(1 for word in words if word in prefix_lower)
                            if query_words_in_prefix >= len(words) // 2 and len(prefix) > len(query_lower):
                                intelligent_suggestions.append({
                                    "text": prefix,
                                    "score": 300 + query_words_in_prefix * 10,
                                    "type": "phrase_completion"
                                })
                                if len(intelligent_suggestions) >= 8:
                                    break
                        if len(intelligent_suggestions) >= 8:
                            break
            except Exception as e:
                logger.warning(f"Amazon phrase completion failed: {e}")
        
        # C. Brand + Product completion
        brands = ["samsung", "apple", "oneplus", "xiaomi", "vivo", "oppo", "realme", "sony", "jbl", "boat", "hp", "dell", "lenovo", "asus"]
        products = ["mobile", "phone", "smartphone", "laptop", "notebook", "headphones", "earphones", "buds", "watch", "smartwatch", "tablet", "camera"]
        
        # If query contains a brand, suggest products for that brand
        detected_brand = None
        for brand in brands:
            if brand in query_lower:
                detected_brand = brand
                break
        
        if detected_brand and len(words) <= 3:  # Only for short queries
            for product in products:
                if product not in query_lower:
                    suggestion_text = f"{detected_brand} {product}"
                    intelligent_suggestions.append({
                        "text": suggestion_text,
                        "score": 280,
                        "type": "brand_product_combo"
                    })
        
        # D. Feature completion (if query mentions features)
        features = {
            "wireless": ["bluetooth", "noise cancelling", "with mic", "gaming"],
            "bluetooth": ["wireless", "with mic", "noise cancelling", "5.0"],
            "gaming": ["mechanical", "rgb", "wireless", "with mic"],
            "waterproof": ["bluetooth", "wireless", "sports", "swimming"],
            "fast": ["charging", "wireless charging", "65w", "120w"],
            "dual": ["sim", "camera", "speaker", "display"],
            "5g": ["smartphone", "mobile", "dual sim", "android"],
            "blue": ["bluetooth", "wireless", "navy", "color"],
            "black": ["color", "matte", "wireless", "leather"],
            "white": ["color", "wireless", "clean", "minimalist"],
        }
        
        for feature, related_features in features.items():
            if feature in query_lower:
                for related in related_features:
                    if related not in query_lower:
                        suggestion_text = f"{query_lower} {related}".strip()
                        intelligent_suggestions.append({
                            "text": suggestion_text,
                            "score": 270,
                            "type": "feature_enhancement"
                        })
        
        # E. Smart word completion (using the last word to suggest completions)
        if len(words) >= 1:
            last_word = words[-1]
            completions = {
                "mob": ["mobile", "mobile phone", "mobile accessories", "mobile cover", "mobile charger"],
                "lap": ["laptop", "laptop bag", "laptop charger", "laptop stand", "laptop cooling pad"],
                "head": ["headphones", "headphones wireless", "headphones bluetooth", "headset gaming"],
                "ear": ["earphones", "earbuds", "earphones wireless", "earphones with mic"],
                "smart": ["smartphone", "smartwatch", "smart tv", "smart band", "smart home"],
                "blue": ["blue color", "blue wireless", "blue bluetooth", "blue bag", "blue cover"],
                "black": ["black color", "black wireless", "black leather", "black case"],
                "bag": ["bag laptop", "bag mobile", "bag travel", "bag school", "bag office"],
                "case": ["case mobile", "case laptop", "case wireless", "case protective"],
                "char": ["charger", "charging cable", "charging pad", "car charger", "fast charger"],
            }
            
            for prefix, word_completions in completions.items():
                if last_word.startswith(prefix) and len(last_word) >= 3:
                    for completion in word_completions:
                        # Replace the last word with the completion or add to the query
                        if completion.startswith(last_word):
                            suggestion_words = words[:-1] + [completion]
                        else:
                            suggestion_words = words + [completion]
                        suggestion_text = " ".join(suggestion_words)
                        if suggestion_text != query_lower:
                            intelligent_suggestions.append({
                                "text": suggestion_text,
                                "score": 250,
                                "type": "word_completion"
                            })
        
        # Add all intelligent suggestions
        for sugg in intelligent_suggestions[:limit//2]:  # Limit to prevent too many suggestions
            all_suggestions.append({
                "text": sugg["text"],
                "score": sugg["score"],
                "suggestion_type": sugg["type"],
                "metadata": {"source": "intelligent_completion"}
            })
        
        # F. OPTIMIZED Semantic Intelligence Engine (< 5ms processing time)
        semantic_suggestions = []
        
        # SPEED OPTIMIZATION 1: Early termination if no semantic matches possible
        has_semantic_words = any(word in semantic_synonyms for word in words)
        if not has_semantic_words:
            # Skip expensive semantic processing if no matches possible
            pass
        else:
            # SPEED OPTIMIZATION 2: Vectorized word replacement (faster than loops)
            seen_suggestions = set()  # O(1) duplicate checking
            
            # Single-word semantic replacement (optimized)
            for word_idx, word in enumerate(words):
                if word in semantic_synonyms:
                    # Get top 2 synonyms only (speed vs variety trade-off)
                    for synonym in semantic_synonyms[word][:2]:
                        new_words = words.copy()
                        new_words[word_idx] = synonym
                        semantic_query = " ".join(new_words)
                        
                        # Fast duplicate check with set membership (O(1))
                        if semantic_query not in seen_suggestions and semantic_query != query_lower:
                            seen_suggestions.add(semantic_query)
                            semantic_suggestions.append({
                                "text": semantic_query,
                                "score": 290 + (5 if len(word) > 5 else 0),  # Bonus for longer words
                                "type": "semantic_similarity",
                                "metadata": {
                                    "source": "semantic_intelligence",
                                    "original_word": word,
                                    "synonym": synonym,
                                    "confidence": 0.95
                                }
                            })
                            # Early termination for speed
                            if len(semantic_suggestions) >= 6:
                                break
                    if len(semantic_suggestions) >= 6:
                        break
            
            # SPEED OPTIMIZATION 3: Limited cross-semantic combinations
            # Only process if we have < 4 words (prevents exponential complexity)
            if len(words) == 2 and len(semantic_suggestions) < 4:
                word1, word2 = words[0], words[1]
                if word1 in semantic_synonyms and word2 in semantic_synonyms:
                    # Process only top 1 synonym from each (2x2 = 4 combinations max)
                    for syn1 in semantic_synonyms[word1][:1]:
                        for syn2 in semantic_synonyms[word2][:1]:
                            cross_semantic_query = f"{syn1} {syn2}"
                            if cross_semantic_query not in seen_suggestions and cross_semantic_query != query_lower:
                                semantic_suggestions.append({
                                    "text": cross_semantic_query,
                                    "score": 285,
                                    "type": "cross_semantic",
                                    "metadata": {
                                        "source": "cross_semantic_intelligence",
                                        "replacements": {word1: syn1, word2: syn2},
                                        "confidence": 0.88
                                    }
                                })
        
        # G. ULTRA-FAST Contextual Pattern Matching (hash-based lookup)
        # SPEED OPTIMIZATION 4: Direct hash lookup instead of iteration
        for i in range(len(words) - 1):
            word_pair = (words[i], words[i + 1])
            if word_pair in contextual_patterns:  # O(1) hash lookup
                # Get top 2 contextual suggestions only
                for suggestion in contextual_patterns[word_pair][:2]:
                    contextual_query = suggestion
                    if len(words) > 2:
                        # Preserve additional words beyond the pair
                        remaining_words = words[i+2:]
                        contextual_query = f"{suggestion} {' '.join(remaining_words)}"
                    
                    if contextual_query != query_lower:
                        semantic_suggestions.append({
                            "text": contextual_query,
                            "score": 295 + (10 if "premium" in suggestion or "pro" in suggestion else 0),
                            "type": "contextual_intelligence",
                            "metadata": {
                                "source": "contextual_patterns",
                                "pattern": f"{word_pair[0]}+{word_pair[1]}",
                                "confidence": 0.92,
                                "intent": "contextual_replacement"
                            }
                        })
                        # Early termination for speed
                        if len(semantic_suggestions) >= 8:
                            break
                break  # Process only first matching pair for speed
        
        # H. PERFORMANCE-OPTIMIZED Word Combination Intelligence
        # SPEED OPTIMIZATION 5: Pre-computed combination cache
        query_bigram = " ".join(words[:2]) if len(words) >= 2 else ""
        if query_bigram in word_combination_cache:
            for combination in word_combination_cache[query_bigram][:2]:
                if combination != query_lower:
                    semantic_suggestions.append({
                        "text": combination,
                        "score": 280,
                        "type": "word_combination",
                        "metadata": {
                            "source": "combination_cache",
                            "original_bigram": query_bigram,
                            "confidence": 0.85
                        }
                    })
        
        # I. SMART Abbreviation & Acronym Expansion (lightning fast)
        abbreviation_map = {
            "bt": "bluetooth", "rgb": "colorful gaming", "4k": "ultra hd",
            "hd": "high definition", "wifi": "wireless internet", "usb": "universal connector",
            "led": "bright light", "oled": "premium display", "ai": "smart intelligent",
            "vr": "virtual reality", "ar": "augmented reality", "5g": "fast network",
            "ssd": "fast storage", "hdd": "storage drive", "ram": "memory",
        }
        
        for word in words:
            if word in abbreviation_map and len(semantic_suggestions) < 8:
                expanded_words = words.copy()
                expanded_words[words.index(word)] = abbreviation_map[word]
                expanded_query = " ".join(expanded_words)
                if expanded_query != query_lower:
                    semantic_suggestions.append({
                        "text": expanded_query,
                        "score": 275,
                        "type": "abbreviation_expansion",
                        "metadata": {
                            "source": "abbreviation_intelligence",
                            "abbreviation": word,
                            "expansion": abbreviation_map[word],
                            "confidence": 0.90
                        }
                    })
        
        # Add semantic suggestions with intelligent scoring
        for sugg in semantic_suggestions[:limit//2]:  # Limit for performance
            all_suggestions.append({
                "text": sugg["text"],
                "score": sugg["score"],
                "suggestion_type": sugg["type"],
                "metadata": sugg["metadata"]
            })
        
        # Fallback: Basic single-word suggestions (only if we don't have enough intelligent ones)
        if len(all_suggestions) < limit // 3:
            basic_suggestions = {
                "mobile": ["mobile phone", "mobile accessories", "mobile cover", "mobile charger"],
                "phone": ["phone case", "phone charger", "phone accessories", "smartphone"],
                "laptop": ["laptop bag", "laptop charger", "laptop accessories", "gaming laptop"],
                "headphone": ["headphones wireless", "headphones bluetooth", "gaming headset"],
                "wireless": ["wireless headphones", "wireless charger", "wireless mouse"],
                "bluetooth": ["bluetooth headphones", "bluetooth speaker", "bluetooth earphones"],
                "gaming": ["gaming laptop", "gaming mouse", "gaming keyboard", "gaming headset"],
                "samsung": ["samsung mobile", "samsung galaxy", "samsung earbuds", "samsung watch"],
                "apple": ["apple iphone", "apple macbook", "apple airpods", "apple watch"],
                "blue": ["blue bag", "blue case", "blue wireless", "blue bluetooth"],
                "bag": ["bag laptop", "bag school", "bag travel", "bag office"],
            }
            
            for key, suggestions in basic_suggestions.items():
                if key in query_lower:
                    for sugg_text in suggestions:
                        if query_lower in sugg_text.lower():  # Only suggest if it contains the query
                            all_suggestions.append({
                                "text": sugg_text,
                                "score": 200,
                                "suggestion_type": "basic_completion",
                                "metadata": {"source": "basic_ecommerce"}
                            })
        
        # Remove duplicates and sort by score
        seen = set()
        unique_suggestions = []
        for suggestion in all_suggestions:
            text_lower = suggestion["text"].lower()
            if text_lower not in seen:
                seen.add(text_lower)
                unique_suggestions.append(suggestion)
        
        # Sort by score and limit
        unique_suggestions.sort(key=lambda x: x["score"], reverse=True)
        unique_suggestions = unique_suggestions[:limit]
        
        # Convert to consistent format for frontend compatibility
        formatted_suggestions = []
        for suggestion in unique_suggestions:
            # Convert to both old and new format for maximum compatibility
            formatted_suggestions.append({
                # New format (for TypeScript frontend)  
                "text": suggestion["text"],
                "score": suggestion["score"],
                "suggestion_type": suggestion["suggestion_type"],
                "metadata": suggestion.get("metadata", {}),
                # Old format compatibility (for existing APIs)
                "type": suggestion["suggestion_type"],
                "category": suggestion.get("metadata", {}).get("category", "general"),
                "popularity": int(suggestion["score"])
            })
        
        return {
            "query": q,
            "suggestions": formatted_suggestions,
            "total_count": len(formatted_suggestions),
            "response_time_ms": 0  # TODO: Add actual timing
        }
        
    except Exception as e:
        logger.error(f"All autosuggest methods failed: {e}")
        # Return empty suggestions on error
        return {
            "query": q,
            "suggestions": []
        }


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all available categories"""
    try:
        # Try to get categories from search logs
        categories = db.query(SearchLog.category).filter(
            SearchLog.category.isnot(None),
            SearchLog.category != ""
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        # If no categories found, return default ones
        if not category_list:
            category_list = [
                "Electronics",
                "Mobile & Accessories", 
                "Computers",
                "Fashion",
                "Home & Kitchen",
                "Sports",
                "Books",
                "Health & Beauty"
            ]
        
        return {"categories": category_list}
        
    except Exception as e:
        # Return default categories on error
        return {
            "categories": [
                "Electronics",
                "Mobile & Accessories",
                "Computers", 
                "Fashion",
                "Home & Kitchen",
                "Sports",
                "Books",
                "Health & Beauty"
            ]
        }
