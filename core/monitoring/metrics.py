from prometheus_client import Counter, Histogram, Info
import time

# Request metrics
REQUEST_COUNT = Counter(
    'pult_request_count',
    'Number of requests received',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'pult_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

# Business metrics
PULT_SCORE_UPDATES = Counter(
    'pult_score_updates_total',
    'Number of PULT score updates'
)

ENGAGEMENT_PROCESSED = Counter(
    'pult_engagements_processed_total',
    'Number of engagements processed'
)

# System info
SYSTEM_INFO = Info('pult_system', 'System information')

class MetricsMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record request metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        # Record latency
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response 