"""Snapshot or compare deterministic results for development transcripts.

Run from the repository root:
    python3 eval/run_regression.py snapshot .eval-artifacts/runs/dev
    python3 eval/run_regression.py compare .eval-artifacts/runs/dev
"""

import json
import os
import sys

from test_deterministic import collect_results

BASELINE_PATH = ".eval-artifacts/baseline-dev.json"


def transcripts(dev_dir):
    return sorted(
        os.path.join(dev_dir, f)
        for f in os.listdir(dev_dir)
        if f.endswith(".json")
    )


def snapshot(dev_dir):
    """Record current pass/fail of every check on every dev task as a baseline."""
    baseline = {}
    for path in transcripts(dev_dir):
        task = os.path.basename(path)
        baseline[task] = {r["check"]: r["passed"] for r in collect_results(path)}
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"baseline written to {BASELINE_PATH} for {len(baseline)} dev task(s)")


def compare(dev_dir):
    """Compare current results to the baseline; report regressions and fixes."""
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    regressions, fixes = [], []
    for path in transcripts(dev_dir):
        task = os.path.basename(path)
        current = {r["check"]: r["passed"] for r in collect_results(path)}
        base = baseline.get(task, {})
        for check, now_passes in current.items():
            was_passing = base.get(check)
            if was_passing is True and not now_passes:
                regressions.append(f"{task}: {check} passed before, fails now")
            elif was_passing is False and now_passes:
                fixes.append(f"{task}: {check} failed before, passes now")

    print(f"Development tasks compared: {len(baseline)}")
    print(f"Fixes confirmed (failed before, pass now): {len(fixes)}")
    for line in fixes:
        print(f" + {line}")
    if regressions:
        print(f"REGRESSIONS ({len(regressions)}):")
        for line in regressions:
            print(f" - {line}")
        return 1
    print("No regressions: every check that passed before calibration still passes.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("snapshot", "compare"):
        print("usage: run_regression.py [snapshot|compare] <dev_transcripts_dir>")
        sys.exit(2)
    mode, dev_dir = sys.argv[1], sys.argv[2]
    if mode == "snapshot":
        snapshot(dev_dir)
    else:
        sys.exit(compare(dev_dir))
