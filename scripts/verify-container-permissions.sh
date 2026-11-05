#!/usr/bin/env bash
# verify-container-permissions.sh: check that scripts/run-agent.sh launches
# every governed role with only the container permissions the governance
# policy allows (Module 4.1 Enforcement Layer 1).
#
# Run on the Docker host (e.g. your Mac), not inside the agent container.
# A passing run covers only containers started by run-agent.sh; it says
# nothing about subagents started through the Claude Code Agent tool, which
# run inside the orchestrator's container.
#
# Usage: bash scripts/verify-container-permissions.sh
#
# Every container is started through run-agent.sh. This script never mounts
# the Docker socket and never calls `docker run` directly.
# Compatible with macOS bash 3.2.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$REPO_ROOT/scripts/run-agent.sh"
IMAGE="${AGENT_IMAGE:-agentic_engineer_4}"
TOKEN="perm-probe-$$-$(date +%s)"
PASSED=0
FAILED=0
TMP1=""
TMP2=""

cleanup() {
  [ -n "$TMP1" ] && rm -f "$TMP1"
  [ -n "$TMP2" ] && rm -f "$TMP2"
  for d in "$REPO_ROOT" "$REPO_ROOT/logs" "$REPO_ROOT/.memory/knowledge" "$REPO_ROOT/.memory/reference"; do
    rm -f "$d/.$TOKEN"
  done
}
trap cleanup EXIT

pass() { echo "PASS: $1"; PASSED=$((PASSED + 1)); }
fail() { echo "FAIL: $1 (expected $2, got $3)"; FAILED=$((FAILED + 1)); }
check() { if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "$2" "$3"; fi; }

# --- Preflight -------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "docker CLI not found on PATH" >&2; exit 2
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running" >&2; exit 2
fi
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Image not found: $IMAGE; build it with: docker build -t agentic_engineer_4 ." >&2; exit 2
fi

# --- Static checks on run-agent.sh -----------------------------------------
# `mkdir -p` is not a port flag, so mkdir lines are excluded from the -p check.
static_absent() {
  if [ "$2" = "0" ]; then pass "run-agent.sh has no $1"; else fail "run-agent.sh has no $1" "0 matches" "$2 matches"; fi
}
static_absent "published ports (-p / --publish)" \
  "$(grep -v '^[[:space:]]*mkdir ' "$RUN" | grep -Ec -- '(^|[[:space:](])-p([[:space:]]|$)|--publish')"
static_absent "docker.sock mount" "$(grep -c 'docker.sock' "$RUN")"
static_absent "SLACK_ variables" "$(grep -c 'SLACK_' "$RUN")"
static_absent "ANTHROPIC_API_KEY" "$(grep -c 'ANTHROPIC_API_KEY' "$RUN")"
n=$(grep -c 'REPO_ROOT}/logs' "$RUN")
if [ "$n" = "0" ]; then
  pass "run-agent.sh does not bind-mount repo logs/"
else
  fail "run-agent.sh does not bind-mount repo logs/" "0 matches" "$n matches"
fi

# --- Probe (runs inside each container; token arrives as $1) ---------------
PROBE='
T="$1"
mopt() { awk -v m="$1" "BEGIN{r=\"none\"} \$2==m {split(\$4,a,\",\"); r=a[1]} END{print r}" /proc/mounts; }
wr() { if [ -d "$1" ] && ( : > "$1/.$T" ) 2>/dev/null; then rm -f "$1/.$T"; echo yes; else echo no; fi; }
echo "role=${AGENT_ROLE:-}"
echo "ws_mount=$(mopt /workspace)"
echo "kn_mount=$(mopt /workspace/.memory/knowledge)"
echo "ref_mount=$(mopt /workspace/.memory/reference)"
echo "ws_write=$(wr /workspace)"
echo "kn_write=$(wr /workspace/.memory/knowledge)"
echo "ref_write=$(wr /workspace/.memory/reference)"
echo "logs_write=$(wr /logs)"
if ( : > "/logs/.$T" ) 2>/dev/null; then
  if [ -e "/workspace/logs/.$T" ]; then echo "logs_in_repo=yes"; else echo "logs_in_repo=no"; fi
  rm -f "/logs/.$T"
else
  echo "logs_in_repo=unknown"
fi
if awk "\$2==\"/memory\" {f=1} END{exit !f}" /proc/mounts; then
  echo "mem_mounted=yes"; echo "mem_write=$(wr /memory)"
