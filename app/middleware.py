"""
Thin ASGI middleware that wraps every incoming request with a rate-limit
check. Kept deliberately small: all the actual logic lives in
RateLimiter (app/rate_limiter.py) so this file just wires it in.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.rate_limiter import rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for the health check so monitoring never gets throttled.
        if request.url.path == "/health":
            return await call_next(request)

        # Identify the client. In production behind a proxy you'd read
        # X-Forwarded-For instead; keeping it simple here.
        client_key = request.client.host if request.client else "unknown"

        allowed, remaining = await rate_limiter.is_allowed(client_key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(rate_limiter.window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
