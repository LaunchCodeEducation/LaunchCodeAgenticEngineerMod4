#!/bin/bash
set -e

# --- Claude login persistence (from Module 3) ---
# Mount a named volume at /claude-auth (-v claude-auth:/claude-auth) to keep the
# Claude Code login across container runs.
AUTH_DIR=/claude-auth
mkdir -p "$AUTH_DIR" /root/.claude

# A persisted credential means this is NOT the first run: restore it and mark
# onboarding complete so Claude skips the first-run flow (theme, login, trust).
if [ -f "$AUTH_DIR/.credentials.json" ]; then
  cp "$AUTH_DIR/.credentials.json" /root/.claude/.credentials.json
  chmod 600 /root/.claude/.credentials.json
  echo '{ "hasCompletedOnboarding": true, "projects": { "/workspace": { "hasTrustDialogAccepted": true } } }' > /root/.claude.json
fi

# --- Register MCP servers via Claude Code CLI (Module 4) ---
# Defaults keep startup working when Slack credentials are not supplied.
claude mcp add slack \
  node /usr/local/lib/node_modules/@modelcontextprotocol/server-slack/dist/index.js \
  -e SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-}" \
  -e SLACK_TEAM_ID="${SLACK_TEAM_ID:-}"

claude mcp add gmail \
  node /usr/local/lib/node_modules/@gongrzhe/server-gmail-autoauth-mcp/build/index.js

# Save the credential whenever it changes, so login survives any exit.
( set +e
  while true; do
    if [ -f /root/.claude/.credentials.json ] && \
       { [ ! -f "$AUTH_DIR/.credentials.json" ] || \
         [ /root/.claude/.credentials.json -nt "$AUTH_DIR/.credentials.json" ]; }; then
      tmp=$(mktemp "$AUTH_DIR/.credentials.json.tmp.XXXXXX")
      cp /root/.claude/.credentials.json "$tmp"
      chmod 600 "$tmp"
      mv -f "$tmp" "$AUTH_DIR/.credentials.json"
    fi
    sleep 5
  done ) &

# exec so the command runs as PID 1 (correct signal handling / reaping).
exec "$@"
