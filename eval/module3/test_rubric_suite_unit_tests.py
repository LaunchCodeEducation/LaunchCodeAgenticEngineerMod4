#!/usr/bin/env python3
"""Deterministic-gated rubric evaluation for the unit-test regression profile.

Reuses the original judge call and score validation from eval/test_rubric_suite.py
(unchanged). The judge runs ONLY if eval/test_deterministic_unit_tests.py passes.

python3 eval/test_rubric_suite_unit_tests.py <run.json> [--output report.json]
"""
import argparse
import json
import sys
from pathlib import Path

from test_deterministic import ROOT, load_manifest
from test_deterministic_unit_tests import evaluate, is_test_command
from test_rubric_suite import judge_with_claude, validate_scores

sys.path.insert(0, str(ROOT / "module-3.3-evaluation-harness"))
from parse_agent_execution import parse_execution

RUBRIC_PATH = Path(__file__).with_name("rubric-unit-tests.json")


def run(manifest_path, judge=judge_with_claude):
    deterministic = evaluate(manifest_path)
    result = {"deterministic": deterministic, "rubric_ran": False, "rubric": None}
    if not deterministic["passed"]:
        result["reason"] = "Deterministic gate failed; judge not called."
        return result
    manifest_path, manifest = load_manifest(manifest_path)
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    outputs = []
    for entry in manifest["executions"]:
        parsed = parse_execution((manifest_path.parent / entry["transcript"]).resolve())
        outputs.append({"role": entry["role"], "final_response": parsed["final_response"],
                        "test_tool_evidence": [c for c in parsed["tool_calls"] if is_test_command(c)]})
    prompt = ("You are an independent judge evaluating a MarketRadar unit-test verification summary. "
              "Score ONLY from the recorded command evidence and substantive agent output. "
              "Do not assume a command succeeded merely because an agent said so. "
              "If evidence is insufficient, assign a lower score and explain why. "
              "Return ONLY valid JSON of shape: "
              "{\"scores\":[{\"dimension\":\"dimension_id\",\"score\":1,\"justification\":\"reason\"}]}. "
              "Include exactly one score for every rubric dimension.\n"
              "RUBRIC:\n" + json.dumps(rubric, indent=2) + "\n"
              "DEVELOPMENT TASK:\n" + str(manifest.get("task_description", "")) + "\n"
              "RECORDED EVIDENCE:\n" + json.dumps(outputs, indent=2))
    scores = validate_scores(judge(prompt), rubric)
    thresholds = {d["id"]: d["pass_threshold"] for d in rubric["dimensions"]}
    enriched = [{**s, "pass_threshold": thresholds[s["dimension"]],
                 "passed": s["score"] >= thresholds[s["dimension"]]} for s in scores]
    total = sum(s["score"] for s in enriched)
    result["rubric_ran"] = True
    result["rubric"] = {"scores": enriched, "total": total, "maximum": len(enriched) * 4,
                        "overall_pass_threshold": rubric["overall_pass_threshold"],
                        "passed": total >= rubric["overall_pass_threshold"] and all(s["passed"] for s in enriched)}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.manifest)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Rubric evaluation error: {error}\n")
    report = json.dumps(result, indent=2)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    if not result["deterministic"]["passed"]:
        return 1
    return 0 if result["rubric"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
