"""Rubric-scored suite checks for Module 3 orchestration runs.

Run from the repository root:
    
    python3 eval/test_rubric_suite.py eval/evidence/DEV-appt-status.json
"""

import json
import sys
import subprocess

from harness_deterministic import run_all_checks, load_json

RUBRIC_PATH = "eval/rubric.json"


def load_rubric(path):
    with open(path) as f:
        return json.load(f)


def call_judge(prompt):
    """Send a prompt to the agent-as-judge through Claude Code; return reply text.

    The container may have no internet egress, so the judge runs through Claude
    Code in print mode rather than calling a public model API directly.
    """
    completed = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"judge invocation failed: {completed.stderr.strip()}")
    envelope = json.loads(completed.stdout)
    return envelope["result"]


def parse_score(reply):
    """Extract the first JSON object from the judge's reply.

    Uses raw_decode so that curly braces inside string values (e.g. a
    justification that mentions a dict like STATUS_TRANSITIONS) do not
    break parsing the way naive brace-counting does.
    """
    start = reply.find("{")
    if start == -1:
        raise ValueError(f"no JSON object found in judge reply: {reply[:200]}")
    try:
        obj, _ = json.JSONDecoder().raw_decode(reply[start:])
        return obj
    except json.JSONDecodeError as e:
        raise ValueError(f"could not parse JSON in judge reply: {reply[:200]}") from e


def build_judge_prompt(dimension, transcript_text):
    """Compose the instruction the judge receives for one dimension."""
    return (
        "You are scoring the output of a multi-agent software workflow against "
        "one quality dimension. Read the run transcript and the dimension "
        "definition below, then score the output from 1 to 4 using the level "
        "descriptions. Return only a JSON object with the fields "
        '"dimension", "score" (an integer from 1 to 4), and "justification" '
        "(one or two sentences). Return nothing else.\n\n"
        f"DIMENSION: {dimension['name']}\n"
        f"WHAT IT MEASURES: {dimension['description']}\n"
        f"LEVELS:\n{json.dumps(dimension['levels'], indent=2)}\n\n"
        f"RUN TRANSCRIPT:\n{transcript_text}\n"
    )


def check_dimension(dimension, transcript_text):
    reply = call_judge(build_judge_prompt(dimension, transcript_text))
    score_obj = parse_score(reply)
    score = int(score_obj["score"])
    justification = score_obj.get("justification", "")
    passed = score >= dimension["pass_threshold"]
    return {
        "check": f"rubric:{dimension['name']}",
        "failure_mode": "quality (rubric)",
        "passed": passed,
        "score": score,
        "message": f"scored {score}/4 (needs {dimension['pass_threshold']}). {justification}",
    }


def check_aggregate(dimension_results, overall_threshold):
    total = sum(r["score"] for r in dimension_results)
    passed = total >= overall_threshold
    return {
        "check": "rubric:aggregate",
        "failure_mode": "quality (rubric)",
        "passed": passed,
        "message": f"total {total} (needs {overall_threshold}).",
    }


def collect_rubric_results(transcript_path):
    """Score every rubric dimension and return the structured results unprinted."""
    rubric = load_rubric(RUBRIC_PATH)
    transcript = load_json(transcript_path)
    transcript_text = json.dumps(transcript, indent=2)
    dimension_results = [check_dimension(d, transcript_text) for d in rubric["dimensions"]]
    return dimension_results + [
        check_aggregate(dimension_results, rubric["overall_pass_threshold"])
    ]


def run_rubric_suite(transcript_path):
    # Gate: the rubric suite runs only if the deterministic checks all pass.
    if run_all_checks(transcript_path) != 0:
        print("\nDeterministic checks failed; skipping the rubric suite.")
        print("Fix the deterministic failures first. A rubric score on a malformed run is not meaningful.")
        return 1

    print("\nRunning rubric suite (each dimension is one model call)...\n")
    results = collect_rubric_results(transcript_path)
    passed = sum(r["passed"] for r in results)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"[{mark}] {r['check']}: {r['message']}")
    print(f"\n{passed}/{len(results)} rubric checks passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: test_rubric_suite.py <transcript_path>")
        sys.exit(2)
    sys.exit(run_rubric_suite(sys.argv[1]))
