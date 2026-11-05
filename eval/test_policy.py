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
