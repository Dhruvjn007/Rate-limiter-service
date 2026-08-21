"""
All configuration lives here so the rest of the app never reads
environment variables directly. Everything has a sane default,
so `docker compose up` works with zero setup.
"""

import os


class Settings:
    # Where Redis lives. Inside Docker Compose this is "redis://redis:6379/0".
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Rate limit: N requests per WINDOW seconds, per client (identified by IP).
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "10"))


settings = Settings()
