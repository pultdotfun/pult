from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class UserBase(BaseModel):
    twitter_id: str
    username: str
    
    @validator('twitter_id')
    def validate_twitter_id(cls, v):
        if not v.strip():
            raise ValueError('Twitter ID cannot be empty')
        return v

class UserCreate(UserBase):
    access_token: str
    refresh_token: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_enterprise: bool = False
    pult_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class EngagementCreate(BaseModel):
    tweet_id: str
    engagement_type: str = Field(..., regex='^(like|retweet|reply)$')
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)

class EnterpriseData(BaseModel):
    pult_trends: List[Dict[str, float]]
    engagement_distribution: Dict[str, int]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WebSocketMessage(BaseModel):
    type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow) 