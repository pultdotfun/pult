import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User
from models.engagement import Engagement

class PULTProcessor:
    def __init__(self, db: Session):
        self.db = db
        
    def process_user_data(self, user_id: int):
        """Process user's engagement data using PULT algorithm"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        # Get user engagements
        engagements = self.db.query(Engagement).filter(
            Engagement.user_id == user_id
        ).all()
        
        # Create engagement tensor
        engagement_tensor = self._create_engagement_tensor(engagements)
        
        # Calculate PULT score
        pult_score = self._calculate_pult_score(engagement_tensor)
        
        # Update user's PULT score
        user.pult_score = float(pult_score)
        user.last_processed = datetime.utcnow()
        self.db.commit()
        
        return pult_score
    
    def _create_engagement_tensor(self, engagements):
        """Convert engagements into a tensor representation"""
        # Initialize basic tensor
        tensor = np.zeros((3, 10))  # 3 types (like,retweet,reply) x 10 time periods
        
        for eng in engagements:
            eng_type_idx = {
                'like': 0,
                'retweet': 1,
                'reply': 2
            }.get(eng.engagement_type, 0)
            
            # Calculate time period (simplified)
            time_idx = min(int((datetime.utcnow() - eng.created_at).days / 3), 9)
            
            # Add to tensor with sentiment weighting
            tensor[eng_type_idx][time_idx] += 1 + (eng.sentiment_score or 0)
            
        return tensor
    
    def _calculate_pult_score(self, tensor):
        """Calculate PULT score from engagement tensor"""
        # Weights for different engagement types
        type_weights = np.array([0.5, 0.8, 1.0])
        
        # Time decay weights
        time_weights = np.exp(-np.arange(10) * 0.2)
        
        # Calculate weighted score
        weighted_tensor = tensor * time_weights
        type_scores = np.sum(weighted_tensor, axis=1)
        final_score = np.sum(type_scores * type_weights)
        
        # Normalize to 0-100 range
        normalized_score = min(100, max(0, final_score * 10))
        
        return normalized_score 