#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BACKEND_PYTHON="$ROOT_DIR/backend/venv/bin/python"

if [ ! -x "$BACKEND_PYTHON" ]; then
  echo "Backend virtualenv is missing: $BACKEND_PYTHON" >&2
  echo "Create it with: python3 -m venv backend/venv" >&2
  exit 1
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "Frontend dependencies are missing. Run: npm --prefix frontend install" >&2
  exit 1
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Backend port 8000 is already in use. Stop the existing backend first." >&2
  exit 1
fi

if lsof -nP -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Frontend port 5173 is already in use. Stop the existing frontend first." >&2
  exit 1
fi

cleanup() {
  trap - INT TERM EXIT
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

"$BACKEND_PYTHON" -m uvicorn main:app \
  --app-dir "$ROOT_DIR/backend" \
  --host 127.0.0.1 \
  --port 8000 &
BACKEND_PID=$!

npm --prefix "$ROOT_DIR/frontend" run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!

echo "Frontend: http://127.0.0.1:5173/"
echo "Backend:  http://127.0.0.1:8000/"
echo "Press Ctrl+C to stop both servers."

wait "$BACKEND_PID" "$FRONTEND_PID"
