from functools import wraps
import asyncio
from typing import Callable
from core.logger import log_error

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.is_open = False
        self.last_failure_time = None

    async def __call__(self, func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.is_open:
                raise Exception("Circuit breaker is open")
                
            try:
                result = await func(*args, **kwargs)
                self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.is_open = True
                    asyncio.create_task(self.reset_after_timeout())
                raise e
                
        return wrapper
        
    async def reset_after_timeout(self):
        await asyncio.sleep(self.reset_timeout)
        self.is_open = False
        self.failure_count = 0

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    if retry_count == retries:
                        raise e
                    wait_time = (backoff_in_seconds * 2 ** retry_count)
                    log_error(e, f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator 