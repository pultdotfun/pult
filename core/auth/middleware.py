from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.user import User
import jwt
from datetime import datetime, timedelta
import os

class AuthMiddleware(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=["HS256"])
            user_id: int = payload.get("user_id")
            token_type: str = payload.get("type", "user")
            
            if not user_id:
                raise HTTPException(status_code=403, detail="Invalid token payload")
                
            request.state.user_id = user_id
            request.state.token_type = token_type
            
            return credentials.credentials
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=403, detail="Could not validate credentials")

    def create_token(self, user_id: int, is_enterprise: bool = False):
        """Create JWT token for user"""
        expires_delta = timedelta(days=30 if is_enterprise else 7)
        
        payload = {
            "user_id": user_id,
            "type": "enterprise" if is_enterprise else "user",
            "exp": datetime.utcnow() + expires_delta
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256") 