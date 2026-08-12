from pathlib import Path
import re
import json

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
def test_documentation_writer_policy_matches_enforcement():
    policy = (ROOT / "docs" / "governance-policy.md").read_text(encoding="utf-8")

    storage = json.loads(
        (ROOT / "mcp-servers" / "storage" / "allow-list.json").read_text(
            encoding="utf-8"
        )
    )

    retrieval = json.loads(
        (ROOT / "mcp-servers" / "retrieval" / "allow-list.json").read_text(
            encoding="utf-8"
        )
    )

    startup = (ROOT / "scripts" / "run-agent.ps1").read_text(encoding="utf-8")

    role = "documentation-writer"

    # Policy entry exists and records the intended container permissions.
    assert "## Role: documentation-writer" in policy
    assert "**Maximum level:** internal" in policy
    assert "**Container permissions:** workspace read-only, memory omitted" in policy

    # Storage grants match the policy.
    assert role in storage["read_entry"]
    assert role in storage["list_entries"]
    assert role not in storage["write_entry"]
    assert role not in storage["update_entry"]
    assert role not in storage["delete_entry"]
    assert role not in storage["audit_read"]

    # Retrieval grant and classification ceiling match the policy.
    assert retrieval["retrieve"][role]["granted"] is True
    assert retrieval["retrieve"][role]["classification_ceiling"] == "internal"

    # Startup script recognizes the role as a governed read-only role.
    assert "documentation-writer" in startup
    assert "'reviewer', 'tester', 'project-manager', 'documentation-writer'" in startup