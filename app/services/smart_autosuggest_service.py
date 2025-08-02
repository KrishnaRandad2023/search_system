"""
Smart Autosuggest Service - Connects query analysis with autosuggest

This service:
1. Uses query analyzer to understand search intent
2. Generates intelligent suggestions based on analysis
3. Provides compatibility with existing autosuggest implementation
4. Learns from user interactions to improve over time
"""

import time
from typing import List, Dict, Any, Optional
import logging

from sqlalchemy.orm import Session
from app.schemas.autosuggest import AutosuggestItem
from app.services.query_analyzer_service import QueryAnalyzerService, get_query_analyzer
from app.db.models import AutosuggestQuery, Product

logger = logging.getLogger(__name__)


class SmartAutosuggestService:
    """
    Smart autosuggest service that connects query analysis with autosuggest engine
    Uses NLP-based query understanding for better suggestions
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session"""
        self.db = db
        self.query_analyzer = get_query_analyzer()
        if db:
            self.query_analyzer.db = db
        logger.info("SmartAutosuggestService initialized")
    
    def get_smart_suggestions(self, db: Session, query: str, limit: int = 10, category: Optional[str] = None) -> List[AutosuggestItem]:
        """
        Get smart autosuggest suggestions
        
        Args:
            db: Database session
            query: Search query prefix
            limit: Maximum number of suggestions
            category: Optional category filter
            
        Returns:
            List of AutosuggestItem objects
        """
        # Store db if not already initialized
        if self.db is None:
            self.db = db
            
        start_time = time.time()
        
        # Analyze the query
        analysis = self.query_analyzer.analyze_query(query)
        logger.debug(f"Query analysis: {analysis}")
        
        # Generate suggestions based on analysis
        raw_suggestions = self.query_analyzer.generate_suggestions(query, max_suggestions=limit * 2)
        
        # Convert to AutosuggestItem objects
        suggestions = []
        for suggestion in raw_suggestions:
            item = AutosuggestItem(
                text=suggestion['text'],
                type=suggestion['type'],
                category=suggestion.get('category', 'general'),
                popularity=int(suggestion.get('score', 0.5) * 1000)  # Convert score to popularity
            )
            suggestions.append(item)
        
        # Filter by category if specified
        if category:
            suggestions = [s for s in suggestions if category.lower() in s.category.lower()]
        
        # Add database-sourced suggestions if we need more
        if len(suggestions) < limit and self.db:
            db_suggestions = self._get_db_suggestions(query, category, limit - len(suggestions))
            suggestions.extend(db_suggestions)
        
        # Sort by popularity and deduplicate
        suggestions.sort(key=lambda x: x.popularity, reverse=True)
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            if suggestion.text.lower() not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion.text.lower())
        
        # Limit to requested number
        result = unique_suggestions[:limit]
        
        # Update timing
        processing_time = (time.time() - start_time) * 1000  # ms
        logger.debug(f"Generated {len(result)} suggestions in {processing_time:.2f}ms")
        
        return result
    
    def _get_db_suggestions(self, query: str, category: Optional[str], limit: int) -> List[AutosuggestItem]:
        """Get suggestions from database"""
        try:
            if not self.db:
                return []
                
            query_lower = query.lower().strip()
            
            # Query the autosuggest table with explicit column selection
            query_obj = self.db.query(
                AutosuggestQuery.query,
                AutosuggestQuery.category,
                AutosuggestQuery.popularity
            )
            
            # Apply filters
            query_obj = query_obj.filter(AutosuggestQuery.query.ilike(f"{query_lower}%"))
            
            if category:
                query_obj = query_obj.filter(AutosuggestQuery.category.ilike(f"%{category.lower()}%"))
            
            # Order and limit
            query_results = query_obj.order_by(AutosuggestQuery.popularity.desc()).limit(limit).all()
            
            # Convert to AutosuggestItem objects
            suggestions = []
            for query_text, category_text, popularity_val in query_results:
                item = AutosuggestItem(
                    text=query_text,
                    type="query",
                    category=category_text if category_text else "general",
                    popularity=int(popularity_val or 0)
                )
                suggestions.append(item)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting DB suggestions: {e}")
            return []
    
    def record_interaction(self, query: str, selected_suggestion: Optional[str] = None, user_id: Optional[str] = None):
        """
        Record user interaction with autosuggest
        Used to improve suggestions over time
        """
        if not self.db:
            return
            
        try:
            # Update query database with this interaction
            self.query_analyzer.update_query_database(
                query=query,
                user_id=user_id,
                clicked=selected_suggestion is not None
            )
            
            # If they selected a suggestion, record that too
            if selected_suggestion:
                self.query_analyzer.update_query_database(
                    query=selected_suggestion,
                    user_id=user_id,
                    clicked=True
                )
                
            logger.debug(f"Recorded interaction: {query} -> {selected_suggestion}")
            
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")


# Factory function for dependency injection
def get_smart_autosuggest_service() -> SmartAutosuggestService:
    """Get SmartAutosuggestService instance"""
    return SmartAutosuggestService(None)
