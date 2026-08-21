#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed or is not available on PATH." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running or the current user cannot access it." >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
fi

echo "Starting FinAgent Platform and waiting for service health checks..."
docker compose up -d --build --wait
docker compose exec -T api python -c \
  "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10).status == 200"
docker compose exec -T web wget -qO- http://127.0.0.1/ >/dev/null

echo "FinAgent Platform is healthy."
docker compose ps
