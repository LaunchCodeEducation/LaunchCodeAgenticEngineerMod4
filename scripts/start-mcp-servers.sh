#!/usr/bin/env bash
set -euo pipefail

STORAGE_PORT="${STORAGE_PORT:-8001}"
RETRIEVAL_PORT="${RETRIEVAL_PORT:-8002}"
CHUNKING="${CHUNKING:-paragraph}"
BOUNDARY_THRESHOLD="${BOUNDARY_THRESHOLD:-0.75}"

mkdir -p /memory /memory/reference

python3 mcp-servers/storage/server.py --port "$STORAGE_PORT" &
STORAGE_PID=$!

python3 mcp-servers/retrieval/server.py \
  --port "$RETRIEVAL_PORT" \
  --chunking "$CHUNKING" \
  --boundary-threshold "$BOUNDARY_THRESHOLD" &
RETRIEVAL_PID=$!

cleanup() {
  kill "$STORAGE_PID" "$RETRIEVAL_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Storage MCP server PID:   $STORAGE_PID  http://127.0.0.1:${STORAGE_PORT}/mcp"
echo "Retrieval MCP server PID: $RETRIEVAL_PID  http://127.0.0.1:${RETRIEVAL_PORT}/mcp"
echo "Press Ctrl-C to stop both servers."
wait
