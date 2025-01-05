from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    twitter_id = Column(String, unique=True)
    username = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_processed = Column(DateTime)
    engagement_data = Column(JSON)
    pult_score = Column(Float, default=0.0)
    is_enterprise = Column(Boolean, default=False) 