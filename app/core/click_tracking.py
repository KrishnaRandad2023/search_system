"""
🔥 Click Tracking & Feedback System for Flipkart Grid Search System

Implements comprehensive user interaction tracking:
- Search query logging
- Click tracking with position
- User behavior analytics
- A/B testing support
- Real-time feedback collection
- Performance metrics calculation
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

@dataclass
@dataclass
class SearchEvent:
    """Search event data structure"""
    session_id: str
    user_id: Optional[str]
    query: str
    timestamp: datetime
    results_count: int
    response_time_ms: float
    search_type: str  # "text", "voice", "image", etc.
    filters_applied: Dict[str, Any]
    sort_order: str
    page_number: int

@dataclass
class ClickEvent:
    """Click event data structure"""
    session_id: str
    user_id: Optional[str]
    query: str
    product_id: str
    position: int  # Position in search results (1-based)
    timestamp: datetime
    click_type: str  # "product", "wishlist", "cart", "compare"
    page_number: int
    total_results: int

@dataclass
class FeedbackEvent:
    """User feedback event"""
    session_id: str
    user_id: Optional[str]
    query: str
    product_id: Optional[str]
    feedback_type: str  # "thumbs_up", "thumbs_down", "not_relevant", "report"
    feedback_text: Optional[str]
    timestamp: datetime
    position: Optional[int]

@dataclass
class ConversionEvent:
    """Purchase/conversion event"""
    session_id: str
    user_id: Optional[str]
    query: str
    product_id: str
    purchase_amount: float
    timestamp: datetime
    conversion_type: str  # "purchase", "add_to_cart", "wishlist"

class ClickTrackingSystem:
    """
    Advanced click tracking and feedback collection system
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_tracking_tables()
        
        # Performance metrics cache
        self._metrics_cache = {}
        self._cache_expiry = {}
        
        print("🚀 Click Tracking System initialized!")
        
    def setup_tracking_tables(self):
        """Setup database tables for tracking"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                query TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                results_count INTEGER,
                response_time_ms REAL,
                search_type TEXT DEFAULT 'text',
                filters_applied TEXT,
                sort_order TEXT,
                page_number INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Click events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS click_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                query TEXT NOT NULL,
                product_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                click_type TEXT DEFAULT 'product',
                page_number INTEGER DEFAULT 1,
                total_results INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Feedback events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                query TEXT NOT NULL,
                product_id TEXT,
                feedback_type TEXT NOT NULL,
                feedback_text TEXT,
                timestamp DATETIME NOT NULL,
                position INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversion events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversion_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                query TEXT NOT NULL,
                product_id TEXT NOT NULL,
                purchase_amount REAL,
                timestamp DATETIME NOT NULL,
                conversion_type TEXT DEFAULT 'purchase',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                total_searches INTEGER DEFAULT 0,
                total_clicks INTEGER DEFAULT 0,
                total_conversions INTEGER DEFAULT 0,
                user_agent TEXT,
                ip_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_query ON search_events(query)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_click_product ON click_events(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_click_position ON click_events(position)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversion_product ON conversion_events(product_id)")
        
        conn.commit()
        conn.close()
        
    def track_search(self, search_event: SearchEvent) -> str:
        """Track a search event"""
        
        event_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO search_events (
                id, session_id, user_id, query, timestamp, results_count,
                response_time_ms, search_type, filters_applied, sort_order, page_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, search_event.session_id, search_event.user_id,
            search_event.query, search_event.timestamp, search_event.results_count,
            search_event.response_time_ms, search_event.search_type,
            json.dumps(search_event.filters_applied), search_event.sort_order,
            search_event.page_number
        ))
        
        # Update session stats
        self._update_session_stats(search_event.session_id, 'search')
        
        conn.commit()
        conn.close()
        
        return event_id
        
    def track_click(self, click_event: ClickEvent) -> str:
        """Track a click event"""
        
        event_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO click_events (
                id, session_id, user_id, query, product_id, position,
                timestamp, click_type, page_number, total_results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, click_event.session_id, click_event.user_id,
            click_event.query, click_event.product_id, click_event.position,
            click_event.timestamp, click_event.click_type,
            click_event.page_number, click_event.total_results
        ))
        
        # Update session stats
        self._update_session_stats(click_event.session_id, 'click')
        
        # Update product click counts
        self._update_product_clicks(click_event.product_id)
        
        conn.commit()
        conn.close()
        
        return event_id
        
    def track_feedback(self, feedback_event: FeedbackEvent) -> str:
        """Track a feedback event"""
        
        event_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback_events (
                id, session_id, user_id, query, product_id, feedback_type,
                feedback_text, timestamp, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, feedback_event.session_id, feedback_event.user_id,
            feedback_event.query, feedback_event.product_id, feedback_event.feedback_type,
            feedback_event.feedback_text, feedback_event.timestamp, feedback_event.position
        ))
        
        conn.commit()
        conn.close()
        
        return event_id
        
    def track_conversion(self, conversion_event: ConversionEvent) -> str:
        """Track a conversion event"""
        
        event_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversion_events (
                id, session_id, user_id, query, product_id, purchase_amount,
                timestamp, conversion_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, conversion_event.session_id, conversion_event.user_id,
            conversion_event.query, conversion_event.product_id, conversion_event.purchase_amount,
            conversion_event.timestamp, conversion_event.conversion_type
        ))
        
        # Update session stats
        self._update_session_stats(conversion_event.session_id, 'conversion')
        
        conn.commit()
        conn.close()
        
        return event_id
        
    def _update_session_stats(self, session_id: str, event_type: str):
        """Update session statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if session exists
        cursor.execute("SELECT session_id FROM user_sessions WHERE session_id = ?", (session_id,))
        if not cursor.fetchone():
            # Create new session
            cursor.execute("""
                INSERT INTO user_sessions (session_id, start_time)
                VALUES (?, ?)
            """, (session_id, datetime.now()))
            
        # Update counters
        if event_type == 'search':
            cursor.execute("""
                UPDATE user_sessions 
                SET total_searches = total_searches + 1, end_time = ?
                WHERE session_id = ?
            """, (datetime.now(), session_id))
        elif event_type == 'click':
            cursor.execute("""
                UPDATE user_sessions 
                SET total_clicks = total_clicks + 1, end_time = ?
                WHERE session_id = ?
            """, (datetime.now(), session_id))
        elif event_type == 'conversion':
            cursor.execute("""
                UPDATE user_sessions 
                SET total_conversions = total_conversions + 1, end_time = ?
                WHERE session_id = ?
            """, (datetime.now(), session_id))
            
        conn.commit()
        conn.close()
        
    def _update_product_clicks(self, product_id: str):
        """Update product click count in products table"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE products 
                SET click_count = click_count + 1
                WHERE id = ?
            """, (product_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating product clicks: {e}")
            
    def get_search_metrics(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Get search performance metrics"""
        
        cache_key = f"search_metrics_{time_period_hours}"
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
            
        start_time = datetime.now() - timedelta(hours=time_period_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total searches
        cursor.execute("""
            SELECT COUNT(*) FROM search_events 
            WHERE timestamp >= ?
        """, (start_time,))
        total_searches = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time_ms) FROM search_events 
            WHERE timestamp >= ? AND response_time_ms IS NOT NULL
        """, (start_time,))
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Top queries
        cursor.execute("""
            SELECT query, COUNT(*) as search_count
            FROM search_events 
            WHERE timestamp >= ?
            GROUP BY query
            ORDER BY search_count DESC
            LIMIT 10
        """, (start_time,))
        top_queries = cursor.fetchall()
        
        # Zero results queries
        cursor.execute("""
            SELECT COUNT(*) FROM search_events 
            WHERE timestamp >= ? AND results_count = 0
        """, (start_time,))
        zero_results_count = cursor.fetchone()[0]
        
        conn.close()
        
        metrics = {
            'total_searches': total_searches,
            'avg_response_time_ms': round(avg_response_time, 2),
            'zero_results_rate': round(zero_results_count / max(total_searches, 1), 3),
            'top_queries': [{'query': q, 'count': c} for q, c in top_queries],
            'time_period_hours': time_period_hours
        }
        
        # Cache results
        self._metrics_cache[cache_key] = metrics
        self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
        
        return metrics
        
    def get_click_metrics(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Get click performance metrics"""
        
        cache_key = f"click_metrics_{time_period_hours}"
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
            
        start_time = datetime.now() - timedelta(hours=time_period_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total clicks
        cursor.execute("""
            SELECT COUNT(*) FROM click_events 
            WHERE timestamp >= ?
        """, (start_time,))
        total_clicks = cursor.fetchone()[0]
        
        # CTR calculation
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM search_events 
            WHERE timestamp >= ?
        """, (start_time,))
        unique_searches = cursor.fetchone()[0]
        
        ctr = round(total_clicks / max(unique_searches, 1), 3)
        
        # Position-based CTR
        cursor.execute("""
            SELECT position, COUNT(*) as clicks
            FROM click_events 
            WHERE timestamp >= ?
            GROUP BY position
            ORDER BY position
            LIMIT 10
        """, (start_time,))
        position_ctr = cursor.fetchall()
        
        # Top clicked products
        cursor.execute("""
            SELECT product_id, COUNT(*) as click_count
            FROM click_events 
            WHERE timestamp >= ?
            GROUP BY product_id
            ORDER BY click_count DESC
            LIMIT 10
        """, (start_time,))
        top_products = cursor.fetchall()
        
        conn.close()
        
        metrics = {
            'total_clicks': total_clicks,
            'overall_ctr': ctr,
            'position_ctr': [{'position': p, 'clicks': c} for p, c in position_ctr],
            'top_clicked_products': [{'product_id': p, 'clicks': c} for p, c in top_products],
            'time_period_hours': time_period_hours
        }
        
        # Cache results
        self._metrics_cache[cache_key] = metrics
        self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
        
        return metrics
        
    def get_conversion_metrics(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Get conversion metrics"""
        
        start_time = datetime.now() - timedelta(hours=time_period_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total conversions
        cursor.execute("""
            SELECT COUNT(*), SUM(purchase_amount)
            FROM conversion_events 
            WHERE timestamp >= ?
        """, (start_time,))
        result = cursor.fetchone()
        total_conversions = result[0]
        total_revenue = result[1] or 0
        
        # Conversion rate
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM click_events 
            WHERE timestamp >= ?
        """, (start_time,))
        unique_clickers = cursor.fetchone()[0]
        
        conversion_rate = round(total_conversions / max(unique_clickers, 1), 3)
        
        # Average order value
        avg_order_value = round(total_revenue / max(total_conversions, 1), 2)
        
        conn.close()
        
        return {
            'total_conversions': total_conversions,
            'total_revenue': total_revenue,
            'conversion_rate': conversion_rate,
            'avg_order_value': avg_order_value,
            'time_period_hours': time_period_hours
        }
        
    def get_user_behavior_insights(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Get user behavior insights"""
        
        start_time = datetime.now() - timedelta(hours=time_period_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Session duration analysis
        cursor.execute("""
            SELECT 
                AVG((julianday(end_time) - julianday(start_time)) * 24 * 60) as avg_session_minutes,
                AVG(total_searches) as avg_searches_per_session,
                AVG(total_clicks) as avg_clicks_per_session
            FROM user_sessions 
            WHERE start_time >= ? AND end_time IS NOT NULL
        """, (start_time,))
        
        session_stats = cursor.fetchone()
        
        # Query refinement patterns
        cursor.execute("""
            SELECT 
                s1.query as original_query,
                s2.query as refined_query,
                COUNT(*) as refinement_count
            FROM search_events s1
            JOIN search_events s2 ON s1.session_id = s2.session_id
            WHERE s1.timestamp >= ? 
                AND s2.timestamp > s1.timestamp
                AND s1.query != s2.query
                AND (julianday(s2.timestamp) - julianday(s1.timestamp)) * 24 * 60 < 5
            GROUP BY s1.query, s2.query
            ORDER BY refinement_count DESC
            LIMIT 10
        """, (start_time,))
        
        query_refinements = cursor.fetchall()
        
        conn.close()
        
        return {
            'avg_session_duration_minutes': round(session_stats[0] or 0, 1),
            'avg_searches_per_session': round(session_stats[1] or 0, 1),
            'avg_clicks_per_session': round(session_stats[2] or 0, 1),
            'top_query_refinements': [
                {'from': orig, 'to': refined, 'count': count} 
                for orig, refined, count in query_refinements
            ],
            'time_period_hours': time_period_hours
        }
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        return (cache_key in self._cache_expiry and 
                datetime.now() < self._cache_expiry[cache_key])
                
    def generate_sample_data(self, num_events: int = 1000):
        """Generate sample tracking data for testing"""
        
        print(f"🔄 Generating {num_events} sample tracking events...")
        
        import random
        from faker import Faker
        fake = Faker()
        
        # Sample queries and products
        sample_queries = [
            "iphone 15", "samsung galaxy", "laptop", "headphones", "nike shoes",
            "bluetooth speaker", "smartwatch", "gaming laptop", "winter jacket",
            "books", "kitchen appliances", "mobile cover", "air conditioner"
        ]
        
        # Get some product IDs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products LIMIT 100")
        product_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not product_ids:
            print("⚠️  No products found in database. Please generate products first.")
            return
            
        # Generate events
        for i in range(num_events):
            if i % 100 == 0:
                print(f"Generated {i}/{num_events} events...")
                
            session_id = str(uuid.uuid4())[:8]
            user_id = fake.uuid4() if random.random() > 0.3 else None
            query = random.choice(sample_queries)
            
            # Generate search event
            search_event = SearchEvent(
                session_id=session_id,
                user_id=user_id,
                query=query,
                timestamp=fake.date_time_between(start_date='-7d', end_date='now'),
                results_count=random.randint(5, 50),
                response_time_ms=random.uniform(50, 500),
                search_type="text",
                filters_applied={},
                sort_order="relevance",
                page_number=1
            )
            
            self.track_search(search_event)
            
            # Generate click events (probabilistic)
            if random.random() > 0.3:  # 70% chance of click
                num_clicks = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
                
                for click_num in range(num_clicks):
                    click_event = ClickEvent(
                        session_id=session_id,
                        user_id=user_id,
                        query=query,
                        product_id=random.choice(product_ids),
                        position=random.choices(range(1, 11), weights=[30, 20, 15, 10, 8, 6, 4, 3, 2, 2])[0],
                        timestamp=search_event.timestamp + timedelta(seconds=random.randint(5, 300)),
                        click_type="product",
                        page_number=1,
                        total_results=search_event.results_count
                    )
                    
                    self.track_click(click_event)
                    
                    # Generate conversion (probabilistic)
                    if random.random() > 0.9:  # 10% conversion rate
                        conversion_event = ConversionEvent(
                            session_id=session_id,
                            user_id=user_id,
                            query=query,
                            product_id=click_event.product_id,
                            purchase_amount=random.uniform(500, 15000),
                            timestamp=click_event.timestamp + timedelta(minutes=random.randint(5, 60)),
                            conversion_type="purchase"
                        )
                        
                        self.track_conversion(conversion_event)
                        
        print(f"✅ Generated {num_events} sample tracking events!")

# Test the tracking system
if __name__ == "__main__":
    from pathlib import Path
    
    db_path = str(Path(__file__).parent.parent.parent / "data" / "db" / "flipkart_products.db")
    
    # Initialize tracking system
    tracking_system = ClickTrackingSystem(db_path)
    
    # Generate sample data
    tracking_system.generate_sample_data(500)
    
    # Get metrics
    search_metrics = tracking_system.get_search_metrics(24)
    click_metrics = tracking_system.get_click_metrics(24)
    conversion_metrics = tracking_system.get_conversion_metrics(24)
    behavior_insights = tracking_system.get_user_behavior_insights(24)
    
    print("\n📊 TRACKING SYSTEM METRICS")
    print("=" * 50)
    print(f"Search Metrics: {search_metrics}")
    print(f"Click Metrics: {click_metrics}")
    print(f"Conversion Metrics: {conversion_metrics}")
    print(f"Behavior Insights: {behavior_insights}")
    
    print("\n✅ Click tracking system test completed!")
