from fastapi import FastAPI

from app.config import settings
from app.middleware import RateLimitMiddleware
from app.rate_limiter import rate_limiter

app = FastAPI(
    title="Rate Limiter Service",
    description="Demo API protected by a Redis-backed sliding-window rate limiter.",
)

app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def demo_endpoint():
    """The endpoint being protected. Every hit counts against the caller's limit."""
    return {
        "message": "Request succeeded!",
        "limit": settings.rate_limit_requests,
        "window_seconds": settings.rate_limit_window_seconds,
    }


@app.get("/health")
async def health():
    """Not rate limited - see middleware.py."""
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await rate_limiter.close()
