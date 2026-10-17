#!/usr/bin/env bash
# P8-02: run the backend inside a GitHub Codespace and make port 8000 public, so the Vercel frontend
# can call it (a private port redirects to GitHub sign-in, which breaks CORS preflight).
# Usage (Codespace terminal, repo root): bash scripts/run_codespace.sh   (Ctrl+C stops the server)
set -euo pipefail
: "${CODESPACE_NAME:?run this inside a GitHub Codespace}"
cd "$(dirname "$0")/.."
PORT=8000

python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null' INT TERM

for _ in $(seq 60); do
  curl -fs "http://127.0.0.1:$PORT/api/health" >/dev/null && break
  sleep 1
done

URL="https://$CODESPACE_NAME-$PORT.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
if gh codespace ports visibility "$PORT:public" -c "$CODESPACE_NAME"; then
  echo "Public API: $URL   (check: curl -s $URL/api/health)"
else
  echo "Could not make port $PORT public. Ports tab -> right-click $PORT -> Port Visibility -> Public." >&2
fi

wait "$SERVER"
