from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.user import User
from models.engagement import Engagement
from fastapi import HTTPException

class EnterpriseService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_aggregated_data(self, days: int = 30):
        """Get aggregated PULT data for enterprise users"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get average PULT scores over time
        pult_trends = self.db.query(
            User.id,
            User.pult_score,
            User.last_processed
        ).filter(
            User.last_processed >= cutoff_date
        ).all()
        
        # Get engagement distributions
        engagement_dist = self.db.query(
            Engagement.engagement_type,
            func.count(Engagement.id).label('count')
        ).filter(
            Engagement.created_at >= cutoff_date
        ).group_by(
            Engagement.engagement_type
        ).all()
        
        return {
            "pult_trends": [
                {
                    "user_id": p[0],
                    "score": p[1],
                    "timestamp": p[2].isoformat()
                } for p in pult_trends
            ],
            "engagement_distribution": {
                e[0]: e[1] for e in engagement_dist
            }
        }
    
    async def verify_enterprise_access(self, token: str):
        """Verify enterprise API token"""
        # TODO: Implement proper token verification
        return token == "test_enterprise_token" 