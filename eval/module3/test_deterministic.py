#!/usr/bin/env python3
"""Evidence-based deterministic checks for a MarketRadar development lint run.

Run: python3 eval/test_deterministic.py eval/evidence/development-run.json
Manifest is evidence metadata, NOT proof by itself: every role must have a real
Claude Code JSONL transcript with a system init and final result.
"""
import argparse
import json
import sys
from pathlib import Path

# Module 4.1 migration: harness relocated to eval/module3/, which is now the harness root.
ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT / "module-3.3-evaluation-harness"))
from parse_agent_execution import parse_execution

ALLOWED = {"Read", "Grep", "Glob", "Bash", "mcp__retrieval__retrieve"}
FORBIDDEN = {"Edit", "Write", "NotebookEdit", "mcp__storage__write_entry", "mcp__storage__update_entry", "mcp__storage__delete_entry"}


def check(name, risk, passed, explanation):
    return {"check": name, "failure_mode": risk, "passed": bool(passed), "explanation": explanation}


def load_manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("executions"), list):
        raise ValueError("Manifest must contain an executions list")
    return path, manifest


def evaluate(path):
    path, manifest = load_manifest(path)
    checks = []
    executions = manifest["executions"]
    roles = [e.get("role") for e in executions if isinstance(e, dict)]
    expected = manifest.get("expected_roles")
    valid_route = expected == ["tester"] and roles == expected and len(executions) == 1
    checks.append(check("routing_order", "Routing misfire / missing agent", valid_route,
                        f"Expected development lint route ['tester']; observed {roles!r}."))

    parsed = []
    errors = []
    for entry in executions:
        try:
            if not isinstance(entry, dict):
                raise ValueError("Execution entry must be an object")
            relative = entry.get("transcript")
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
                raise ValueError("Transcript must be a relative path")
            transcript = (path.parent / relative).resolve()
            if not transcript.is_relative_to(ROOT):
                raise ValueError("Transcript must be inside the repository")
            parsed.append(parse_execution(transcript))
        except (OSError, ValueError, TypeError) as error:
            errors.append(str(error))
    transcripts_valid = len(parsed) == len(executions) == 1 and not errors and bool(parsed[0].get("session_id"))
    checks.append(check("real_transcript_present", "Fabricated or missing execution evidence", transcripts_valid,
                        "Parsed Claude Code init/result records for all listed executions." if transcripts_valid else f"Transcript problems: {errors!r}."))

    if not transcripts_valid:
        checks.extend([
            check("tool_authorization", "Over-broad tool grants", False, "Cannot inspect verified transcript."),
            check("lint_command_evidence", "Missing tool/output evidence", False, "Cannot inspect verified transcript."),
            check("no_source_writes", "Tester modifying application", False, "Cannot inspect verified transcript."),
            check("execution_health", "Failed or incomplete execution", False, "Cannot inspect verified transcript."),
        ])
        return {"run_id": manifest.get("run_id"), "checks": checks, "passed": False}

    execution = parsed[0]
    grants = execution.get("available_tools")
    calls = execution.get("tool_calls") or []
    grants_valid = (isinstance(grants, list) and len(grants) == len(set(grants))
                    and set(grants) == ALLOWED)
    actual_valid = all(c.get("tool_name") in ALLOWED for c in calls)
    no_denials = execution.get("permission_denials") == []
    checks.append(check("tool_authorization", "Unauthorized tool call or over-broad grant",
                        grants_valid and actual_valid and no_denials,
                        f"Expected grants {sorted(ALLOWED)}; observed {grants!r}; actual calls {[c.get('tool_name') for c in calls]!r}; permission denials {execution.get('permission_denials')!r}."))

    bash_calls = [c for c in calls if c.get("tool_name") == "Bash"]
    lint_calls = [c for c in bash_calls if isinstance(c.get("arguments"), dict)
                  and "npm run lint" in str(c["arguments"].get("command", ""))]
    observed = [c for c in lint_calls if c.get("response_received") is True
                and c.get("response") is not None and c.get("is_error") is not None]
    checks.append(check("lint_command_evidence", "Unverified lint report / missing tool response", bool(observed),
                        f"Observed {len(observed)} lint Bash call(s) with returned tool evidence out of {len(lint_calls)} matching call(s)."))

    no_writes = all(c.get("tool_name") not in FORBIDDEN for c in calls)
    checks.append(check("no_source_writes", "Tester modifying application or storage", no_writes,
                        "No prohibited write tools invoked." if no_writes else "Prohibited write tool invoked."))

    duration = execution.get("duration_ms")
    usage = execution.get("token_usage") or {}
    keys = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    token_values = [usage.get(k) for k in keys]
    valid_tokens = all(type(v) is int and v >= 0 for v in token_values)
    token_total = sum(token_values) if valid_tokens else None
    health = (execution.get("status") == "success" and execution.get("is_error") is False
              and type(duration) in (int, float) and 0 <= duration <= 180000
              and valid_tokens and token_total <= 40000)
    checks.append(check("execution_health", "Failed execution / runaway latency or token cost", health,
                        f"status={execution.get('status')!r}, duration_ms={duration!r} (limit 180000), tokens={token_total!r} (limit 40000; includes cache tokens)."))

    return {"run_id": manifest.get("run_id"), "checks": checks,
            "passed": all(c["passed"] for c in checks)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"Evaluation setup error: {error}\n")
    report = json.dumps(result, indent=2)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
