#!/usr/bin/env python3
"""PreToolUse hook: enforce the run-tests skill activation scope (Layer 3).

Policy (docs/governance-policy.md, per-role "Skill activation scope"):
- run-tests may be activated only by the tester (hook input agent_type "tester");
- the tester may activate no skill other than run-tests.
Every other role and skill combination is left to Claude Code's normal handling.

Unauthorized activations are denied with a PreToolUse "deny" decision and an
audit record written outside the repository. Input the hook cannot read is
denied (fail closed). The skill name is read from tool_input["skill"], the
parameter name of Claude Code's Skill tool.

This hook governs Skill tool calls only. It does not stop a role that holds
Bash from running the test command directly (governance policy D4, D5).
"""
import datetime
import json
import os
import sys
from pathlib import Path

GOVERNED_SKILL = "run-tests"
AUTHORIZED_AGENT = "tester"
POLICY_REFERENCE = "docs/governance-policy.md"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _normalize(value):
    """Return the bare skill name from a value such as '/project:run-tests --x'."""
    if not isinstance(value, str) or not value.strip():
        return None
    token = value.strip().split()[0].lstrip("/")
    return token.split(":")[-1] or None


def skill_name(tool_input):
    """Return the requested skill name, or None when it cannot be determined."""
    if not isinstance(tool_input, dict):
        return None
    return _normalize(tool_input.get("skill"))


def _mentions_governed_skill(value):
    if isinstance(value, str):
        return any(_normalize(part) == GOVERNED_SKILL for part in value.split())
    if isinstance(value, dict):
        return any(_mentions_governed_skill(item) for item in value.values())
    if isinstance(value, list):
        return any(_mentions_governed_skill(item) for item in value)
    return False


def decide(payload):
    """Return (decision, reason); decision is "deny", "authorize" or None (not governed)."""
    if payload.get("tool_name") != "Skill":
        return None, "not a Skill call"
    agent = payload.get("agent_type") or ""
    tool_input = payload.get("tool_input")
    name = skill_name(tool_input)
    if agent == AUTHORIZED_AGENT:
        if name == GOVERNED_SKILL:
            return "authorize", f"the tester may activate '{GOVERNED_SKILL}'"
        return "deny", (
            f"the tester may activate only '{GOVERNED_SKILL}' "
            f"(requested: {name or 'unknown'})"
        )
    if name == GOVERNED_SKILL or (name is None and _mentions_governed_skill(tool_input)):
        caller = agent or "main session (no agent_type)"
        return "deny", f"'{GOVERNED_SKILL}' may be activated only by the tester (caller: {caller})"
    return None, "skill not governed by this hook"


def _inside(path, root):
    return path == root or root in path.parents


def audit_log_path(env=None):
    """Return the audit log path, never inside the repository or project directory."""
    env = os.environ if env is None else env
    candidates = []
    if env.get("SKILL_AUDIT_LOG"):
        candidates.append(Path(env["SKILL_AUDIT_LOG"]))
    if Path("/logs").is_dir():
        candidates.append(Path("/logs/skill-audit-log.jsonl"))
    home = Path(env.get("HOME") or Path.home())
    candidates.append(home / ".local" / "state" / "marketradar" / "skill-audit-log.jsonl")
    roots = [REPO_ROOT]
    if env.get("CLAUDE_PROJECT_DIR"):
        roots.append(Path(env["CLAUDE_PROJECT_DIR"]).resolve())
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if not any(_inside(resolved, root) for root in roots):
            return resolved
    return None


def write_audit(record, env=None):
    path = audit_log_path(env)
    if path is None:
        print("enforce_skill_scope: no audit path outside the repository", file=sys.stderr)
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as log:
            log.write(json.dumps(record) + "\n")
    except OSError as error:
        print(f"enforce_skill_scope: audit write failed: {error}", file=sys.stderr)
        return None
    return path


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        decision, reason = decide(payload)
    else:
        payload = {}
        decision, reason = "deny", "unreadable hook input; failing closed"
    if decision is None:
        return 0
    denied = decision == "deny"
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": "skill_activation_denied" if denied else "skill_activation_authorized",
        "operation": "activate_skill",
        "skill": skill_name(payload.get("tool_input")) or "",
        "role": payload.get("agent_type") or "",
        "outcome": "denied" if denied else "authorized",
        "detail": reason,
        "policy_reference": POLICY_REFERENCE,
    }
    write_audit(record)
    if denied:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"skill_activation_denied: {reason}. See {POLICY_REFERENCE}."
                ),
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
