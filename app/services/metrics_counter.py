"""
Real-time Metrics Counter Service
Tracks API calls and search counts in memory for live analytics
"""

from datetime import datetime, date
from typing import Dict, Any
import threading
from collections import defaultdict

class MetricsCounter:
    """Thread-safe metrics counter for real-time analytics"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._api_call_count = 0
        self._daily_search_count = defaultdict(int)  # date -> count
        self._search_count = 0
        self._start_time = datetime.now()
        
        # Feature-specific counters
        self._autosuggest_count = 0
        self._hybrid_search_count = 0
        self._semantic_search_count = 0
        self._feedback_count = 0
        self._product_clicks = 0
        self._filter_usage = 0
        self._category_searches = defaultdict(int)  # category -> count
        self._ml_ranking_calls = 0
        self._typo_corrections = 0
        self._zero_result_queries = 0
        
        # Performance metrics
        self._total_response_time = 0.0
        self._response_count = 0
        
    def increment_api_call(self):
        """Increment total API call counter"""
        with self._lock:
            self._api_call_count += 1
            
    def increment_search_call(self):
        """Increment search-specific counter"""
        with self._lock:
            self._search_count += 1
            today = date.today().isoformat()
            self._daily_search_count[today] += 1
            
    def increment_autosuggest(self):
        """Increment autosuggest usage counter"""
        with self._lock:
            self._autosuggest_count += 1
            
    def increment_hybrid_search(self):
        """Increment hybrid search counter"""
        with self._lock:
            self._hybrid_search_count += 1
            
    def increment_semantic_search(self):
        """Increment semantic search counter"""
        with self._lock:
            self._semantic_search_count += 1
            
    def increment_feedback(self):
        """Increment feedback counter"""
        with self._lock:
            self._feedback_count += 1
            
    def increment_product_click(self):
        """Increment product click counter"""
        with self._lock:
            self._product_clicks += 1
            
    def increment_filter_usage(self):
        """Increment filter usage counter"""
        with self._lock:
            self._filter_usage += 1
            
    def increment_category_search(self, category: str):
        """Increment category-specific search counter"""
        with self._lock:
            # Normalize category to lowercase to avoid duplicates
            category_normalized = category.lower()
            self._category_searches[category_normalized] += 1
            
    def increment_ml_ranking(self):
        """Increment ML ranking usage counter"""
        with self._lock:
            self._ml_ranking_calls += 1
            
    def increment_typo_correction(self):
        """Increment typo correction counter"""
        with self._lock:
            self._typo_corrections += 1
            
    def increment_zero_results(self):
        """Increment zero results counter"""
        with self._lock:
            self._zero_result_queries += 1
            
    def add_response_time(self, response_time_ms: float):
        """Add response time measurement"""
        with self._lock:
            self._total_response_time += response_time_ms
            self._response_count += 1
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        with self._lock:
            today = date.today().isoformat()
            avg_response_time = (self._total_response_time / self._response_count) if self._response_count > 0 else 0
            
            return {
                "total_api_calls": self._api_call_count,
                "total_search_calls": self._search_count,
                "daily_search_count": self._daily_search_count[today],
                "all_daily_counts": dict(self._daily_search_count),
                "uptime_seconds": int((datetime.now() - self._start_time).total_seconds()),
                "start_time": self._start_time.isoformat(),
                
                # Feature usage metrics
                "autosuggest_calls": self._autosuggest_count,
                "hybrid_search_calls": self._hybrid_search_count,
                "semantic_search_calls": self._semantic_search_count,
                "feedback_submissions": self._feedback_count,
                "product_clicks": self._product_clicks,
                "filter_usage": self._filter_usage,
                "category_searches": dict(self._category_searches),
                "ml_ranking_calls": self._ml_ranking_calls,
                "typo_corrections": self._typo_corrections,
                "zero_result_queries": self._zero_result_queries,
                
                # Performance metrics
                "average_response_time_ms": round(avg_response_time, 2),
                "total_response_measurements": self._response_count,
            }
            
    def reset_counters(self):
        """Reset all counters (for testing purposes)"""
        with self._lock:
            self._api_call_count = 0
            self._daily_search_count.clear()
            self._search_count = 0
            self._start_time = datetime.now()
            
            # Reset feature counters
            self._autosuggest_count = 0
            self._hybrid_search_count = 0
            self._semantic_search_count = 0
            self._feedback_count = 0
            self._product_clicks = 0
            self._filter_usage = 0
            self._category_searches.clear()
            self._ml_ranking_calls = 0
            self._typo_corrections = 0
            self._zero_result_queries = 0
            
            # Reset performance metrics
            self._total_response_time = 0.0
            self._response_count = 0

# Global instance
metrics_counter = MetricsCounter()
