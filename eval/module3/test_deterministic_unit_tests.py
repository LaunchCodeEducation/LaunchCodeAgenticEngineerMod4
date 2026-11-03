#!/usr/bin/env python3
"""Deterministic checks for a Tester-only *unit-test* development run.

Separate profile for the distinct regression task (tracker-api Vitest suite).
The original lint profile, eval/test_deterministic.py, is NOT modified. This
profile reuses its tool-grant sets, manifest loader and check() helper, and
keeps the same execution-health limits (180,000 ms, 40,000 tokens including
cache tokens). The only difference is that `lint_command_evidence` is replaced
by `test_command_evidence`.

Run: python3 eval/test_deterministic_unit_tests.py <run.json> [--output report.json]
"""
import argparse
import json
import sys
from pathlib import Path

from test_deterministic import ALLOWED, FORBIDDEN, ROOT, check, load_manifest

sys.path.insert(0, str(ROOT / "module-3.3-evaluation-harness"))
from parse_agent_execution import parse_execution

# Same limits as the original lint profile (eval/test_deterministic.py, eval/README.md).
DURATION_LIMIT_MS = 180000
TOKEN_LIMIT = 40000
TEST_COMMAND_MARKERS = ("npm run test", "npm test", "vitest run")


def is_test_command(call):
    if call.get("tool_name") != "Bash" or not isinstance(call.get("arguments"), dict):
        return False
    command = str(call["arguments"].get("command", ""))
    return any(marker in command for marker in TEST_COMMAND_MARKERS)


def evaluate(path):
    path, manifest = load_manifest(path)
    checks = []
    executions = manifest["executions"]
    roles = [e.get("role") for e in executions if isinstance(e, dict)]
    expected = manifest.get("expected_roles")
    valid_route = expected == ["tester"] and roles == expected and len(executions) == 1
    checks.append(check("routing_order", "Routing misfire / missing agent", valid_route,
                        f"Expected unit-test route ['tester']; observed {roles!r}."))

    parsed, errors = [], []
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
        for name in ("tool_authorization", "test_command_evidence", "no_source_writes", "execution_health"):
            checks.append(check(name, "Cannot inspect verified transcript", False, "Cannot inspect verified transcript."))
        return {"run_id": manifest.get("run_id"), "profile": "unit-tests", "checks": checks, "passed": False}

    execution = parsed[0]
    grants = execution.get("available_tools")
    calls = execution.get("tool_calls") or []
    grants_valid = isinstance(grants, list) and len(grants) == len(set(grants)) and set(grants) == ALLOWED
    actual_valid = all(c.get("tool_name") in ALLOWED for c in calls)
    no_denials = execution.get("permission_denials") == []
    checks.append(check("tool_authorization", "Unauthorized tool call or over-broad grant",
                        grants_valid and actual_valid and no_denials,
                        f"Expected grants {sorted(ALLOWED)}; observed {grants!r}; actual calls {[c.get('tool_name') for c in calls]!r}; permission denials {execution.get('permission_denials')!r}."))

    test_calls = [c for c in calls if is_test_command(c)]
    observed = [c for c in test_calls if c.get("response_received") is True
                and c.get("response") is not None and c.get("is_error") is not None]
    checks.append(check("test_command_evidence", "Unverified test report / missing tool response", bool(observed),
                        f"Observed {len(observed)} test-command Bash call(s) with returned tool evidence out of {len(test_calls)} matching call(s)."))

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
              and type(duration) in (int, float) and 0 <= duration <= DURATION_LIMIT_MS
              and valid_tokens and token_total <= TOKEN_LIMIT)
    checks.append(check("execution_health", "Failed execution / runaway latency or token cost", health,
                        f"status={execution.get('status')!r}, duration_ms={duration!r} (limit {DURATION_LIMIT_MS}), tokens={token_total!r} (limit {TOKEN_LIMIT}; includes cache tokens)."))

    return {"run_id": manifest.get("run_id"), "profile": "unit-tests", "checks": checks,
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
