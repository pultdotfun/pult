from prometheus_client import Counter, Histogram, Info, Gauge
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

# WebSocket metrics
WEBSOCKET_CONNECTIONS = Gauge(
    'pult_websocket_connections',
    'Number of active WebSocket connections',
    ['user_id']
)

WEBSOCKET_MESSAGES = Counter(
    'pult_websocket_messages_total',
    'Number of WebSocket messages processed',
    ['direction', 'type']
)

# Background task metrics
BACKGROUND_TASKS = Counter(
    'pult_background_tasks_total',
    'Number of background tasks processed',
    ['task_type', 'status']
)

PROCESSING_TIME = Histogram(
    'pult_processing_time_seconds',
    'Time taken to process user data',
    ['task_type']
)

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