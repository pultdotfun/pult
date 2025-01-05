import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models.user import User
from models.engagement import Engagement
from core.analytics.processor import AnalyticsProcessor
from core.scheduler.tasks import TaskScheduler
from datetime import datetime, timedelta
import asyncio

client = TestClient(app)

@pytest.fixture
def test_user(db: Session):
    user = User(
        twitter_id="test_integration_id",
        username="test_integration_user",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    return user

@pytest.mark.asyncio
async def test_full_user_flow(test_user, db: Session):
    """Test complete user flow from auth to analytics"""
    # Create auth token
    token = auth_handler.create_token(test_user.id)
    
    # Add test engagements
    engagements = [
        Engagement(
            user_id=test_user.id,
            tweet_id=f"tweet_{i}",
            engagement_type="like",
            created_at=datetime.utcnow() - timedelta(hours=i)
        ) for i in range(5)
    ]
    db.bulk_save_objects(engagements)
    db.commit()
    
    # Test WebSocket connection
    with client.websocket_connect(f"/ws/{test_user.id}?token={token}") as websocket:
        # Trigger processing
        response = client.post(
            f"/api/process/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Verify WebSocket update
        data = await websocket.receive_json()
        assert "score" in data
        assert "timestamp" in data
    
    # Test analytics
    analytics = AnalyticsProcessor(db)
    insights = await analytics.get_user_insights(test_user.id)
    assert insights["total_engagements"] == 5
    assert insights["most_common_type"] == "like"

@pytest.mark.asyncio
async def test_enterprise_analytics(db: Session):
    """Test enterprise analytics pipeline"""
    # Create enterprise user
    enterprise_user = User(
        twitter_id="enterprise_test",
        username="enterprise_user",
        is_enterprise=True,
        created_at=datetime.utcnow()
    )
    db.add(enterprise_user)
    db.commit()
    
    token = auth_handler.create_token(enterprise_user.id, is_enterprise=True)
    
    # Test enterprise data endpoint
    response = client.get(
        "/api/enterprise/data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "pult_trends" in data
    assert "engagement_patterns" in data

@pytest.mark.asyncio
async def test_scheduler(db: Session):
    """Test task scheduler"""
    scheduler = TaskScheduler(db, websocket_manager)
    scheduler.start()
    
    # Wait for initial tasks
    await asyncio.sleep(1)
    
    # Verify scheduler is running
    assert scheduler.scheduler.running
    
    # Clean up
    scheduler.scheduler.shutdown() 