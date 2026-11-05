#!/usr/bin/env bash
# run-agent.sh: launch a subagent container with only the permissions its
# governance policy allows. Pass the role name as the first argument.
# Module 4.1 Enforcement Layer 1: container-level permissions.
set -euo pipefail

LAUNCH_NAME="${1:?Usage: run-agent.sh <role-name> [command]}"
shift

# Resolve the repository root from this script's location, not the caller's cwd.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

IMAGE="${AGENT_IMAGE:-agentic_engineer_4}"
WORKSPACE_MODE="ro"
MOUNT_MEMORY=0

case "$LAUNCH_NAME" in
  implementer|orchestrator)
    AGENT_ROLE="$LAUNCH_NAME"
    WORKSPACE_MODE="rw"
    MOUNT_MEMORY=1
    ;;
  planner|tester|project-manager)
    AGENT_ROLE="$LAUNCH_NAME"
    WORKSPACE_MODE="ro"
    MOUNT_MEMORY=0
    ;;
  marketradar-code-reviewer|reviewer)
    # Allow-lists are keyed on "reviewer"; renaming them is Layer 2.
    AGENT_ROLE="reviewer"
    WORKSPACE_MODE="ro"
    MOUNT_MEMORY=0
    ;;
  *)
    echo "Unknown role: $LAUNCH_NAME" >&2
    echo "This role has no policy entry, so it cannot be launched." >&2
    exit 1
    ;;
esac

ARGS=( run --rm )

# Allocate a TTY only when both stdin and stdout are terminals.
if [ -t 0 ] && [ -t 1 ]; then
  ARGS+=( -it )
else
  ARGS+=( -i )
fi

# No published ports and no Slack credentials: the policy grants neither
# to any role.

# Workspace. Logs use a named volume outside the repository so that
# read-only roles cannot write repository files through /logs.
ARGS+=( -v "${REPO_ROOT}:/workspace:${WORKSPACE_MODE}" )
ARGS+=( -v agent-logs:/logs )

# Knowledge and reference memory are read-only for every role, including
# roles with a read-write workspace.
ARGS+=( -v "${REPO_ROOT}/.memory/knowledge:/workspace/.memory/knowledge:ro" )
ARGS+=( -v "${REPO_ROOT}/.memory/reference:/workspace/.memory/reference:ro" )

# Audit log locations.
ARGS+=( -e "STORAGE_AUDIT_LOG=/logs/storage-audit-log.jsonl" )
ARGS+=( -e "RETRIEVAL_AUDIT_LOG=/logs/retrieval-audit-log.jsonl" )

# Mount persistent memory only for roles allowed by policy.
if [ "$MOUNT_MEMORY" -eq 1 ]; then
  ARGS+=( -v agent-memory:/memory )
fi

# Role identity.
ARGS+=( -e "AGENT_ROLE=${AGENT_ROLE}" )

# Image and optional command.
ARGS+=( "$IMAGE" "$@" )

MEMORY_STATE=$([ "$MOUNT_MEMORY" -eq 1 ] && echo mounted || echo omitted)
echo "Launching '${LAUNCH_NAME}' (AGENT_ROLE=${AGENT_ROLE}): image=${IMAGE}, workspace=${WORKSPACE_MODE}, knowledge/reference=ro, memory=${MEMORY_STATE}"
exec docker "${ARGS[@]}"
