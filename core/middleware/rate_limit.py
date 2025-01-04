from fastapi import HTTPException
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
        
    def check_rate_limit(self, client_id: str):
        """Check if client has exceeded rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        with self.lock:
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again in a minute."
                )
            
            # Add new request
            self.requests[client_id].append(now)

class RateLimitMiddleware:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        
    async def __call__(self, request, call_next):
        # Get client IP or token as identifier
        client_id = request.headers.get('authorization', request.client.host)
        
        # Check rate limit
        self.rate_limiter.check_rate_limit(client_id)
        
        # Process request
        response = await call_next(request)
        return response 