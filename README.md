# Rate Limiter Service

A rate-limiting service that throttles requests to an API endpoint
using a sliding-window algorithm backed by Redis.

## Motivation
Uncontrolled request bursts can overwhelm backend services. This
project implements a configurable rate limiter as a standalone
middleware/service to demonstrate request throttling patterns used
in scalable web infrastructure.

## Planned architecture
- **Algorithm:** sliding-window rate limiting, using Redis for
  distributed request counting
- **Service:** FastAPI middleware wrapping a demo endpoint, with
  configurable request/time-window limits
- **Containerization:** Docker Compose setup running the app and
  Redis together for local multi-container testing

## Status
🚧 In active development. Core limiting logic and Redis integration
in progress.

## Stack
Python, FastAPI, Redis, Docker
