from redis import Redis
import json
from datetime import timedelta
import os

class RedisCache:
    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        
    async def get(self, key: str):
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
        
    async def set(self, key: str, value: any, expire_minutes: int = 30):
        """Set value in cache"""
        self.redis.setex(
            key,
            timedelta(minutes=expire_minutes),
            json.dumps(value)
        )
        
    async def delete(self, key: str):
        """Delete value from cache"""
        self.redis.delete(key) 