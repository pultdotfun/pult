import pytest
from sqlalchemy.orm import Session
from core.tasks.processor import BackgroundProcessor
from core.websocket.handler import WebSocketManager
from models.user import User
from models.engagement import Engagement
from datetime import datetime

@pytest.fixture
def background_processor(db: Session):
    websocket_manager = WebSocketManager()
    return BackgroundProcessor(db, websocket_manager)

@pytest.mark.asyncio
async def test_process_user_data(background_processor, db: Session):
    # Create test user
    user = User(
        twitter_id="test_id",
        username="test_user",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    
    # Create test engagements
    engagement = Engagement(
        user_id=user.id,
        tweet_id="test_tweet",
        engagement_type="like",
        created_at=datetime.utcnow()
    )
    db.add(engagement)
    db.commit()
    
    # Process data
    await background_processor.process_user_data(user.id)
    
    # Verify processing
    processed_user = db.query(User).filter(User.id == user.id).first()
    assert processed_user.pult_score is not None
    assert processed_user.last_processed is not None 