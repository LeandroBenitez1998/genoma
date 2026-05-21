#!/bin/bash
set -e

cd /Users/leandrothomas/Desktop/Projects/genoma

# Install deps once (silent)
echo "Installing dependencies..."
python3 -m pip install fastapi uvicorn pydantic python-dotenv --break-system-packages -q 2>/dev/null || true
pnpm install --ignore-scripts -q 2>/dev/null || true

echo "Starting backend on :8000..."
python3 -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting MCP server (stdio)..."
python3 -m backend.mcp_server &
MCP_PID=$!

echo "Starting frontend on :3000..."
sleep 2

# Kill backend + MCP if script exits
trap "kill $BACKEND_PID $MCP_PID 2>/dev/null || true" EXIT

# Run frontend (foreground — Ctrl+C kills both)
pnpm dev