else
  echo "mem_mounted=no"; echo "mem_write=no"
fi
n=$(env | grep -c "^SLACK_"); echo "slack_vars=${n:-0}"
n=0
for d in /workspace /workspace/.memory/knowledge /workspace/.memory/reference /logs /memory; do
  [ -e "$d/.$T" ] && n=$((n + 1))
done
echo "leftover=$n"
'

# Value of KEY from the last "KEY=value" line in $OUT.
val() { printf '%s\n' "$OUT" | grep "^$1=" | tail -n 1 | sed "s/^$1=//"; }

# Sets E_ROLE, E_WS, E_WSW, E_MEM, E_MEMW for a launch name.
expect() {
  case "$1" in
    planner|tester|project-manager)
      E_ROLE="$1"; E_WS=ro; E_WSW=no; E_MEM=no; E_MEMW=no ;;
    marketradar-code-reviewer|reviewer)
      E_ROLE=reviewer; E_WS=ro; E_WSW=no; E_MEM=no; E_MEMW=no ;;
    implementer|orchestrator)
      E_ROLE="$1"; E_WS=rw; E_WSW=yes; E_MEM=yes; E_MEMW=yes ;;
  esac
}

for launch in planner implementer tester marketradar-code-reviewer reviewer project-manager orchestrator; do
  expect "$launch"
  OUT=$(bash "$RUN" "$launch" bash -c "$PROBE" probe "$TOKEN" </dev/null 2>&1)
  rc=$?
  check "$launch: wrapper exit code" 0 "$rc"
  banner=$(printf '%s\n' "$OUT" | grep '^Launching' | head -n 1)
  case "$banner" in
    *"(AGENT_ROLE=${E_ROLE})"*) pass "$launch: banner shows AGENT_ROLE=$E_ROLE" ;;
    *) fail "$launch: banner shows AGENT_ROLE=$E_ROLE" "AGENT_ROLE=$E_ROLE" "'$banner'" ;;
  esac
  pairs="role=$E_ROLE ws_mount=$E_WS ws_write=$E_WSW kn_mount=ro ref_mount=ro kn_write=no ref_write=no"
  pairs="$pairs logs_write=yes logs_in_repo=no mem_mounted=$E_MEM mem_write=$E_MEMW slack_vars=0 leftover=0"
  for p in $pairs; do
    k="${p%%=*}"; e="${p#*=}"
    check "$launch: $k" "$e" "$(val "$k")"
  done
done

# --- Negative tests: roles without a policy entry must not launch ----------
for bad in code-reviewer "foo-$TOKEN"; do
  OUT=$(bash "$RUN" "$bad" true </dev/null 2>&1)
  rc=$?
  if printf '%s\n' "$OUT" | grep -q 'Launching'; then banner=yes; else banner=no; fi
  if [ "$rc" -ne 0 ] && [ "$banner" = no ]; then
    pass "$bad: rejected"
  else
    fail "$bad: rejected" "non-zero exit and no banner" "exit $rc, banner=$banner"
  fi
done

# --- Concurrency: two read-write roles at once (no host port clash) --------
TMP1=$(mktemp "${TMPDIR:-/tmp}/perm-probe.XXXXXX")
TMP2=$(mktemp "${TMPDIR:-/tmp}/perm-probe.XXXXXX")
bash "$RUN" orchestrator bash -c 'sleep 5' </dev/null >"$TMP1" 2>&1 &
P1=$!
bash "$RUN" implementer bash -c 'sleep 5' </dev/null >"$TMP2" 2>&1 &
P2=$!
wait "$P1"; R1=$?
wait "$P2"; R2=$?
check "concurrent orchestrator exit code" 0 "$R1"
check "concurrent implementer exit code" 0 "$R2"
[ "$R1" -ne 0 ] && sed 's/^/  orchestrator: /' "$TMP1"
[ "$R2" -ne 0 ] && sed 's/^/  implementer: /' "$TMP2"

# --- Host-side leftover scan ------------------------------------------------
for d in "$REPO_ROOT" "$REPO_ROOT/logs" "$REPO_ROOT/.memory/knowledge" "$REPO_ROOT/.memory/reference"; do
  if [ -e "$d/.$TOKEN" ]; then
    fail "no probe file left in $d" "absent" "present"
  else
    pass "no probe file left in $d"
  fi
done

echo "Summary: $PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ] || exit 1
exit 0
