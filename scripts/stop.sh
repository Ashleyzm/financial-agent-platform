#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed or is not available on PATH." >&2
  exit 1
fi

docker compose down --remove-orphans
echo "FinAgent Platform stopped. Named data volumes were preserved."
