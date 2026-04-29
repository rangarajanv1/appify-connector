#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec uv run uvicorn appify_connector.main:app --reload --reload-include='.env' --host 0.0.0.0 --port 8080
