"""Run the full harness across a holdout transcript directory.

Run from the repository root:
    python3 eval/run_holdout.py .eval-artifacts/runs/holdout
"""

import os
import sys

from test_deterministic import collect_results
from test_rubric_suite import collect_rubric_results


def run_holdout(holdout_dir):
    transcripts = sorted(
        os.path.join(holdout_dir, f)
        for f in os.listdir(holdout_dir)
        if f.endswith(".json")
    )
    n_tasks = len(transcripts)
    det_passed = det_total = 0
    failing_checks = {}  # check name -> number of tasks it failed on
    rubric_score = rubric_max = 0
    dims_passed = dims_total = 0
    fully_passing = 0

    for path in transcripts:
        det = collect_results(path)
        task_det_passed = sum(r["passed"] for r in det)
        det_passed += task_det_passed
        det_total += len(det)
        for r in det:
            if not r["passed"]:
                failing_checks[r["check"]] = failing_checks.get(r["check"], 0) + 1

        if task_det_passed != len(det):
            # The gate from the rubric section: a task that fails its
            # deterministic floor does not get a rubric score.
            continue

        rub = collect_rubric_results(path)
        dims = [r for r in rub if r["check"] != "rubric:aggregate"]
        rubric_score += sum(r["score"] for r in dims)
        rubric_max += 4 * len(dims)
        dims_passed += sum(r["passed"] for r in dims)
        dims_total += len(dims)
        aggregate = next(r for r in rub if r["check"] == "rubric:aggregate")
        if aggregate["passed"]:
            fully_passing += 1

    print(f"Holdout set size: {n_tasks} tasks")
    print(f"Deterministic checks: {det_passed} / {det_total} passing across all tasks")
    if failing_checks:
        print("Deterministic checks failing on at least one task:")
        for name, count in sorted(failing_checks.items()):
            print(f" - {name}: failed on {count} task(s)")
    else:
        print("All deterministic checks passed on every holdout task.")
    print(
        f"Rubric suite: {rubric_score} / {rubric_max} aggregate, "
        f"{dims_passed} / {dims_total} dimension checks passing threshold"
    )
    print(f"Tasks passing both layers fully: {fully_passing} / {n_tasks}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: run_holdout.py <holdout_transcripts_dir>")
        sys.exit(2)
    run_holdout(sys.argv[1])
