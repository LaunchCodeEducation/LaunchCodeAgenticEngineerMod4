from pathlib import Path
import json
import re

import pytest


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
# Policy <-> artifact agreement (Module 4.1: policy observable in code).
# Each check fails in either direction: the policy grants something the
# artifact does not, or the artifact grants something the policy does not.
# ---------------------------------------------------------------------------

POLICY_PATH = ROOT / "docs" / "governance-policy.md"
STORAGE_ALLOWLIST = ROOT / "mcp-servers" / "storage" / "allow-list.json"
RETRIEVAL_ALLOWLIST = ROOT / "mcp-servers" / "retrieval" / "allow-list.json"
COURSETOOLS_ALLOWLIST = ROOT / "mcp" / "roles.allowlist.json"
RUN_AGENT_PS1 = ROOT / "scripts" / "run-agent.ps1"
RUN_AGENT_SH = ROOT / "scripts" / "run-agent.sh"
SKILLS_DIR = ROOT / "skills"

TABLE_ROW = re.compile(r"^\|\s*([a-z_\-]+)\s*\|\s*([a-z_\-]+)\s*\|\s*(YES|NO)\s*\|", re.M)
SKILL_ROW = re.compile(r"^\|\s*([a-z_\-]+)\s*\|\s*(YES|NO)\s*\|", re.M)


def _policy_sections() -> dict[str, str]:
    """Map role name -> text of its '## Role: <name>' section."""
    text = POLICY_PATH.read_text(encoding="utf-8")
    sections = {}
    for chunk in re.split(r"(?m)^(?=## )", text):
        match = re.match(r"## Role: (\S+)", chunk)
        if match:
            sections[match.group(1)] = chunk
    return sections


def _subsection(section: str, heading: str) -> str:
    start = section.find(f"### {heading}")
    assert start != -1, f"policy section is missing '### {heading}'"
    end = section.find("\n### ", start + 1)
    return section[start:] if end == -1 else section[start:end]


POLICY = _policy_sections()
ROLES = sorted(POLICY)


def _policy_ops(role: str, server: str) -> set[str]:
    table = _subsection(POLICY[role], "MCP server and operation access")
    return {op for op, srv, granted in TABLE_ROW.findall(table) if srv == server and granted == "YES"}


def _policy_skills(role: str) -> set[str]:
    table = _subsection(POLICY[role], "Skill activation scope")
    return {skill for skill, granted in SKILL_ROW.findall(table) if granted == "YES"}


def _policy_ceiling(role: str) -> str:
    block = _subsection(POLICY[role], "Data classification ceiling")
    return re.search(r"\*\*Maximum level:\*\*\s*(\w+)", block).group(1)


def _policy_workspace_mode(role: str) -> str:
    match = re.search(r"\*\*Container permissions:\*\*\s*workspace (read-write|read-only)", POLICY[role])
    assert match, f"{role}: policy entry has no '**Container permissions:**' line"
    return "rw" if match.group(1) == "read-write" else "ro"


def _skill_scope(path: Path) -> tuple[set[str], set[str]]:
    text = path.read_text(encoding="utf-8")
    def roles(label):
        match = re.search(rf"\*\*{label}:\*\*\s*(.+)", text)
        return {r.strip() for r in match.group(1).split(",")} if match else set()
    return roles("Permitted roles"), roles("Denied roles")


SCOPED_SKILLS = sorted(
    p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md") if "## Activation Scope" in p.read_text(encoding="utf-8")
)


def test_policy_has_expected_roles():
    assert set(ROLES) == {"orchestrator", "planner", "implementer", "reviewer", "tester", "project-manager", "dependency-auditor"}, ROLES


@pytest.mark.parametrize("role", ROLES)
def test_role_definition_file_exists(role):
    defined_in = re.search(r"\*\*Defined in:\*\*\s*(\S+)", POLICY[role]).group(1)
    assert (ROOT / defined_in).exists(), f"{role}: {defined_in} does not exist"


@pytest.mark.parametrize("role", ROLES)
def test_storage_allowlist_matches_policy(role):
    allow = json.loads(STORAGE_ALLOWLIST.read_text(encoding="utf-8"))
    in_allowlist = {op for op, roles in allow.items() if role in roles}
    in_policy = _policy_ops(role, "storage")
    assert in_allowlist == in_policy, (
        f"{role}: policy grants {sorted(in_policy)}, allow-list grants {sorted(in_allowlist)}"
    )


