# Rate Limiter Service

A small FastAPI service that throttles requests using a **sliding-window**
rate-limiting algorithm, backed by Redis. Built to demonstrate the request
throttling patterns used in real API infrastructure.

## How the algorithm works

Each client (identified here by IP address) gets a Redis **sorted set**.
Every request is stored as an entry with the request's timestamp as its
score. To decide whether a new request is allowed:

1. **Trim** — delete every entry older than `now - window_seconds`.
2. **Count** — how many entries are left?
3. **Decide** — if count is under the limit, allow the request and add a
   new entry; otherwise reject it with `429 Too Many Requests`.

This is a *sliding* window (as opposed to a *fixed* window like "5
requests per clock-minute") because the window boundary moves with every
request instead of resetting on a fixed schedule. That avoids the classic
fixed-window problem where a burst at 0:59 and another at 1:01 can both
sneak through even though they're only 2 seconds apart.

All three steps run in a single Redis pipeline, so the check-and-increment
is effectively atomic — two requests arriving at the exact same instant
can't both slip through when only one slot is free.

See `app/rate_limiter.py` for the implementation, it's ~50 lines and
heavily commented.

## Project layout

```
app/
  config.py       # settings, all read from environment variables
  rate_limiter.py # the sliding-window algorithm itself
  middleware.py    # FastAPI middleware that calls the limiter on every request
  main.py          # FastAPI app + demo endpoint
Dockerfile
docker-compose.yml # runs the app + Redis together
scripts/demo.sh    # fires a burst of requests so you can see it throttle
```

## Running it

### With Docker Compose (recommended)

```bash
docker compose up --build
```

The API is now at `http://localhost:8000`. Try it:

```bash
curl http://localhost:8000/
```

Or run the demo script to watch the limiter reject requests once you go
over the limit:

```bash
./scripts/demo.sh
```

### Locally, without Docker

You'll need a Redis instance running (`redis-server` or `docker run -p 6379:6379 redis:7-alpine`).

```bash
pip install -r requirements.txt
cp .env.example .env   # optional, defaults already work
uvicorn app.main:app --reload
```

## Configuration

Set via environment variables (see `.env.example`):

| Variable                    | Default | Meaning                                |
|------------------------------|---------|-----------------------------------------|
| `REDIS_URL`                  | `redis://localhost:6379/0` | Where Redis lives |
| `RATE_LIMIT_REQUESTS`        | `5`     | Max requests allowed per window          |
| `RATE_LIMIT_WINDOW_SECONDS`  | `10`    | Length of the sliding window, in seconds |

## Endpoints

- `GET /` — demo endpoint, protected by the rate limiter.
- `GET /health` — health check, **not** rate limited.

Every response from a rate-limited endpoint includes:

- `X-RateLimit-Limit` — the configured max requests per window
- `X-RateLimit-Remaining` — requests left in the current window

A rejected request (`429`) also includes `Retry-After` (seconds until
you should try again).

## Status

🚧 Core sliding-window logic and Redis integration are implemented and
working. Possible next steps: per-route limits (instead of one global
limit), API-key-based identification instead of IP, and a Lua script to
make the pipeline fully atomic under heavier concurrency.

## Stack

Python, FastAPI, Redis, Docker
