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
    import yaml

    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"].get("policy-gate")
    assert job is not None, "Missing policy-gate job"
    assert job.get("continue-on-error") is not True, "policy-gate must remain a real gate, not advisory."
    for step in job.get("steps", []):
        assert step.get("continue-on-error") is not True, (
            f"policy-gate step {step.get('name')!r} must not use continue-on-error."
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
    "dependency-auditor",
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
    "dependency-auditor": set(),
}

# None means retrieval is denied.
EXPECTED_RETRIEVE_CEILING = {
    "planner": "internal",
    "implementer": "internal",
    "tester": "internal",
    "reviewer": "internal",
    "project-manager": None,
    "orchestrator": None,
    "dependency-auditor": None,
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
    "dependency-auditor": "NO",
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
    "dependency-auditor",
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
    "dependency-auditor": ("dependency-auditor", "ro", False),
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


# ---------------------------------------------------------------------------
# Policy observability: parse the per-role tables in docs/governance-policy.md
# and compare them with the enforcement artifacts, so a grant changed in only
# one place fails. Each comparison reports overgrants (granted by an artifact
# but not by the policy) and missing grants (granted by the policy but absent
# from the artifact). The hard-coded matrices above are also checked against
# the parsed tables.
# ---------------------------------------------------------------------------

POLICY_PATH = REPO_ROOT / "docs" / "governance-policy.md"
POLICY_ROLES = [
    "planner",
    "implementer",
    "tester",
    "marketradar-code-reviewer",
    "project-manager",
    "orchestrator",
    "dependency-auditor",
]


def _policy_subsection(body, title):
    match = re.search(rf"^### {re.escape(title)}[ \t]*$(.*?)(?=^### |\Z)", body, re.M | re.S)
    assert match, f"policy role section is missing '### {title}'"
    return match.group(1)


def _policy_table_rows(section):
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def _parse_policy_roles():
    text = POLICY_PATH.read_text(encoding="utf-8")
    parts = re.split(r"^## Role: (\S+)[ \t]*$", text, flags=re.M)
    roles = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        body = re.split(r"^## ", body, flags=re.M)[0]
        runtime = re.search(r"^\*\*Module 4 runtime role:\*\* `([^`]+)`", body, re.M)
        ceiling = re.search(r"^\*\*Maximum level:\*\*\s*(\w+)", body, re.M)
        container = re.search(r"^\*\*Container permissions:\*\*(.*)$", body, re.M)
        assert runtime and ceiling and container, f"policy role '{name}' is missing a required field"
        mcp = {
            row[0]: row[2].upper().startswith("YES")
            for row in _policy_table_rows(_policy_subsection(body, "MCP server and operation access"))
            if len(row) >= 3 and row[1] in ("storage", "retrieval")
        }
        skills = {
            row[0]: row[1].upper().startswith("YES")
            for row in _policy_table_rows(_policy_subsection(body, "Skill activation scope"))
            if len(row) >= 2 and row[1].upper().startswith(("YES", "NO"))
        }
        line = container.group(1)
        mode = "rw" if "workspace read-write" in line else "ro" if "workspace read-only" in line else None
        memory = True if "memory mounted" in line else False if "memory omitted" in line else None
        roles[name] = {
            "runtime": runtime.group(1),
            "storage": {op: mcp.get(op) for op in STORAGE_OPS},
            "retrieve": mcp.get("retrieve"),
            "ceiling": ceiling.group(1),
            "skills": skills,
            "container": (mode, memory),
        }
    return roles


def _grant_diff(label, artifact, policy):
    overgrants = sorted(set(artifact) - set(policy))
    missing = sorted(set(policy) - set(artifact))
    return f"{label}: overgrants {overgrants}, missing grants {missing}"


@pytest.fixture(scope="module")
def policy_roles():
    return _parse_policy_roles()


def test_policy_tables_parse_for_every_role(policy_roles):
    assert sorted(policy_roles) == sorted(POLICY_ROLES)
    for name, role in policy_roles.items():
        assert None not in role["storage"].values(), f"{name}: storage table incomplete"
        assert role["retrieve"] is not None, f"{name}: retrieve row missing"
        assert "run-tests" in role["skills"], f"{name}: run-tests row missing"
        assert None not in role["container"], f"{name}: container permissions not parsed"


def test_hard_coded_matrices_match_policy_tables(policy_roles):
    by_runtime = {role["runtime"]: role for role in policy_roles.values()}
    assert EXPECTED_STORAGE_GRANTS == {
        runtime: {op for op, granted in role["storage"].items() if granted}
        for runtime, role in by_runtime.items()
    }
    assert EXPECTED_RETRIEVE_CEILING == {
        runtime: (role["ceiling"] if role["retrieve"] else None)
        for runtime, role in by_runtime.items()
    }
    assert EXPECTED_RUN_TESTS_SCOPE == {
        runtime: ("YES" if role["skills"]["run-tests"] else "NO")
        for runtime, role in by_runtime.items()
    }
    for name, role in policy_roles.items():
        assert EXPECTED_CONTAINER[name] == (role["runtime"], *role["container"])


@pytest.mark.parametrize("op", STORAGE_OPS)
def test_storage_allow_list_matches_policy_tables(op, policy_roles):
    allow_list = json.loads((SERVERS_DIR / "storage" / "allow-list.json").read_text(encoding="utf-8"))
    assert set(allow_list) - {"explicit_denials"} == set(STORAGE_OPS)
    granted = {role["runtime"] for role in policy_roles.values() if role["storage"][op]}
    actual = set(allow_list[op])
    assert actual == granted, _grant_diff(op, actual, granted)


def test_retrieval_allow_list_matches_policy_tables(policy_roles):
    rules = json.loads((SERVERS_DIR / "retrieval" / "allow-list.json").read_text(encoding="utf-8"))["retrieve"]
    granted = {role["runtime"]: role["ceiling"] for role in policy_roles.values() if role["retrieve"]}
    actual = {name: rule.get("classification_ceiling") for name, rule in rules.items() if rule.get("granted")}
    assert set(actual) == set(granted), _grant_diff("retrieve", actual, granted)
    assert actual == granted, f"retrieve ceilings differ: allow-list {actual}, policy {granted}"
    known = {role["runtime"] for role in policy_roles.values()}
    assert set(rules) <= known, f"retrieval allow-list names roles without a policy entry: {sorted(set(rules) - known)}"
    assert set(rules) == known, f"roles not explicitly represented in the retrieval allow-list: {sorted(known - set(rules))}"


def test_run_tests_scope_matches_policy_tables(policy_roles):
    text = RUN_TESTS_SKILL.read_text(encoding="utf-8")
    skill_scope = {
        match.group(1)
        for match in re.finditer(r"^\|\s*`?([a-z-]+)`?[^|]*\|\s*YES\s*\|", text, re.MULTILINE)
    }
    granted = {role["runtime"] for role in policy_roles.values() if role["skills"]["run-tests"]}
    assert skill_scope == granted, _grant_diff("run-tests Activation Scope", skill_scope, granted)
    holders = set()
    for path in sorted(AGENTS_DIR.glob("*.md")):
        fields = _frontmatter(path)
        if "Skill" in _tools(fields):
            holders.add(fields.get("name"))
    expected_holders = {name for name, role in policy_roles.items() if role["skills"]["run-tests"]}
    assert holders == expected_holders, _grant_diff("Skill tool holders", holders, expected_holders)


@pytest.mark.parametrize("role_name", POLICY_ROLES)
def test_skill_hook_matches_policy_tables(role_name, policy_roles, tmp_path):
    agent_type = None if role_name == "orchestrator" else role_name
    result = _run_hook(_skill_payload(agent_type, "run-tests"), tmp_path)
    assert result.returncode == 0, result.stderr
    authorized = result.stdout.strip() == ""
    granted = policy_roles[role_name]["skills"]["run-tests"]
    assert authorized == granted, (
        f"hook {'authorizes' if authorized else 'denies'} run-tests for {role_name}; "
        f"policy says {'YES' if granted else 'NO'}"
    )


@pytest.mark.parametrize("role_name", POLICY_ROLES)
def test_container_permissions_match_policy_tables(role_name, policy_roles, tmp_path):
    role = policy_roles[role_name]
    mode, memory = role["container"]
    result, args = _launch(role_name, tmp_path)
    assert result.returncode == 0, result.stderr
    assert args is not None
    assert f"AGENT_ROLE={role['runtime']}" in args
    assert f"{REPO_ROOT}:/workspace:{mode}" in args
    assert ("agent-memory:/memory" in args) is memory


def test_launcher_accepts_only_policy_roles(policy_roles):
    script = RUN_AGENT.read_text(encoding="utf-8")
    accepted = set()
    for match in re.finditer(r"^\s{2}([a-z|-]+)\)[ \t]*$", script, re.M):
        accepted |= set(match.group(1).split("|"))
    known = set(policy_roles) | {role["runtime"] for role in policy_roles.values()}
    assert accepted <= known, f"run-agent.sh launches roles without a policy entry: {sorted(accepted - known)}"
    missing = set(policy_roles) - accepted
    assert not missing, f"policy roles that run-agent.sh cannot launch: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Module 4.1 Exercise 1: dependency-auditor enforcement.
# ---------------------------------------------------------------------------

BASH_HOOK = REPO_ROOT / "scripts" / "enforce_bash_scope.py"
AUDITOR_DEFINITION = AGENTS_DIR / "dependency-auditor.md"

AUDITOR_ALLOWED_COMMANDS = [
    "npm audit --json --prefix tracker-api",
    "npm audit --json --prefix tracker-client",
    "npm outdated --json --prefix tracker-api",
    "npm outdated --json --prefix tracker-client",
    "npm --prefix tracker-api audit --json",
    "npm --prefix tracker-client outdated --json",
    "npm  audit   --json --prefix   tracker-api",
]

AUDITOR_DENIED_COMMANDS = [
    "npm install --prefix tracker-api",
    "npm ci --prefix tracker-client",
    "npm update --prefix tracker-api",
    "npm uninstall vite --prefix tracker-client",
    "npm audit fix --prefix tracker-api",
    "npm audit fix --force --json --prefix tracker-api",
    "npm test --prefix tracker-api",
    "npm --prefix tracker-api test",
    "npm audit --json",
    "npm audit --json --prefix ..",
    "npm audit --json --prefix tracker-api > audit.json",
    "npm audit --json --prefix tracker-api; rm -rf tracker-api",
    "npm audit --json --prefix tracker-api && npm install",
    "npm audit --json --prefix tracker-api\ntouch /workspace/should-fail.txt",
    "touch /workspace/should-fail.txt",
    "git commit -am x",
    "",
]


def _run_bash_hook(payload_text, tmp_path):
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path / "home"),
        "BASH_AUDIT_LOG": str(tmp_path / "bash-audit-log.jsonl"),
        "CLAUDE_PROJECT_DIR": str(REPO_ROOT),
    }
    return subprocess.run(
        [sys.executable, "-I", str(BASH_HOOK)],
        input=payload_text,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _bash_payload(agent_type, command):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}
    if agent_type is not None:
        payload["agent_type"] = agent_type
    return json.dumps(payload)


