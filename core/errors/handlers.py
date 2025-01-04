from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from core.logger import log_error
import tweepy

async def error_handler(request: Request, exc: Exception):
    """Global error handler"""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    if isinstance(exc, tweepy.errors.TweepyException):
        log_error(exc, "Twitter API Error")
        return JSONResponse(
            status_code=400,
            content={"detail": "Twitter API error occurred"}
        )
    
    # Log unexpected errors
    log_error(exc, f"Unexpected error on {request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

class APIError(Exception):
    """Custom API error"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message) 