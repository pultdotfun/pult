# PULT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

<div align="center">
  <img src="pult.png" alt="PULT" width="200"/>
</div>

A real-time social media engagement analysis system using predictive update learning tensors.

## Core Features

- Twitter OAuth2 integration
- Real-time WebSocket score updates
- Enterprise analytics dashboard
- Automated background processing
- Prometheus/Grafana monitoring

## Implementation

### Authentication

python
@app.get("/api/auth/twitter/callback")
async def twitter_callback(code: str, db: Session = Depends(get_db)):
try:
user = await process_twitter_auth(code, db)
token = auth_handler.create_token(user.id)
return {"success": True, "token": token}
except Exception as e:
raise HTTPException(status_code=400, detail=str(e))


### WebSocket Updates

python
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str):
try:
if not auth_handler.verify_token(token):
await websocket.close(code=4001)
return
await websocket_manager.connect(websocket, user_id)
while True:
data = await websocket.receive_json()
await handle_websocket_message(user_id, data)
except Exception as e:
await websocket.close(code=4002)

### Background Tasks

python
class TaskScheduler:
def init(self, db: Session, websocket_manager: WebSocketManager):
self.scheduler = AsyncIOScheduler()
def start(self):
self.scheduler.add_job(
self.update_pult_scores,
CronTrigger(hour='')
)
self.scheduler.start()


## Project Structure

    .
    ├── core/
    │   ├── auth/           # Twitter OAuth implementation
    │   ├── errors/         # Error handling and recovery
    │   ├── monitoring/     # Prometheus metrics
    │   ├── pult/          # Score processing
    │   ├── scheduler/      # Background tasks
    │   └── websocket/      # Real-time updates
    ├── models/             # SQLAlchemy models
    ├── services/           # Business logic
    ├── tests/             # Test suite
    └── scripts/           # Utility scripts

## Configuration

Required environment variables:

env
DATABASE_URL=postgresql://user:password@localhost:5432/pult
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=your_secret_key


## Monitoring

Prometheus metrics available at `/metrics`:
- Active WebSocket connections
- Request latency
- Background task status
- Error rates

## Testing

Run the test suite:

bash
pytest


Key test areas:
- WebSocket connections
- Background task scheduling
- Twitter OAuth flow
- Error recovery mechanisms

## Dependencies

- FastAPI
- SQLAlchemy
- APScheduler
- Prometheus Client
- Redis
- PostgreSQL

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Twitter API](https://developer.twitter.com/en/docs)