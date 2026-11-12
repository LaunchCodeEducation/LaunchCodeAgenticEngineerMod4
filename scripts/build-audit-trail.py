#!/usr/bin/env python3
"""
Build a small combined audit trail from CI metadata and downloaded artifacts.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_text(path: Path, default=""):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--changed-files", default="")
    parser.add_argument("--touches-policy", default="false")
    parser.add_argument("--requires-governed-check", default="false")
    parser.add_argument("--policy-result", default="unknown")
    parser.add_argument("--governed-result", default="unknown")
    parser.add_argument("--review-result", default="unknown")
    parser.add_argument("--agent-affecting", default="false")
    parser.add_argument("--eval-result", default="unknown")
    parser.add_argument("--deterministic-outcome", default="unknown")
    parser.add_argument("--rubric-outcome", default="unknown")
    parser.add_argument("--artifacts", default="ci-artifacts")
    args = parser.parse_args()

    artifact_dir = Path(args.artifacts)

    policy_report = load_json(artifact_dir / "policy-report.json", {})
    governed_report = load_json(artifact_dir / "governed-file-report.json", {})
    review_audit = load_json(artifact_dir / "review-audit.json", {})
    review_output = load_text(artifact_dir / "review-output.md", "")
    deterministic_report = load_json(artifact_dir / "deterministic-report.json", {})
    rubric_report = load_json(artifact_dir / "rubric-report.json", {})

    trail = {
        "metadata": {
            "sha": args.sha,
            "event": args.event,
            "pull_request": args.pr,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "change_classification": {
            "changed_files": args.changed_files.split(),
            "touches_policy": args.touches_policy == "true",
            "requires_governed_check": args.requires_governed_check == "true",
            "agent_affecting": args.agent_affecting == "true",
        },
        "results": {
            "policy_gate": args.policy_result,
            "governed_file_gate": args.governed_result,
            "advisory_review": args.review_result,
            "eval_gate": args.eval_result,
            "eval_deterministic_step": args.deterministic_outcome,
            "eval_rubric_step_advisory": args.rubric_outcome,
        },
        "reports_present": {
            "policy_report": bool(policy_report),
            "governed_file_report": bool(governed_report),
            "review_audit": bool(review_audit),
            "review_output": bool(review_output),
            "deterministic_report": bool(deterministic_report),
            "rubric_report": bool(rubric_report),
        },
        "policy_report_summary": {
            "exitcode": policy_report.get("exitcode"),
            "tests": len(policy_report.get("tests", [])),
        },
        "governed_report_summary": {
            "exitcode": governed_report.get("exitcode"),
            "tests": len(governed_report.get("tests", [])),
        },
        "deterministic_report_summary": {
            "exitcode": deterministic_report.get("exitcode"),
            "tests": len(deterministic_report.get("tests", [])),
        },
        "rubric_report_summary": {
            "deterministic_precheck_passed": (rubric_report.get("deterministic") or {}).get("passed"),
            "rubric_ran": rubric_report.get("rubric_ran"),
            "rubric_passed": (rubric_report.get("rubric") or {}).get("passed"),
            "reason": rubric_report.get("reason"),
        },
        "review_audit": review_audit,
    }

    out = Path(f"ci-audit-trail-{args.sha}.json")
    out.write_text(json.dumps(trail, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