def test_dependency_auditor_definition_matches_policy(policy_roles):
    fields = _frontmatter(AUDITOR_DEFINITION)
    assert fields.get("name") == "dependency-auditor"
    assert _tools(fields) == {"Read", "Grep", "Glob", "Bash"}
    assert "skills" not in fields
    assert "dependency-auditor" in policy_roles


def test_project_settings_register_bash_hook():
    settings = json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8"))
    commands = [
        hook.get("command", "")
        for entry in settings["hooks"]["PreToolUse"]
        if entry.get("matcher") == "Bash"
        for hook in entry.get("hooks", [])
        if hook.get("type") == "command"
    ]
    assert any("scripts/enforce_bash_scope.py" in command for command in commands)


@pytest.mark.parametrize("command", AUDITOR_ALLOWED_COMMANDS)
def test_bash_hook_allows_auditor_audit_commands(command, tmp_path):
    result = _run_bash_hook(_bash_payload("dependency-auditor", command), tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
    records = _audit(tmp_path / "bash-audit-log.jsonl")
    assert [record["event"] for record in records] == ["bash_command_authorized"]
    _check_audit_record(records[0])


@pytest.mark.parametrize("command", AUDITOR_DENIED_COMMANDS)
def test_bash_hook_denies_other_auditor_commands(command, tmp_path):
    result = _run_bash_hook(_bash_payload("dependency-auditor", command), tmp_path)
    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"].startswith("bash_command_denied:")
    records = _audit(tmp_path / "bash-audit-log.jsonl")
    assert [record["event"] for record in records] == ["bash_command_denied"]
    assert records[0]["role"] == "dependency-auditor"
    _check_audit_record(records[0])


@pytest.mark.parametrize("agent_type", [None, "implementer", "tester", "marketradar-code-reviewer"])
def test_bash_hook_does_not_govern_other_roles(agent_type, tmp_path):
    result = _run_bash_hook(_bash_payload(agent_type, "npm install --prefix tracker-api"), tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
    assert _audit(tmp_path / "bash-audit-log.jsonl") == []


@pytest.mark.parametrize("raw", ["", "not json", "[]"], ids=["empty", "not-json", "list"])
def test_bash_hook_fails_closed_on_unreadable_input(raw, tmp_path):
    result = _run_bash_hook(raw, tmp_path)
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_storage_explicit_denials_match_policy_tables(policy_roles):
    allow_list = json.loads((SERVERS_DIR / "storage" / "allow-list.json").read_text(encoding="utf-8"))
    denials = allow_list.get("explicit_denials", {})
    assert "dependency-auditor" in denials
    by_runtime = {role["runtime"]: role for role in policy_roles.values()}
    for runtime, ops in denials.items():
        assert runtime in by_runtime, f"explicit denial for a role without a policy entry: {runtime}"
        policy_denied = {op for op, granted in by_runtime[runtime]["storage"].items() if not granted}
        assert set(ops) == policy_denied, _grant_diff(f"{runtime} explicit denials", ops, policy_denied)
        for op in ops:
            assert runtime not in allow_list[op], f"{runtime} is both granted and denied {op}"


# ---------------------------------------------------------------------------
# Module 4.2: Evaluation Harness gating job (eval-gate).
# ---------------------------------------------------------------------------

import yaml

WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DETERMINISTIC_EVAL_FILES = [
    "eval/test_deterministic.py",
    "eval/test_deterministic_router.py",
    "eval/test_deterministic_step.py",
]


def _workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _step(job, step_id):
    return next(step for step in job["steps"] if step.get("id") == step_id)


def _agent_affecting_pattern():
    classify = next(
        step for step in _workflow()["jobs"]["change-type-check"]["steps"] if step.get("id") == "classify"
    )
    match = re.search(r"grep -qE '([^']+)'; then\s*\n\s*echo \"agent-affecting=true\"", classify["run"])
    assert match, "change-type-check has no agent-affecting classification"
    return re.compile(match.group(1))


def test_eval_gate_reports_on_every_run_after_policy_gate():
    jobs = _workflow()["jobs"]
    job = jobs["eval-gate"]
    assert set(job["needs"]) == {"change-type-check", "policy-gate"}
    assert "if" not in job, "eval-gate must have no job-level condition so it reports on every run"
    assert job.get("continue-on-error") is not True
    assert "agent-affecting" in jobs["change-type-check"]["outputs"]


def test_eval_gate_deterministic_step_is_gating_and_runs_in_docker():
    step = _step(_workflow()["jobs"]["eval-gate"], "deterministic")
    assert step.get("continue-on-error") is not True
    assert "docker run" in step["run"] and "agentic_engineer_4" in step["run"]
    assert ":/workspace:ro" in step["run"]
    for path in DETERMINISTIC_EVAL_FILES:
        assert path in step["run"]
    assert "env" not in step


def test_eval_gate_rubric_step_is_advisory_and_runs_in_docker():
    step = _step(_workflow()["jobs"]["eval-gate"], "rubric")
    assert step.get("continue-on-error") is True
    assert "docker run" in step["run"] and "agentic_engineer_4" in step["run"]
    assert "--judge openrouter" in step["run"]
    assert "steps.deterministic.outcome == 'success'" in step["if"]


def test_openrouter_key_is_scoped_to_the_rubric_step_only():
    workflow = _workflow()
    assert "OPENROUTER_API_KEY" not in json.dumps(workflow.get("env", {}))
    holders = []
    for job_name, job in workflow["jobs"].items():
        assert "OPENROUTER_API_KEY" not in json.dumps(job.get("env", {})), f"{job_name} exposes the key job-wide"
        for step in job.get("steps", []):
            if "OPENROUTER_API_KEY" in json.dumps(step.get("env", {})):
                holders.append((job_name, step.get("id")))
    assert holders == [("eval-gate", "rubric")]
    rubric_env = _step(workflow["jobs"]["eval-gate"], "rubric")["env"]
    assert rubric_env["OPENROUTER_API_KEY"] == "${{ secrets.OPENROUTER_API_KEY }}"


def test_eval_reports_upload_always_and_ignore_missing():
    upload = next(
        step for step in _workflow()["jobs"]["eval-gate"]["steps"]
        if str(step.get("uses", "")).startswith("actions/upload-artifact")
    )
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "ignore"
    assert "deterministic-report.json" in upload["with"]["path"]
    assert "rubric-report.json" in upload["with"]["path"]


@pytest.mark.parametrize(
    "path, expected",
    [
        ("docs/ci-step-design.md", False),
        ("README.md", False),
        ("docs/module3/holdout-task-set.md", False),
        ("tracker-client/src/App.tsx", False),
        (".claude/agents/tester.md", True),
        (".claude/settings.json", True),
        ("scripts/enforce_bash_scope.py", True),
        ("mcp-servers/storage/allow-list.json", True),
        ("eval/test_policy.py", True),
        ("docs/governance-policy.md", True),
        ("CLAUDE.md", True),
        ("Dockerfile", True),
        (".github/workflows/ci.yml", True),
    ],
)
def test_change_classifier_separates_agent_affecting_from_docs_only(path, expected):
    assert bool(_agent_affecting_pattern().match(path)) is expected


def test_audit_trail_records_eval_gate():
    job = _workflow()["jobs"]["audit-trail"]
    assert "eval-gate" in job["needs"]
    assert job["if"] == "always()"
    command = next(step["run"] for step in job["steps"] if "build-audit-trail.py" in str(step.get("run", "")))
    assert "--eval-result" in command and "needs.eval-gate.result" in command
