from pathlib import Path
import re


ROOT = Path(".")


def test_governance_policy_exists():
    assert (ROOT / "docs" / "governance-policy.md").exists(), (
        "Missing docs/governance-policy.md"
    )


def test_ci_step_design_exists():
    assert (ROOT / "docs" / "ci-step-design.md").exists(), (
        "Missing docs/ci-step-design.md"
    )


def test_workflow_exists_at_repo_root():
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists(), (
        "Workflow must live at .github/workflows/ci.yml"
    )


def test_workflow_does_not_hardcode_anthropic_key():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    forbidden_patterns = [
        r"sk-ant-[A-Za-z0-9_\-]+",
        r"ANTHROPIC_API_KEY\s*=\s*sk-",
    ]

    for pattern in forbidden_patterns:
        assert not re.search(pattern, workflow), (
            "Do not hardcode Anthropic keys in the workflow. "
            "Use ${{ secrets.ANTHROPIC_API_KEY }}."
        )


def test_policy_gate_is_not_continue_on_error():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    policy_section_start = workflow.find("policy-gate:")
    assert policy_section_start != -1, "Missing policy-gate job"

    next_job_start = workflow.find("\n  governed-file-gate:", policy_section_start)
    section = workflow[policy_section_start:next_job_start]

    assert "continue-on-error: true" not in section, (
        "policy-gate must remain a real gate, not advisory."
    )


# ---------------------------------------------------------------------------
# Module 4.1 Enforcement Layer 2: MCP server allow-lists.
#
# The expected matrix below is hard-coded from the per-role "MCP server and
# operation access" tables in docs/governance-policy.md. It is deliberately
# not parsed from the policy: changing a grant requires changing the policy,
# the allow-list and this matrix together.
#
# Each test loads a fresh copy of the server module with AGENT_ROLE and all
# file paths pointed at pytest's tmp_path, then calls the tools through an
# in-memory fastmcp Client. Nothing is written inside the repository.
# ---------------------------------------------------------------------------

import asyncio
import importlib.util
import json
import sys
import uuid

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError


SERVERS_DIR = Path(__file__).resolve().parent.parent / "mcp-servers"

RUNTIME_ROLES = [
    "planner",
    "implementer",
    "tester",
    "reviewer",
    "project-manager",
    "orchestrator",
]

STORAGE_OPS = [
    "write_entry",
    "read_entry",
    "list_entries",
    "update_entry",
    "delete_entry",
    "audit_read",
]

EXPECTED_STORAGE_GRANTS = {
    "planner": set(),
    "implementer": {"write_entry"},
    "tester": set(),
    "reviewer": set(),
    "project-manager": {"write_entry"},
    "orchestrator": {"read_entry", "list_entries", "audit_read"},
}

# None means retrieval is denied.
EXPECTED_RETRIEVE_CEILING = {
    "planner": "internal",
    "implementer": "internal",
    "tester": "internal",
    "reviewer": "internal",
    "project-manager": None,
    "orchestrator": None,
}

# Agent-definition names and self-declared calling_role values that are not
# runtime roles. None of them may be authorized.
NON_RUNTIME_NAMES = ["marketradar-code-reviewer", "code-reviewer", "project_manager", ""]

STORAGE_ARGS = {
    "write_entry": {"key": "k", "value": "v"},
    "read_entry": {"key": "k"},
    "list_entries": {},
    "update_entry": {"key": "k", "value": "v"},
    "delete_entry": {"key": "k"},
    "audit_read": {},
}

# Existing success events written by mcp-servers/storage/server.py.
# audit_read writes no audit record on success.
STORAGE_SUCCESS_EVENT = {
    "write_entry": "storage_write",
    "read_entry": "storage_read",
    "list_entries": "storage_list",
    "update_entry": "storage_update",
    "delete_entry": "storage_delete",
    "audit_read": None,
}

# Matches all three corpus documents (public, internal, confidential).
CLASSIFICATION_QUERY = "public internal confidential"


def _name_id(name):
    return name or "<empty>"


