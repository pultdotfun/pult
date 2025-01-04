from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .user import Base
import datetime

class Engagement(Base):
    __tablename__ = "engagements"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    tweet_id = Column(String)
    engagement_type = Column(String)  # like, retweet, reply
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="engagements") 