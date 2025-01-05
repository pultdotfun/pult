from fastapi import FastAPI, HTTPException, Depends, Header, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import tweepy
import os
from dotenv import load_dotenv
from models.user import User
from database import get_db
from services.enterprise.service import EnterpriseService
from core.auth.middleware import AuthMiddleware
from core.errors.handlers import error_handler, APIError
from core.logger import log_info, log_error
from fastapi.openapi.utils import get_openapi
from core.monitoring.metrics import MetricsMiddleware, PULT_SCORE_UPDATES, ENGAGEMENT_PROCESSED
from prometheus_client import make_asgi_app
from core.middleware.rate_limit import RateLimiter, RateLimitMiddleware
from core.cache.redis import RedisCache
from schemas.base import UserResponse, EnterpriseData, WebSocketMessage
from typing import List
from core.scheduler.tasks import TaskScheduler

load_dotenv()

app = FastAPI(
    title="PULT API",
    description="API for Predictive Update Learning Tensors (PULT) system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pult.fun"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twitter OAuth Config
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
TWITTER_REDIRECT_URI = "https://pult.fun/callback"

# Initialize auth
auth_handler = AuthMiddleware()

# Add exception handler
app.add_exception_handler(Exception, error_handler)

# Create metrics endpoint
metrics_app = make_asgi_app()

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Mount metrics endpoint
app.mount("/metrics", metrics_app)

# Initialize rate limiter and cache
rate_limiter = RateLimiter(requests_per_minute=60)
cache = RedisCache()

# Add rate limit middleware
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Initialize scheduler
scheduler = None

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="PULT API",
        version="1.0.0",
        description="""
        # PULT (Predictive Update Learning Tensors) API
        
        This API provides access to the PULT system for analyzing and improving social media engagement.
        
        ## Features
        
        * Real-time PULT score updates via WebSocket
        * Enterprise analytics and insights
        * Background processing and scheduling
        * Comprehensive monitoring and metrics
        
        ## Authentication
        
        All endpoints require authentication via JWT tokens. Enterprise features require enterprise-level access.
        
        ## Rate Limiting
        
        API requests are limited to 60 requests per minute per client.
        """,
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Update endpoint documentation
@app.get(
    "/api/auth/twitter/url",
    tags=["Authentication"],
    summary="Get Twitter OAuth URL",
    response_description="Twitter OAuth URL for user authentication"
)
async def get_twitter_auth_url():
    """
    Generate Twitter OAuth URL for user authentication.
    
    Returns:
        dict: Contains the OAuth URL for Twitter authentication
    """
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=TWITTER_CLIENT_ID,
        client_secret=TWITTER_CLIENT_SECRET,
        redirect_uri=TWITTER_REDIRECT_URI,
        scope=["tweet.read", "users.read"],
    )
    return {"url": oauth2_user_handler.get_authorization_url()}

@app.get("/api/auth/twitter/callback")
async def twitter_callback(code: str, db: Session = Depends(get_db)):
    """Handle Twitter OAuth callback"""
    try:
        log_info(f"Processing Twitter callback")
        oauth2_user_handler = tweepy.OAuth2UserHandler(
            client_id=TWITTER_CLIENT_ID,
            client_secret=TWITTER_CLIENT_SECRET,
            redirect_uri=TWITTER_REDIRECT_URI,
            scope=["tweet.read", "users.read"],
        )
        tokens = oauth2_user_handler.fetch_token(code)
        
        # Initialize client
        client = tweepy.Client(tokens["access_token"])
        twitter_user = client.get_me().data
        
        # Create or update user
        user = db.query(User).filter(User.twitter_id == str(twitter_user.id)).first()
        if not user:
            user = User(
                twitter_id=str(twitter_user.id),
                username=twitter_user.username,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token")
            )
            db.add(user)
        else:
            user.access_token = tokens["access_token"]
            user.refresh_token = tokens.get("refresh_token")
        
        db.commit()
        
        # Create JWT token
        token = auth_handler.create_token(user.id, user.is_enterprise)
        
        log_info(f"User {user.username} authenticated successfully")
        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "token": token
        }
    except Exception as e:
        log_error(e, "Twitter callback failed")
        raise

@app.get("/api/user/me", response_model=UserResponse)
async def get_user(token: str = Depends(auth_handler), db: Session = Depends(get_db)):
    """Get current user info"""
    user_id = auth_handler.get_user_id(token)
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

@app.get(
    "/api/enterprise/data",
    tags=["Enterprise"],
    summary="Get enterprise analytics data",
    response_model=EnterpriseData,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "pult_trends": {
                            "mean": 75.5,
                            "median": 80.0,
                            "std_dev": 12.3
                        },
                        "engagement_patterns": {
                            "hourly_distribution": {"0": 100, "1": 150},
                            "type_distribution": {"like": 500, "retweet": 300}
                        },
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        403: {
            "description": "Not authorized for enterprise access"
        }
    }
)
async def get_enterprise_data(
    days: int = Field(30, ge=1, le=365),
    token: str = Depends(auth_handler),
    db: Session = Depends(get_db)
):
    """
    Get aggregated PULT analytics data for enterprise users.
    
    Args:
        days (int): Number of days to analyze (default: 30)
        token (str): Enterprise API token
        
    Returns:
        dict: Contains PULT trends and engagement distribution
        
    Raises:
        HTTPException: If token is invalid or user lacks enterprise access
    """
    try:
        # Check cache first
        cache_key = f"enterprise_data_{days}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            return EnterpriseData(**cached_data)
        
        # Get fresh data
        enterprise_service = EnterpriseService(db)
        data = await enterprise_service.get_aggregated_data(days)
        
        # Cache the result
        await cache.set(cache_key, data.dict(), expire_minutes=5)
        
        # Record metrics
        PULT_SCORE_UPDATES.inc()
        ENGAGEMENT_PROCESSED.inc(len(data.get("pult_trends", [])))
        
        log_info("Enterprise data fetched successfully")
        return data
    except Exception as e:
        log_error(e, "Enterprise data fetch failed")
        raise

@app.get("/api/enterprise/verify")
async def verify_enterprise(
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    """Verify enterprise token"""
    enterprise_service = EnterpriseService(db)
    is_valid = await enterprise_service.verify_enterprise_access(token)
    
    return {
        "valid": is_valid,
        "type": "enterprise" if is_valid else "free"
    }

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int, 
    token: str
):
    try:
        if not auth_handler.verify_token(token):
            await websocket.close(code=4001)
            return
            
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                message = WebSocketMessage(**data)
                
                # Handle validated message
                await handle_websocket_message(user_id, message)
                
        except Exception as e:
            log_error(e, "WebSocket error")
            
        finally:
            await websocket_manager.disconnect(websocket, user_id)
            
    except Exception as e:
        log_error(e, "WebSocket connection error")
        await websocket.close(code=4002)

@app.on_event("startup")
async def startup_event():
    global scheduler, background_processor
    db = next(get_db())
    background_processor = BackgroundProcessor(db, websocket_manager)
    
    # Start scheduler
    scheduler = TaskScheduler(db, websocket_manager)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler:
        scheduler.scheduler.shutdown()