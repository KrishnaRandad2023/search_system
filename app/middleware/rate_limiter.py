"""
Rate Limiting Middleware
Addresses security vulnerabilities by implementing request throttling
"""

import time
import json
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API endpoints"""
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 20):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Storage for client tokens and timestamps
        self._clients: Dict[str, Dict] = defaultdict(lambda: {
            'tokens': burst_size,
            'last_refill': time.time(),
            'request_history': deque(maxlen=100)  # Track recent requests
        })
        
        # Cleanup old clients periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Use IP address as primary identifier
        client_ip = request.client.host
        
        # Add user agent for additional differentiation
        user_agent = request.headers.get('user-agent', 'unknown')
        
        # Create composite identifier
        return f"{client_ip}:{hash(user_agent) % 1000000}"
        
    def _refill_tokens(self, client_data: Dict) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_elapsed = now - client_data['last_refill']
        
        # Calculate tokens to add
        tokens_to_add = time_elapsed * self.refill_rate
        
        # Update token count (don't exceed burst size)
        client_data['tokens'] = min(
            self.burst_size,
            client_data['tokens'] + tokens_to_add
        )
        client_data['last_refill'] = now
        
    def _cleanup_old_clients(self) -> None:
        """Remove inactive clients to prevent memory leaks"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
            
        # Remove clients inactive for more than 1 hour
        inactive_threshold = now - 3600
        clients_to_remove = [
            client_id for client_id, data in self._clients.items()
            if data['last_refill'] < inactive_threshold
        ]
        
        for client_id in clients_to_remove:
            del self._clients[client_id]
            
        self._last_cleanup = now
        
        if clients_to_remove:
            logger.info(f"Cleaned up {len(clients_to_remove)} inactive rate limit clients")
            
    def is_allowed(self, request: Request) -> tuple[bool, Dict]:
        """Check if request is allowed and return rate limit info"""
        client_id = self._get_client_id(request)
        client_data = self._clients[client_id]
        
        # Refill tokens
        self._refill_tokens(client_data)
        
        # Check if request is allowed
        if client_data['tokens'] >= 1:
            client_data['tokens'] -= 1
            client_data['request_history'].append({
                'timestamp': time.time(),
                'endpoint': str(request.url.path),
                'method': request.method
            })
            
            # Periodic cleanup
            self._cleanup_old_clients()
            
            return True, {
                'allowed': True,
                'remaining': int(client_data['tokens']),
                'reset_time': client_data['last_refill'] + (60 / self.refill_rate),
                'limit': self.requests_per_minute
            }
        else:
            return False, {
                'allowed': False,
                'remaining': 0,
                'reset_time': client_data['last_refill'] + (60 / self.refill_rate),
                'limit': self.requests_per_minute,
                'retry_after': int((1 - client_data['tokens']) / self.refill_rate)
            }
            
    def get_client_stats(self, request: Request) -> Dict:
        """Get statistics for a specific client"""
        client_id = self._get_client_id(request)
        client_data = self._clients.get(client_id)
        
        if not client_data:
            return {'error': 'Client not found'}
            
        recent_requests = list(client_data['request_history'])
        
        return {
            'client_id': client_id[:20] + '...',  # Truncate for privacy
            'current_tokens': client_data['tokens'],
            'last_refill': client_data['last_refill'],
            'recent_requests_count': len(recent_requests),
            'recent_endpoints': list(set(r['endpoint'] for r in recent_requests[-10:]))
        }
        
    def get_global_stats(self) -> Dict:
        """Get global rate limiter statistics"""
        now = time.time()
        active_clients = sum(
            1 for data in self._clients.values()
            if now - data['last_refill'] < 300  # Active in last 5 minutes
        )
        
        return {
            'total_clients': len(self._clients),
            'active_clients': active_clients,
            'requests_per_minute_limit': self.requests_per_minute,
            'burst_size': self.burst_size,
            'last_cleanup': self._last_cleanup
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def initialize_rate_limiter(requests_per_minute: int = 100, burst_size: int = 20):
    """Initialize the global rate limiter"""
    global _rate_limiter
    _rate_limiter = RateLimiter(requests_per_minute, burst_size)
    logger.info(f"Rate limiter initialized: {requests_per_minute} req/min, burst: {burst_size}")


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter"""
    if _rate_limiter is None:
        # Initialize with default values if not already initialized
        initialize_rate_limiter()
    return _rate_limiter


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 100, burst_size: int = 20):
        self.app = app
        initialize_rate_limiter(requests_per_minute, burst_size)
        
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ['/health', '/metrics', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)
            
        rate_limiter = get_rate_limiter()
        allowed, rate_info = rate_limiter.is_allowed(request)
        
        if not allowed:
            # Return rate limit exceeded response
            response_data = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_info['limit']} per minute",
                "retry_after": rate_info.get('retry_after', 60)
            }
            
            response = JSONResponse(
                status_code=429,
                content=response_data
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
            response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
            response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_time']))
            response.headers["Retry-After"] = str(rate_info.get('retry_after', 60))
            
            return response
            
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_time']))
        
        return response
