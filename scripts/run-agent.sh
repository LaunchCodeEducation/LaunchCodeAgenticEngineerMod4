#!/usr/bin/env bash
# run-agent.sh: launch a subagent container with only the permissions its
# governance policy allows. Pass the role name as the first argument.
set -euo pipefail

ROLE="${1:?Usage: run-agent.sh <role-name> [command]}"
shift

IMAGE="${AGENT_IMAGE:-agentic_engineer_4}"
WORKSPACE_MODE="ro"
MOUNT_MEMORY=0

case "$ROLE" in
  implementer|orchestrator)
    WORKSPACE_MODE="rw"
    MOUNT_MEMORY=1
    ;;
  planner|reviewer|tester|project-manager|dependency-auditor)
    WORKSPACE_MODE="ro"
    MOUNT_MEMORY=0
    ;;
  *)
    echo "Unknown role: $ROLE" >&2
    echo "This role has no policy entry, so it cannot be launched." >&2
    exit 1
    ;;
esac

ARGS=( run --rm -it )

# Expose local application ports.
ARGS+=( -p 8501:8501 )
ARGS+=( -p 8502:8502 )

# Slack configuration.
# These may be set in your shell before running this script.
ARGS+=( -e "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-xoxb-your-token}" )
ARGS+=( -e "SLACK_TEAM_ID=${SLACK_TEAM_ID:-T0123456}" )

# Workspace and logs.
mkdir -p logs
ARGS+=( -v "$(pwd):/workspace:${WORKSPACE_MODE}" )
ARGS+=( -v "$(pwd)/logs:/logs:rw" )

# Audit log locations.
ARGS+=( -e "STORAGE_AUDIT_LOG=/logs/storage-audit-log.jsonl" )
ARGS+=( -e "RETRIEVAL_AUDIT_LOG=/logs/retrieval-audit-log.jsonl" )

# Mount persistent memory only for roles allowed by policy.
if [ "$MOUNT_MEMORY" -eq 1 ]; then
  ARGS+=( -v agent-memory:/memory )
fi

# Role identity.
ARGS+=( -e "AGENT_ROLE=${ROLE}" )

# Image and optional command.
ARGS+=( "$IMAGE" "$@" )

MEMORY_STATE=$([ "$MOUNT_MEMORY" -eq 1 ] && echo mounted || echo omitted)
echo "Launching '$ROLE': image=${IMAGE}, workspace=${WORKSPACE_MODE}, memory=${MEMORY_STATE}"
exec docker "${ARGS[@]}"