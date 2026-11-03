# Module 3.3 Exercise 1 — MarketRadar evaluation harness

## Evidence status

- `docs/holdout-task-set.md` is frozen; **do not edit it**.
- Prior HO-01 and HO-02 exploratory executions already happened. Do not describe them as untouched holdouts.
- `eval/evidence/synthetic-fixture.json` is **synthetic**, for testing harness wiring ONLY. It is not a development-run transcript or a real rubric judgment.
- A **real, authenticated development run remains necessary** for full Step 6 completion. No such transcript was present in the uploaded ZIP (raw JSONL files were excluded).

## Real development task

Use a familiar read-only task: "Tester: run `cd tracker-client && npm run lint`, summarize pass/fail, errors, warnings and recommended next action. Do not modify source files." A single Tester role is intentional; it is the actual orchestration path for this small verification-only development task. A full multi-agent implementation workflow requires its own distinct manifest and routing checks, not this development-lint profile.

Run the commands below from this worktree’s project root. The course image uses `WORKDIR /workspace`, and `setup.md` mounts the current directory there, so start the container from `~/marketradar-module-3.3-exercise-1-eval-harness`. Inside that container the same commands run from `/workspace`.

```bash
mkdir -p eval/evidence
claude --agent tester --permission-mode dontAsk --allowedTools 'Read,Grep,Glob,Bash,mcp__retrieval__retrieve' --disallowedTools 'Edit,Write,NotebookEdit' --no-session-persistence --print --verbose --output-format stream-json -p 'Development task, not a holdout: run cd tracker-client && npm run lint; report whether lint passed or failed, all important errors and warnings, and an actionable recommendation. Do not modify files. Include exact command and observed evidence.' > eval/evidence/development-tester.jsonl
```

Create `eval/evidence/development-run.json`:

```json
{
  "run_id": "DEV-LINT-001",
  "kind": "real_development_run",
  "task_description": "Run tracker-client npm lint and report results without modifying files.",
  "expected_roles": ["tester"],
  "executions": [{"role": "tester", "transcript": "development-tester.jsonl"}]
}
```

The transcript contains the actual Bash tool response, including lint stdout/stderr. For this read-only run there should be **no storage writes**. If a storage audit event occurs, copy the storage server audit log into `eval/evidence/` and review it. That log is `STORAGE_AUDIT_PATH`, which defaults to `/memory/storage-audit.log` in `mcp/storage/server.py`, and it is not part of this repository. The retrieval server does not write a separate audit file.

## Run evaluation

```bash
python3 eval/test_deterministic.py eval/evidence/development-run.json --output eval/evidence/development-deterministic-report.json
python3 eval/test_rubric_suite.py eval/evidence/development-run.json --output eval/evidence/development-rubric-report.json
```

The second command calls an authenticated `claude` CLI as an independent judge **only if** every deterministic check passes. It validates all scores and justifications, and enforces score >=3 for each Module 1 dimension and aggregate >=9/12. If the deterministic gate fails, preserve the failure; do not change thresholds just to pass.

## Offline fixture checks (not real evidence)

```bash
python3 -m unittest discover -s eval -p 'test_harness_selftest.py' -v
python3 eval/test_deterministic.py eval/evidence/synthetic-fixture.json
```

These prove parser/check/judge-interface wiring and gate behavior. Mock judge scores in self-tests do not count as quality scores. Raw real transcripts can contain secrets: review and redact before committing or uploading. The course upload requires only the four named files, plus written answers.

## Limitations

- The provided deterministic profile tests the **Tester-only lint development workflow**. It does not assert that a multi-agent implementation workflow executed.
- Agent role in the manifest is a declaration corroborated by a valid transcript and role-appropriate tool grants, not cryptographically authenticated role provenance; Claude JSONL does not explicitly contain a verified subagent-role field.
- A successful command tool call is not proof that the command exited zero; the rubric judge evaluates the reported lint outcome against tool evidence.
- Duration/token thresholds are development defaults (180 seconds, 40,000 tokens including cache tokens); preserve and report real failures rather than raising limits to pass.
