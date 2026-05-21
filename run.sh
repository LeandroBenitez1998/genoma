#!/bin/bash
set -e

cd /Users/leandrothomas/Desktop/Projects/genoma

# ── Load env ──
if [ -f .env.local ]; then
  set -a
  source .env.local
  set +a
fi

# ── Python venv ──
PYTHON="./venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
  python3 -m venv venv
  ./venv/bin/pip install -q -r backend/requirements.txt openai 2>/dev/null || true
fi

# Install Node deps once (silent)
pnpm install --ignore-scripts -q 2>/dev/null || true

echo "Starting backend on 8000..."
$PYTHON -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting MCP server (stdio)..."
$PYTHON -m backend.mcp_server &
MCP_PID=$!

echo "Starting frontend on 3000..."
sleep 2

trap "kill $BACKEND_PID $MCP_PID 2>/dev/null || true" EXIT

pnpm dev