def _load_server(server, role, monkeypatch, tmp_path, set_store=True):
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setenv("AGENT_ROLE", role)
    monkeypatch.setenv("STORAGE_AUDIT_LOG", str(tmp_path / "storage-audit-log.jsonl"))
    monkeypatch.setenv("RETRIEVAL_AUDIT_LOG", str(tmp_path / "retrieval-audit-log.jsonl"))
    if set_store:
        monkeypatch.setenv("STORAGE_STORE", str(tmp_path / "store.json"))
    else:
        monkeypatch.delenv("STORAGE_STORE", raising=False)
    spec = importlib.util.spec_from_file_location(
        f"_policy_test_{server}_{uuid.uuid4().hex}", SERVERS_DIR / server / "server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(module, tool, args):
    async def run():
        async with Client(module.mcp) as client:
            return await client.call_tool(tool, args)

    return asyncio.run(run())


def _audit(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_storage_denied(module, role, op, tmp_path):
    with pytest.raises(ToolError) as excinfo:
        _call(module, op, STORAGE_ARGS[op])
    assert str(excinfo.value).startswith(
        f"authorization_denied: role '{role}' may not call '{op}'"
    )
    records = _audit(tmp_path / "storage-audit-log.jsonl")
    assert len(records) == 1
    assert records[0]["event"] == "authorization_denied"
    assert records[0]["role"] == role
    assert records[0]["operation"] == op


def _assert_retrieve_denied(module, role, tmp_path):
    with pytest.raises(ToolError) as excinfo:
        _call(module, "retrieve", {"query": CLASSIFICATION_QUERY})
    assert str(excinfo.value).startswith(
        f"authorization_denied: role '{role}' may not call 'retrieve': "
    )
    records = _audit(tmp_path / "retrieval-audit-log.jsonl")
    assert len(records) == 1
    assert records[0]["event"] == "authorization_denied"
    assert records[0]["role"] == role
    assert records[0]["operation"] == "retrieve"


@pytest.mark.parametrize("op", STORAGE_OPS)
@pytest.mark.parametrize("role", RUNTIME_ROLES)
def test_storage_authorization_matches_policy(role, op, monkeypatch, tmp_path):
    server = _load_server("storage", role, monkeypatch, tmp_path)
    if op in EXPECTED_STORAGE_GRANTS[role]:
        _call(server, op, STORAGE_ARGS[op])
        records = _audit(tmp_path / "storage-audit-log.jsonl")
        expected_event = STORAGE_SUCCESS_EVENT[op]
        if expected_event is None:
            assert records == []
        else:
            assert len(records) == 1
            assert records[0]["event"] == expected_event
            assert records[0]["role"] == role
            assert records[0]["operation"] == op
            assert records[0]["outcome"] == "success"
    else:
        _assert_storage_denied(server, role, op, tmp_path)


@pytest.mark.parametrize("role", RUNTIME_ROLES)
def test_retrieve_authorization_and_ceiling_match_policy(role, monkeypatch, tmp_path):
    server = _load_server("retrieval", role, monkeypatch, tmp_path)
    ceiling = EXPECTED_RETRIEVE_CEILING[role]
    if ceiling is None:
        _assert_retrieve_denied(server, role, tmp_path)
        return

    result = _call(server, "retrieve", {"query": CLASSIFICATION_QUERY})
    docs = json.loads(result.content[0].text)
    classifications = {doc["classification"] for doc in docs}
    assert "confidential" not in classifications
    assert classifications == {"public", "internal"}

    records = _audit(tmp_path / "retrieval-audit-log.jsonl")
    assert [r["event"] for r in records] == ["classification_withheld", "retrieval_success"]
    for record in records:
        assert record["role"] == role
        assert record["operation"] == "retrieve"
    assert "2 result(s)" in records[1]["detail"]
    assert ceiling in records[1]["detail"]


@pytest.mark.parametrize("op", STORAGE_OPS)
@pytest.mark.parametrize("name", NON_RUNTIME_NAMES, ids=_name_id)
def test_non_runtime_names_denied_storage(name, op, monkeypatch, tmp_path):
    server = _load_server("storage", name, monkeypatch, tmp_path)
    _assert_storage_denied(server, name, op, tmp_path)


@pytest.mark.parametrize("name", NON_RUNTIME_NAMES, ids=_name_id)
def test_non_runtime_names_denied_retrieve(name, monkeypatch, tmp_path):
    server = _load_server("retrieval", name, monkeypatch, tmp_path)
    _assert_retrieve_denied(server, name, tmp_path)


def test_storage_store_defaults_next_to_audit_log(monkeypatch, tmp_path):
    server = _load_server("storage", "implementer", monkeypatch, tmp_path, set_store=False)
    expected_store = tmp_path / "storage-store.json"
    assert server.STORE_PATH == expected_store
    _call(server, "write_entry", {"key": "k", "value": "v"})
    assert expected_store.exists()
    assert json.loads(expected_store.read_text(encoding="utf-8")) == {"k": "v"}


# ---------------------------------------------------------------------------
# Module 4.1 Enforcement Layer 3 and policy observability.
#
# - run-tests skill activation scope: the skill's Activation Scope table, the
#   agent definitions that hold the Skill tool, the hook registration, and the
#   hook's decisions (run as a subprocess with real stdin/stdout).
# - Container permissions: scripts/run-agent.sh launched with a fake docker
#   that records its arguments.
# - Observability: every audit record written on a denial or success carries
#   the same required fields across storage, retrieval and skill enforcement.
#
# These are deterministic tests. They do not start a Claude Code session.
# ---------------------------------------------------------------------------

import datetime
import os
import subprocess

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_HOOK = REPO_ROOT / "scripts" / "enforce_skill_scope.py"
RUN_TESTS_SKILL = REPO_ROOT / ".claude" / "skills" / "run-tests" / "SKILL.md"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
PROJECT_SETTINGS = REPO_ROOT / ".claude" / "settings.json"
RUN_AGENT = REPO_ROOT / "scripts" / "run-agent.sh"

# Hard-coded from each role's "Skill activation scope" table for run-tests.
EXPECTED_RUN_TESTS_SCOPE = {
    "tester": "YES",
    "planner": "NO",
    "implementer": "NO",
    "reviewer": "NO",
    "project-manager": "NO",
    "orchestrator": "NO",
}

# Agent definitions allowed to hold the Skill tool.
EXPECTED_SKILL_TOOL_HOLDERS = {"tester"}

# agent_type values the hook may receive; None is the main (orchestrator) session.
HOOK_AGENT_TYPES = [
    None,
    "planner",
    "implementer",
    "tester",
    "marketradar-code-reviewer",
    "project-manager",
    "general-purpose",
]

# Hard-coded from each role's "Container permissions" line:
# launch name -> (AGENT_ROLE, workspace mode, /memory mounted)
EXPECTED_CONTAINER = {
    "planner": ("planner", "ro", False),
    "implementer": ("implementer", "rw", True),
    "tester": ("tester", "ro", False),
    "marketradar-code-reviewer": ("reviewer", "ro", False),
    "reviewer": ("reviewer", "ro", False),
    "project-manager": ("project-manager", "ro", False),
    "orchestrator": ("orchestrator", "rw", True),
}

AUDIT_REQUIRED_FIELDS = {
    "timestamp",
    "event",
    "operation",
    "role",
    "outcome",
    "detail",
    "policy_reference",
}


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    block = text.split("---\n", 2)[1]
    fields = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def _tools(fields):
    return {tool.strip() for tool in fields.get("tools", "").split(",") if tool.strip()}


def _run_hook(payload_text, tmp_path, extra_env=None):
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path / "home"),
        "SKILL_AUDIT_LOG": str(tmp_path / "skill-audit-log.jsonl"),
        "CLAUDE_PROJECT_DIR": str(REPO_ROOT),
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-I", str(SKILL_HOOK)],
        input=payload_text,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _skill_payload(agent_type, skill):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": skill}}
    if agent_type is not None:
        payload["agent_type"] = agent_type
    return json.dumps(payload)


def _expected_hook_decision(agent_type, skill):
    if agent_type == "tester":
        return "authorized" if skill == "run-tests" else "denied"
    if skill == "run-tests":
        return "denied"
    return None


def _deny_decision(result):
    return json.loads(result.stdout)["hookSpecificOutput"]


def _check_audit_record(record):
    missing = AUDIT_REQUIRED_FIELDS - set(record)
    assert not missing, f"audit record missing {sorted(missing)}: {record}"
    assert record["policy_reference"] == "docs/governance-policy.md"
    datetime.datetime.fromisoformat(record["timestamp"])


def test_run_tests_skill_defines_activation_scope():
    assert RUN_TESTS_SKILL.exists(), "Missing .claude/skills/run-tests/SKILL.md"
    fields = _frontmatter(RUN_TESTS_SKILL)
    assert fields.get("name") == "run-tests"
    assert fields.get("description")
    text = RUN_TESTS_SKILL.read_text(encoding="utf-8")
    assert "## Activation Scope" in text
    scope = {
        match.group(1): match.group(2)
        for match in re.finditer(r"^\|\s*`?([a-z-]+)`?[^|]*\|\s*(YES|NO)\s*\|", text, re.MULTILINE)
    }
    assert scope == EXPECTED_RUN_TESTS_SCOPE


def test_only_tester_holds_skill_tool():
    holders = set()
    for path in sorted(AGENTS_DIR.glob("*.md")):
        fields = _frontmatter(path)
        if "Skill" in _tools(fields):
            holders.add(fields.get("name"))
        assert "run-tests" not in fields.get("skills", ""), f"{path.name} preloads run-tests"
    assert holders == EXPECTED_SKILL_TOOL_HOLDERS


def test_reviewer_definition_has_no_skill_tool():
    fields = _frontmatter(AGENTS_DIR / "marketradar-code-reviewer.md")
    assert fields.get("name") == "marketradar-code-reviewer"
    assert "Skill" not in _tools(fields)


def test_project_settings_register_skill_hook():
    settings = json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8"))
    commands = [
        hook.get("command", "")
        for entry in settings["hooks"]["PreToolUse"]
        if entry.get("matcher") == "Skill"
        for hook in entry.get("hooks", [])
        if hook.get("type") == "command"
    ]
    assert any("scripts/enforce_skill_scope.py" in command for command in commands)


@pytest.mark.parametrize("skill", ["run-tests", "summarize-session"])
@pytest.mark.parametrize("agent_type", HOOK_AGENT_TYPES, ids=lambda value: value or "<main-session>")
def test_skill_hook_enforces_run_tests_scope(agent_type, skill, tmp_path):
    result = _run_hook(_skill_payload(agent_type, skill), tmp_path)
    assert result.returncode == 0, result.stderr
    expected = _expected_hook_decision(agent_type, skill)
    records = _audit(tmp_path / "skill-audit-log.jsonl")
    if expected == "denied":
        decision = _deny_decision(result)
        assert decision["hookEventName"] == "PreToolUse"
        assert decision["permissionDecision"] == "deny"
        assert decision["permissionDecisionReason"].startswith("skill_activation_denied:")
        assert len(records) == 1
        assert records[0]["event"] == "skill_activation_denied"
        assert records[0]["skill"] == skill
        assert records[0]["role"] == (agent_type or "")
    elif expected == "authorized":
        assert result.stdout.strip() == ""
        assert [record["event"] for record in records] == ["skill_activation_authorized"]
    else:
        assert result.stdout.strip() == ""
        assert records == []


@pytest.mark.parametrize("skill_value", ["run-tests", "/run-tests", "run-tests --watch", "project:run-tests"])
def test_skill_hook_recognizes_run_tests_name_forms(skill_value, tmp_path):
    result = _run_hook(_skill_payload("marketradar-code-reviewer", skill_value), tmp_path)
    assert _deny_decision(result)["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "raw",
    ["", "not json", "[]", json.dumps({"tool_name": "Skill", "tool_input": "run-tests"})],
    ids=["empty", "not-json", "list", "string-tool-input"],
)
def test_skill_hook_fails_closed_on_unreadable_input(raw, tmp_path):
    result = _run_hook(raw, tmp_path)
    assert result.returncode == 0, result.stderr
    assert _deny_decision(result)["permissionDecision"] == "deny"


def test_skill_hook_never_writes_audit_inside_repository(tmp_path):
    inside = REPO_ROOT / "logs" / "skill-audit-log.jsonl"
    existed = inside.exists()
    result = _run_hook(
        _skill_payload("implementer", "run-tests"),
        tmp_path,
        {"SKILL_AUDIT_LOG": str(inside)},
    )
    assert _deny_decision(result)["permissionDecision"] == "deny"
    assert inside.exists() == existed
    fallback = tmp_path / "home" / ".local" / "state" / "marketradar" / "skill-audit-log.jsonl"
    written = fallback if fallback.exists() else Path("/logs/skill-audit-log.jsonl")
    records = _audit(written)
    assert records and records[-1]["event"] == "skill_activation_denied"


def _launch(launch_name, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake_docker = bin_dir / "docker"
    fake_docker.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$FAKE_DOCKER_ARGS"\n',
        encoding="utf-8",
    )
    fake_docker.chmod(0o755)
    args_file = tmp_path / "docker-args.txt"
    env = {
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '/usr/bin:/bin')}",
        "FAKE_DOCKER_ARGS": str(args_file),
        "HOME": str(tmp_path),
    }
    result = subprocess.run(
        ["bash", str(RUN_AGENT), launch_name, "true"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    args = args_file.read_text(encoding="utf-8").splitlines() if args_file.exists() else None
    return result, args


@pytest.mark.parametrize("launch_name", sorted(EXPECTED_CONTAINER))
def test_run_agent_container_permissions_match_policy(launch_name, tmp_path):
    role, mode, memory = EXPECTED_CONTAINER[launch_name]
    result, args = _launch(launch_name, tmp_path)
    assert result.returncode == 0, result.stderr
    assert args is not None
    assert f"AGENT_ROLE={role}" in args
    assert f"{REPO_ROOT}:/workspace:{mode}" in args
    assert f"{REPO_ROOT}/.memory/knowledge:/workspace/.memory/knowledge:ro" in args
    assert f"{REPO_ROOT}/.memory/reference:/workspace/.memory/reference:ro" in args
    assert "agent-logs:/logs" in args
    assert ("agent-memory:/memory" in args) is memory
    assert "-p" not in args and "--publish" not in args
    assert not any(
        arg.startswith(("SLACK_", "ANTHROPIC_API_KEY")) or "docker.sock" in arg for arg in args
    )


@pytest.mark.parametrize("launch_name", ["code-reviewer", "unknown-role"])
def test_run_agent_rejects_roles_without_policy_entry(launch_name, tmp_path):
    result, args = _launch(launch_name, tmp_path)
    assert result.returncode != 0
    assert args is None
    assert "Launching" not in result.stdout


def test_storage_audit_records_are_complete(monkeypatch, tmp_path):
    server = _load_server("storage", "implementer", monkeypatch, tmp_path)
    _call(server, "write_entry", {"key": "k", "value": "v"})
    with pytest.raises(ToolError):
        _call(server, "delete_entry", {"key": "k"})
    records = _audit(tmp_path / "storage-audit-log.jsonl")
    assert [record["event"] for record in records] == ["storage_write", "authorization_denied"]
    for record in records:
        _check_audit_record(record)


def test_retrieval_denial_audit_record_is_complete(monkeypatch, tmp_path):
    server = _load_server("retrieval", "orchestrator", monkeypatch, tmp_path)
    with pytest.raises(ToolError):
        _call(server, "retrieve", {"query": CLASSIFICATION_QUERY})
    records = _audit(tmp_path / "retrieval-audit-log.jsonl")
    assert [record["event"] for record in records] == ["authorization_denied"]
    _check_audit_record(records[0])


def test_retrieval_withholding_audit_records_are_complete(monkeypatch, tmp_path):
    server = _load_server("retrieval", "implementer", monkeypatch, tmp_path)
    _call(server, "retrieve", {"query": CLASSIFICATION_QUERY})
    records = _audit(tmp_path / "retrieval-audit-log.jsonl")
    assert [record["event"] for record in records] == ["classification_withheld", "retrieval_success"]
    for record in records:
        _check_audit_record(record)


def test_skill_denial_audit_record_is_complete(tmp_path):
    _run_hook(_skill_payload("marketradar-code-reviewer", "run-tests"), tmp_path)
    records = _audit(tmp_path / "skill-audit-log.jsonl")
    assert len(records) == 1
    _check_audit_record(records[0])
    assert records[0]["skill"] == "run-tests"
