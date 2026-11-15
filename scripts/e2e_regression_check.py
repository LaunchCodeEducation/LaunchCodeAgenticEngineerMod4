#!/usr/bin/env python3
"""End-to-end regression check for the ADR-003 conversion (no model calls).

Scores orchestrator transcripts with the deterministic assertions written in
docs/holdout-task-set.md plus seam checks for the integrated citation step, and
compares new runs against a baseline so "everything that passed before still
passes" can be shown, not asserted.

Usage:
    python scripts/e2e_regression_check.py --runs <dir-of-new-transcripts> \
        --baseline <dir-of-baseline-transcripts> --report <path.json>

Transcripts are matched by name: E2E-HO-01.json is compared with HO-01.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_citations import citation_list  # noqa: E402

VALID_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_key(v, key)
            if found is not None:
                return found
    return None


def retrieval_rows(event):
    result = event.get("result")
    rows = result.get("results") if isinstance(result, dict) else None
    return rows if isinstance(rows, list) else []


def check_transcript(data: dict, task_id: str) -> list[tuple[str, bool, str]]:
    events = [e for e in data.get("events", []) if isinstance(e, dict)]
    outputs = [e for e in events if e.get("type") == "subagent"]
    tools = [e for e in events if e.get("type") == "tool_call"]
    ran = [e.get("role") for e in outputs]
    expected = data.get("expected_path") or []
    results = []

    def add(name, ok, detail):
        results.append((name, bool(ok), detail))

    # Generic workflow checks (every task)
    add("run_completed", bool(outputs), f"{len(outputs)} role output(s)")
    add("role_order_matches_expected_path", not expected or ran == list(expected),
        f"ran {ran}, expected {list(expected)}")

    bad_shape = []
    for e in outputs:
        doc = e.get("output_document")
        if not (isinstance(doc, dict) and isinstance(doc.get("summary"), str)
                and isinstance(doc.get("citation_list"), list)):
            bad_shape.append(e.get("role"))
    add("output_schema_summary_and_citation_list", not bad_shape,
        "all outputs have summary (str) and citation_list (list)" if not bad_shape else f"bad: {bad_shape}")

    retrieved = {r.get("source_document") for e in tools if e.get("tool") == "retrieve" for r in retrieval_rows(e)
                 if isinstance(r, dict)}
    invented = [(e.get("role"), c) for e in outputs
                for c in ((e.get("output_document") or {}).get("citation_list") or []) if c not in retrieved]
    add("no_invented_citations", not invented,
        "every citation appeared in this run's retrieval results" if not invented else f"invented: {invented[:3]}")

    # Seam check: the orchestrator actually wired in the deterministic step
    pending, mismatches = {}, []
    for e in events:
        role = e.get("role")
        if not role:
            continue
        if e.get("type") == "tool_call":
            pending.setdefault(role, []).append(e)
        elif e.get("type") == "subagent":
            expected_list = citation_list(pending.get(role, []))
            got = (e.get("output_document") or {}).get("citation_list")
            if got != expected_list:
                mismatches.append((role, got, expected_list))
            pending[role] = []
    add("citation_list_set_by_deterministic_step", not mismatches,
        "every citation_list equals the rule over that role's own retrievals"
        if not mismatches else f"{len(mismatches)} mismatch(es), first: {mismatches[0]}")

    # Task-specific assertions from docs/holdout-task-set.md
    if task_id == "HO-01":
        planner_retrieves = [e for e in tools if e.get("tool") == "retrieve" and e.get("role") == "planner"]
        add("HO-01.1 planner called retrieve", bool(planner_retrieves), f"{len(planner_retrieves)} call(s)")
        rows = [r for e in planner_retrieves for r in retrieval_rows(e)]
        missing = [r for r in rows if not (isinstance(r, dict) and "source_document" in r and "chunk_index" in r)]
        add("HO-01.2 results have source_document and chunk_index", rows and not missing,
            f"{len(rows)} result(s), {len(missing)} missing a field")
        planner_cites = [c for e in outputs if e.get("role") == "planner"
                         for c in ((e.get("output_document") or {}).get("citation_list") or [])]
        add("HO-01.3 planner citations all retrieved", all(c in retrieved for c in planner_cites),
            f"planner cited {planner_cites}")
    if task_id == "HO-02":
        add("HO-02.1 reviewer ran", "reviewer" in ran, f"roles: {ran}")
        add("HO-02.2 exact order", ran == ["planner", "implementer", "reviewer", "tester"], f"roles: {ran}")
        writes = [e for e in tools if e.get("tool") == "write_entry" and e.get("role") == "implementer"]
        classes = [find_key(w, "classification") for w in writes]
        add("HO-02.3 one implementer write_entry with valid classification",
            len(writes) == 1 and all(c in VALID_CLASSIFICATIONS for c in classes),
            f"{len(writes)} write(s), classification(s) {classes}")
    return results


def task_id_for(name: str) -> str:
    stem = Path(name).stem.replace("E2E-", "")
    return stem if stem.startswith("HO-") else stem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    runs = sorted(Path(args.runs).glob("*.json"))
    if not runs:
        print(f"ERROR: no transcripts in {args.runs}")
        return 1

    report, regressions = [], 0
    for path in runs:
        tid = task_id_for(path.name)
        new = dict((n, (ok, d)) for n, ok, d in check_transcript(json.loads(path.read_text(encoding="utf-8")), tid))
        base_path = Path(args.baseline) / f"{tid}.json"
        base = {}
        if base_path.exists():
            base = dict((n, (ok, d)) for n, ok, d in check_transcript(json.loads(base_path.read_text(encoding="utf-8")), tid))
        duration = json.loads(path.read_text(encoding="utf-8")).get("duration_seconds")
        print(f"\n{path.name}  (baseline: {base_path.name if base else 'none'})  "
              f"duration {f'{duration}s' if duration is not None else 'n/a'}")
        for name, (ok, detail) in new.items():
            before = base.get(name, (None, ""))[0]
            status = "PASS" if ok else "FAIL"
            note = ""
            if before is True and not ok:
                note = "  <-- REGRESSION"
                regressions += 1
            elif before is False and ok:
                note = "  (fixed: failed before)"
            elif before is None:
                note = "  (no baseline)"
            print(f"  {status}  {name}: {detail}{note}")
            report.append({"transcript": path.name, "check": name, "passed": ok, "baseline_passed": before, "detail": detail})

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps({"regressions": regressions, "results": report}, indent=2), encoding="utf-8")
    failed = sum(1 for r in report if not r["passed"])
    print(f"\n{len(report) - failed}/{len(report)} checks passed; regressions vs baseline: {regressions}")
    return 1 if regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
