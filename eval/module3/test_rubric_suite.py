#!/usr/bin/env python3
"""Deterministic-gated rubric evaluation. Requires Claude CLI for real judge.

python3 eval/test_rubric_suite.py eval/evidence/development-run.json
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from test_deterministic import evaluate, load_manifest, ROOT

RUBRIC_PATH = Path(__file__).with_name("rubric.json")


def validate_scores(judgment, rubric):
    if not isinstance(judgment, dict) or not isinstance(judgment.get("scores"), list):
        raise ValueError("Judge must return a JSON object with a scores list")
    scores = judgment["scores"]
    expected = {d["id"] for d in rubric["dimensions"]}
    if len(scores) != len(expected) or {s.get("dimension") for s in scores} != expected:
        raise ValueError("Judge scores must match every rubric dimension exactly once")
    for item in scores:
        if type(item.get("score")) is not int or not 1 <= item["score"] <= 4:
            raise ValueError("Every score must be an integer from 1 through 4")
        if not isinstance(item.get("justification"), str) or not item["justification"].strip():
            raise ValueError("Every dimension requires a nonempty justification")
    return scores


def judge_with_claude(prompt):
    try:
        proc = subprocess.run(["claude", "--print", "--output-format", "text", "--no-session-persistence", "--tools", ""],
                              input=prompt, capture_output=True, text=True, timeout=120, check=False)
    except FileNotFoundError as error:
        raise RuntimeError("Claude CLI not installed. Run rubric suite inside authenticated course container.") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Claude judge timed out after 120 seconds.") from error
    if proc.returncode:
        raise RuntimeError(f"Claude judge exited {proc.returncode}: {proc.stderr[:600]}")
    answer = proc.stdout.strip()
    try:
        return json.loads(answer)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", answer, re.S)
        if match:
            return json.loads(match.group(1))
        raise ValueError("Judge did not return valid JSON; raw response not treated as a score")


def run(manifest_path, judge=judge_with_claude):
    deterministic = evaluate(manifest_path)
    result = {"deterministic": deterministic, "rubric_ran": False, "rubric": None}
    if not deterministic["passed"]:
        result["reason"] = "Deterministic gate failed; judge not called."
        return result
    manifest_path, manifest = load_manifest(manifest_path)
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    outputs = []
    # Transcript must be parsed, not trusted based on manifest claims.
    sys.path.insert(0, str(ROOT / "module-3.3-evaluation-harness"))
    from parse_agent_execution import parse_execution
    for entry in manifest["executions"]:
        path = (manifest_path.parent / entry["transcript"]).resolve()
        parsed = parse_execution(path)
        lint_evidence = [c for c in parsed["tool_calls"] if c.get("tool_name") == "Bash"
                         and "npm run lint" in str((c.get("arguments") or {}).get("command", ""))]
        outputs.append({"role": entry["role"], "final_response": parsed["final_response"],
                        "lint_tool_evidence": lint_evidence})
    prompt = ("You are an independent judge evaluating a MarketRadar lint-verification summary. "
              "Score ONLY from the recorded command evidence and substantive agent output. "
              "Do not assume a command succeeded merely because an agent said so. "
              "If evidence is insufficient, assign a lower score and explain why. "
              "Return ONLY valid JSON of shape: "
              "{\"scores\":[{\"dimension\":\"dimension_id\",\"score\":1,\"justification\":\"reason\"}]}. "
              "Include exactly one score for every rubric dimension.\n"
              "RUBRIC:\n" + json.dumps(rubric, indent=2) + "\n"
              "DEVELOPMENT TASK:\n" + str(manifest.get("task_description", "")) + "\n"
              "RECORDED EVIDENCE:\n" + json.dumps(outputs, indent=2))
    judgment = judge(prompt)
    scores = validate_scores(judgment, rubric)
    thresholds = {d["id"]: d["pass_threshold"] for d in rubric["dimensions"]}
    enriched = [{**s, "pass_threshold": thresholds[s["dimension"]],
                 "passed": s["score"] >= thresholds[s["dimension"]]} for s in scores]
    total = sum(s["score"] for s in enriched)
    passed = total >= rubric["overall_pass_threshold"] and all(s["passed"] for s in enriched)
    result["rubric_ran"] = True
    result["rubric"] = {"scores": enriched, "total": total, "maximum": len(enriched) * 4,
                        "overall_pass_threshold": rubric["overall_pass_threshold"], "passed": passed}
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
