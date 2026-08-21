"""
Sliding-window rate limiter, backed by Redis.

How it works (the "sliding window log" algorithm):

  For every client, we keep a Redis *sorted set* where:
    - the "member" is a unique id for one request
    - the "score" is the timestamp (in milliseconds) that request arrived

  To check "is this new request allowed?" we:
    1. Drop every entry older than (now - window_seconds)      -> ZREMRANGEBYSCORE
    2. Count what's left in the set                            -> ZCARD
    3. If count < limit: add this request and allow it         -> ZADD
       else: reject it

  This is called a "sliding window log" because the window slides
  continuously with time, rather than resetting on a fixed clock tick
  (like "every request in the current minute"). That avoids the classic
  fixed-window bug where two bursts on either side of a window boundary
  can slip through together.

  Steps 1-3 are sent to Redis as a single pipeline so they run as one
  atomic round trip - two clients hitting the limiter at the same time
  can't both "see" a free slot that only exists once.
"""

import time
import uuid

import redis.asyncio as redis

from app.config import settings


class RateLimiter:
    def __init__(self, redis_url: str, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check whether a request from `key` (e.g. a client IP) is allowed
        right now. Returns (allowed, remaining_requests_in_window).
        """
        now_ms = time.time() * 1000
        window_start_ms = now_ms - self.window_seconds * 1000
        redis_key = f"rate_limit:{key}"

        pipe = self._redis.pipeline()
        # 1. Forget requests that fell outside the window.
        pipe.zremrangebyscore(redis_key, 0, window_start_ms)
        # 2. How many requests are still inside the window?
        pipe.zcard(redis_key)
        _, current_count = await pipe.execute()

        if current_count >= self.limit:
            return False, 0

        # 3. Record this request and make sure the key expires on its own
        #    (no reason to keep it around once the window has fully passed).
        request_id = str(uuid.uuid4())
        pipe = self._redis.pipeline()
        pipe.zadd(redis_key, {request_id: now_ms})
        pipe.expire(redis_key, self.window_seconds)
        await pipe.execute()

        remaining = self.limit - current_count - 1
        return True, remaining

    async def close(self):
        await self._redis.close()


# One shared instance, configured from environment variables.
rate_limiter = RateLimiter(
    redis_url=settings.redis_url,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
