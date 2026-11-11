"""Sample deterministic harness checks for the full workflow."""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_handoff_validator_cli_accepts_good_input(tmp_path):
    output = tmp_path / "result.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/validate_handoff_deterministic.py",
            "--input",
            "examples/handoff.json",
            "--schema",
            "schemas/handoff.json",
            "--output",
            str(output),
        ],
        cwd=REPO,
        check=True,
    )
    assert json.loads(output.read_text())["valid"] is True


def test_governance_policy_mentions_least_privilege():
    text = (REPO / "docs" / "governance-policy.md").read_text(encoding="utf-8")
    assert "Every role starts with no access" in text


def test_all_required_directories_exist():
    for relative in [".agents", ".skills", "mcp-servers/storage", "mcp-servers/retrieval", "docs/adr"]:
        assert (REPO / relative).exists()

# CI trigger: verifies the eval gate runs on agent-affecting changes.
