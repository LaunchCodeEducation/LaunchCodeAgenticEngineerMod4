"""Analyze routing problems across holdout transcripts.

Run from the repository root:
    python3 eval/analyze_routing.py .eval-artifacts/runs/holdout
"""

import os
import sys
from collections import Counter

from test_deterministic import load_json


def transcripts(holdout_dir):
    return sorted(
        os.path.join(holdout_dir, f)
        for f in os.listdir(holdout_dir)
        if f.endswith(".json")
    )


def routing_problems(transcript):
    """Compare observed roles to the expected path and name each routing problem."""
    expected = transcript["expected_path"]
    observed = [e["role"] for e in transcript.get("events", []) if e.get("type") == "subagent"]
    problems = []
    for role in expected:
        if role not in observed:
            problems.append(f"skipped:{role}")
    for role in observed:
        if role not in expected:
            problems.append(f"unexpected:{role}")
    seen_in_order = [r for r in observed if r in expected]
    if seen_in_order != [r for r in expected if r in observed]:
        problems.append("out_of_order")
    return problems


def analyze(holdout_dir):
    counter = Counter()
    runs_with_problems = 0
    paths = transcripts(holdout_dir)
    for path in paths:
        problems = routing_problems(load_json(path))
        if problems:
            runs_with_problems += 1
        counter.update(problems)

    total = len(paths)
    print(f"Holdout runs analyzed: {total}; runs with a routing problem: {runs_with_problems}")
    if not counter:
        print("No routing problems found across the holdout set.")
        return

    print("Routing decisions implicated, most common first:")
    for problem, count in counter.most_common():
        print(f" {problem}: {count} run(s)")
    top, top_count = counter.most_common(1)[0]
    print(
        f"\nMost common: {top} ({top_count} of {total} runs). "
        "This is the routing decision to address."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: analyze_routing.py <holdout_transcripts_dir>")
        sys.exit(2)
    analyze(sys.argv[1])
