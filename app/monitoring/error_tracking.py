"""
Enhanced Error Handling and Monitoring
Addresses error handling gaps and monitoring issues
"""

import time
import traceback
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Track and analyze application errors"""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)
        
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error occurrence"""
        error_info = {
            'timestamp': datetime.now(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.errors.append(error_info)
        self.error_counts[error_info['type']] += 1
        
        # Track error patterns
        pattern_key = f"{error_info['type']}:{error_info['message'][:100]}"
        self.error_patterns[pattern_key].append(error_info['timestamp'])
        
        # Log the error
        logger.error(
            f"Error tracked: {error_info['type']} - {error_info['message']}",
            extra={'context': context}
        )
        
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e['timestamp'] > cutoff_time]
        
        # Error frequency analysis
        error_frequency = defaultdict(int)
        for error in recent_errors:
            error_frequency[error['type']] += 1
            
        # Error rate calculation
        total_errors = len(recent_errors)
        error_rate = total_errors / max(hours, 1)  # errors per hour
        
        # Most frequent errors
        top_errors = sorted(
            error_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_errors': total_errors,
            'error_rate_per_hour': round(error_rate, 2),
            'unique_error_types': len(error_frequency),
            'top_errors': [{'type': t, 'count': c} for t, c in top_errors],
            'time_period_hours': hours
        }
        
    def get_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for insights"""
        patterns = {}
        
        for pattern, timestamps in self.error_patterns.items():
            if len(timestamps) >= 3:  # Only patterns with multiple occurrences
                time_diffs = []
                for i in range(1, len(timestamps)):
                    diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                    time_diffs.append(diff)
                
                patterns[pattern] = {
                    'occurrences': len(timestamps),
                    'first_seen': min(timestamps),
                    'last_seen': max(timestamps),
                    'avg_interval_seconds': sum(time_diffs) / len(time_diffs) if time_diffs else 0
                }
                
        return patterns


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.request_times = deque(maxlen=max_samples)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        
    def track_request(self, endpoint: str, duration: float, success: bool = True):
        """Track a request's performance"""
        timestamp = datetime.now()
        
        self.request_times.append({
            'timestamp': timestamp,
            'endpoint': endpoint,
            'duration': duration,
            'success': success
        })
        
        # Update endpoint statistics
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        if not success:
            stats['errors'] += 1
            
    def get_performance_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_requests = [r for r in self.request_times if r['timestamp'] > cutoff_time]
        
        if not recent_requests:
            return {'message': 'No recent requests'}
            
        # Overall statistics
        durations = [r['duration'] for r in recent_requests]
        successful_requests = [r for r in recent_requests if r['success']]
        
        avg_response_time = sum(durations) / len(durations)
        success_rate = len(successful_requests) / len(recent_requests)
        
        # Endpoint performance
        endpoint_performance = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats['count'] > 0:
                endpoint_performance[endpoint] = {
                    'requests': stats['count'],
                    'avg_time_ms': round((stats['total_time'] / stats['count']) * 1000, 2),
                    'min_time_ms': round(stats['min_time'] * 1000, 2),
                    'max_time_ms': round(stats['max_time'] * 1000, 2),
                    'error_rate': round(stats['errors'] / stats['count'], 3),
                    'success_rate': round(1 - (stats['errors'] / stats['count']), 3)
                }
                
        return {
            'total_requests': len(recent_requests),
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'success_rate': round(success_rate, 3),
            'requests_per_hour': len(recent_requests) / max(hours, 1),
            'endpoint_performance': dict(sorted(
                endpoint_performance.items(),
                key=lambda x: x[1]['requests'],
                reverse=True
            )[:10]),
            'time_period_hours': hours
        }


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.checks = {}
        self.last_results = {}
        
    def register_check(self, name: str, check_func, critical: bool = False):
        """Register a health check"""
        self.checks[name] = {
            'func': check_func,
            'critical': critical,
            'last_run': None,
            'last_result': None
        }
        
    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_status = 'healthy'
        
        for name, check_info in self.checks.items():
            try:
                # Run the check with timeout
                result = await asyncio.wait_for(
                    check_info['func'](),
                    timeout=30.0
                )
                
                check_info['last_run'] = datetime.now()
                check_info['last_result'] = result
                
                results[name] = {
                    'status': 'healthy',
                    'result': result,
                    'timestamp': check_info['last_run'].isoformat()
                }
                
            except asyncio.TimeoutError:
                results[name] = {
                    'status': 'timeout',
                    'error': 'Health check timed out',
                    'timestamp': datetime.now().isoformat()
                }
                if check_info['critical']:
                    overall_status = 'unhealthy'
                    
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                if check_info['critical']:
                    overall_status = 'unhealthy'
                    
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }


# Global instances
_error_tracker: Optional[ErrorTracker] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_health_checker: Optional[HealthChecker] = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_health_checker() -> HealthChecker:
    """Get the global health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


@asynccontextmanager
async def track_performance(endpoint: str):
    """Context manager to track request performance"""
    monitor = get_performance_monitor()
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception as e:
        success = False
        error_tracker = get_error_tracker()
        error_tracker.track_error(e, {'endpoint': endpoint})
        raise
    finally:
        duration = time.time() - start_time
        monitor.track_request(endpoint, duration, success)


def setup_monitoring():
    """Initialize monitoring components"""
    health_checker = get_health_checker()
    
    # Register basic health checks
    async def database_check():
        """Check database connectivity"""
        from app.db.connection_pool import check_database_health
        from app.config.settings import get_settings
        
        settings = get_settings()
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        return check_database_health(db_path)
    
    async def memory_check():
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'usage_percent': memory.percent,
                'available_mb': memory.available / (1024 * 1024)
            }
        except ImportError:
            return {'status': 'psutil not available'}
    
    # Register checks
    health_checker.register_check('database', database_check, critical=True)
    health_checker.register_check('memory', memory_check, critical=False)
    
    logger.info("Monitoring system initialized")


# Monitoring decorator
def monitor_endpoint(endpoint_name: str = None):
    """Decorator to automatically monitor endpoint performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            name = endpoint_name or func.__name__
            async with track_performance(name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
