#!/usr/bin/env bash
# Fires 8 quick requests at the demo endpoint so you can watch the
# rate limiter kick in (default config allows 5 requests / 10s).
#
# Usage: ./scripts/demo.sh

URL="http://localhost:8000/"

for i in $(seq 1 8); do
  echo "Request $i:"
  curl -s -o /dev/null -w "  status=%{http_code}\n" "$URL"
done
