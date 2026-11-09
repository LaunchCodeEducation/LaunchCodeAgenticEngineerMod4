#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8002}"

echo "== Paragraph chunking =="
python3 mcp-servers/retrieval/server.py --port "$PORT" --chunking paragraph &
PID=$!
sleep 3
python3 mcp-servers/retrieval/run_ground_truth.py
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true

echo

echo "== Semantic chunking =="
python3 mcp-servers/retrieval/server.py --port "$PORT" --chunking semantic &
PID=$!
sleep 3
python3 mcp-servers/retrieval/run_ground_truth.py
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
