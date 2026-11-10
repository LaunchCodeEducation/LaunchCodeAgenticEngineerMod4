#!/usr/bin/env python3
"""PreToolUse hook: restrict the dependency-auditor's Bash commands.

Policy (docs/governance-policy.md, "Role: dependency-auditor", Agent tool
grants): the dependency-auditor may run only `npm audit --json` and
`npm outdated --json` with `--prefix tracker-api` or `--prefix tracker-client`.
Every other Bash command from that role is denied and audited outside the
repository. Bash calls from other roles are not governed by this hook.

The command is read from tool_input["command"], the parameter name of Claude
Code's Bash tool, and compared as a whole after whitespace is collapsed, so
any extra token (a second command, redirection, another flag) is denied.
Input the hook cannot read is denied (fail closed).
"""
import datetime
import importlib.util
import json
import sys
from pathlib import Path

# The hook runs inside the repository; never write bytecode caches there.
sys.dont_write_bytecode = True

GOVERNED_AGENT = "dependency-auditor"
POLICY_REFERENCE = "docs/governance-policy.md"
AUDIT_ENV_VAR = "BASH_AUDIT_LOG"
AUDIT_FILENAME = "bash-audit-log.jsonl"

ALLOWED_COMMANDS = {
    form.format(command=command, prefix=prefix)
    for command in ("audit", "outdated")
    for prefix in ("tracker-api", "tracker-client")
    for form in ("npm {command} --json --prefix {prefix}", "npm --prefix {prefix} {command} --json")
}

_spec = importlib.util.spec_from_file_location(
    "enforce_skill_scope", Path(__file__).resolve().with_name("enforce_skill_scope.py")
)
_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_audit)


def command_of(tool_input):
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def decide(payload):
    """Return (decision, reason); decision is "deny", "authorize" or None (not governed)."""
    if payload.get("tool_name") != "Bash":
        return None, "not a Bash call"
    if (payload.get("agent_type") or "") != GOVERNED_AGENT:
        return None, "role not governed by this hook"
    command = command_of(payload.get("tool_input"))
    if command is None:
        return "deny", "unreadable Bash command; failing closed"
    normalized = " ".join(command.split())
    if normalized in ALLOWED_COMMANDS:
        return "authorize", f"approved audit command: {normalized}"
    return "deny", (
        "dependency-auditor may run only `npm audit --json` or `npm outdated --json` "
        f"with --prefix tracker-api or tracker-client (requested: {normalized[:200]})"
    )


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
    command = command_of(payload.get("tool_input")) or ""
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": "bash_command_denied" if denied else "bash_command_authorized",
        "operation": "run_bash",
        "command": " ".join(command.split())[:500],
        "role": payload.get("agent_type") or "",
        "outcome": "denied" if denied else "authorized",
        "detail": reason,
        "policy_reference": POLICY_REFERENCE,
    }
    _audit.write_audit(record, env_var=AUDIT_ENV_VAR, filename=AUDIT_FILENAME)
    if denied:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"bash_command_denied: {reason}. See {POLICY_REFERENCE}.",
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