def test_no_storage_overgrant():
    allow = json.loads(STORAGE_ALLOWLIST.read_text(encoding="utf-8"))
    overgrants = [
        f"{role} -> {op}"
        for op, roles in allow.items()
        for role in roles
        if role not in POLICY or op not in _policy_ops(role, "storage")
    ]
    assert not overgrants, f"allow-list grants operations the policy never gave: {overgrants}"


@pytest.mark.parametrize("role", ROLES)
def test_retrieval_allowlist_matches_policy(role):
    rule = json.loads(RETRIEVAL_ALLOWLIST.read_text(encoding="utf-8"))["retrieve"].get(role)
    policy_granted = "retrieve" in _policy_ops(role, "retrieval")
    assert rule is not None, f"{role}: missing from retrieval allow-list"
    assert rule["granted"] == policy_granted, f"{role}: policy retrieve={policy_granted}, allow-list={rule['granted']}"
    if policy_granted:
        assert rule["classification_ceiling"] == _policy_ceiling(role), (
            f"{role}: policy ceiling {_policy_ceiling(role)}, allow-list ceiling {rule['classification_ceiling']}"
        )


def test_run_tests_and_draft_pr_skills_exist():
    for skill in ("run-tests", "draft-pr-description"):
        assert skill in SCOPED_SKILLS, f"skills/{skill}/SKILL.md with an Activation Scope is missing"


@pytest.mark.parametrize("skill", SCOPED_SKILLS)
def test_skill_scope_matches_policy(skill):
    permitted, denied = _skill_scope(SKILLS_DIR / skill / "SKILL.md")
    policy_permitted = {role for role in ROLES if skill in _policy_skills(role)}
    assert permitted == policy_permitted, (
        f"{skill}: policy permits {sorted(policy_permitted)}, SKILL.md permits {sorted(permitted)}"
    )
    assert permitted | denied == set(ROLES), f"{skill}: Activation Scope does not list every role"
    assert not permitted & denied, f"{skill}: a role is both permitted and denied"


def test_run_tests_skill_matches_coursetools_allowlist():
    permitted, _ = _skill_scope(SKILLS_DIR / "run-tests" / "SKILL.md")
    allow = json.loads(COURSETOOLS_ALLOWLIST.read_text(encoding="utf-8"))
    assert set(allow["test_runner"]) == permitted, (
        f"run-tests permits {sorted(permitted)}, coursetools test_runner allows {sorted(allow['test_runner'])}"
    )


def _ps1_modes() -> dict[str, str]:
    text = RUN_AGENT_PS1.read_text(encoding="utf-8")
    modes = {}
    for roles, body in re.findall(r"\{\s*\$_\s+-in\s+([^}]*)\}\s*\{([^}]*)\}", text):
        mode = re.search(r"\$WorkspaceMode\s*=\s*'(rw|ro)'", body).group(1)
        for role in re.findall(r"'([a-z\-]+)'", roles):
            modes[role] = mode
    return modes


def _sh_modes() -> dict[str, str]:
    text = RUN_AGENT_SH.read_text(encoding="utf-8")
    modes = {}
    for roles, mode in re.findall(r"^\s*([a-z|\-]+)\)\s*\n\s*WORKSPACE_MODE=\"(rw|ro)\"", text, re.M):
        for role in roles.split("|"):
            modes[role] = mode
    return modes


@pytest.mark.parametrize("role", ROLES)
def test_container_workspace_matches_policy(role):
    expected = _policy_workspace_mode(role)
    for name, modes in (("run-agent.ps1", _ps1_modes()), ("run-agent.sh", _sh_modes())):
        assert role in modes, f"{role}: no branch in scripts/{name}, so the role cannot be launched"
        assert modes[role] == expected, f"{role}: policy says {expected}, scripts/{name} launches {modes[role]}"


def test_scripts_launch_no_role_without_policy():
    extra = (set(_ps1_modes()) | set(_sh_modes())) - set(ROLES)
    assert not extra, f"launch scripts handle roles with no policy entry: {sorted(extra)}"
