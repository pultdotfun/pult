import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import asyncio
from main import app
from core.websocket.handler import WebSocketManager
from core.auth.middleware import AuthMiddleware
from datetime import datetime

# Test client
client = TestClient(app)

# Mock auth handler
auth_handler = AuthMiddleware()

@pytest.fixture
def websocket_manager():
    return WebSocketManager()

@pytest.mark.asyncio
async def test_websocket_connection():
    token = auth_handler.create_token(user_id=1, is_enterprise=False)
    
    with client.websocket_connect(f"/ws/1?token={token}") as websocket:
        # Test connection
        data = {"type": "ping"}
        await websocket.send_json(data)
        
        # Verify response
        response = await websocket.receive_json()
        assert response["type"] == "pong"

@pytest.mark.asyncio
async def test_websocket_updates():
    token = auth_handler.create_token(user_id=1, is_enterprise=False)
    
    with client.websocket_connect(f"/ws/1?token={token}") as websocket:
        # Trigger processing
        response = client.post(
            "/api/process/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Wait for update
        update = await websocket.receive_json()
        assert "score" in update
        assert "timestamp" in update 