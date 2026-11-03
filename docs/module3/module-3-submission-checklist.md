# Module 3 Lab Submission Checklist

**Prepared:** 2026-11-02. Nothing was rerun to prepare this package.
**Package:** `eval/evidence/submission/`. All paths below are relative to it unless they start with `docs/`. `MANIFEST.json` lists a SHA-256 for every packaged file.

## Transcript format and redaction

- Every `.jsonl` transcript is packaged as a `.json` file. The original `.jsonl` files elsewhere in the repository are unchanged.
- Each converted file is one JSON object with:
  - `source_file` and `source_sha256`, identifying the original;
  - `record_count`;
  - `records`: every JSONL line, parsed, in the original order.
- **Redaction:** in the packaged copies only, the host username in file paths is replaced with `[REDACTED_USER]`. Each affected file records this in a `redaction` field.
  - Nothing else in the records was changed: record structure, tool calls, tool results, usage figures and evaluation results are identical to the originals.
  - The build checked each copy record-for-record against its source, after applying the same replacement to the source.

## 1. Calibration pair (induced fault → fix)

| Item | Path | Status |
|---|---|---|
| Before-fix transcript (`CAL-BEFORE-001`) | `01-calibration/before-fix/before-fix-tester-transcript.json` | Present. The `init` tool grant has no Bash. |
| Before-fix run manifest and deterministic report | `01-calibration/before-fix/before-fix-run.json`, `before-fix-deterministic-report.json` | Present. FAIL 3/6. |
| After-fix transcript (`CAL-AFTER-001`) | `01-calibration/after-fix/after-fix-tester-transcript.json` | Present. The `init` tool grant includes Bash. |
| After-fix run manifest and deterministic report | `01-calibration/after-fix/after-fix-run.json`, `after-fix-deterministic-report.json` | Present. FAIL 5/6 on execution health (59,566 tokens). All five functional checks pass. |
| Root cause, fix and configuration provenance | `05-documentation/calibration-log.md` (Induced Failure, Root Cause, Fix) | Present |

## 2. Deterministic checks before rubric scoring

| Item | Path | Status |
|---|---|---|
| Gate logic, original lint profile | `04-configuration-and-evaluation/evaluation-original-unchanged/eval/test_rubric_suite.py` | Present. The judge runs only after a gate PASS. |
| Gate logic, unit-test profile | `04-configuration-and-evaluation/evaluation-created-after-calibration/eval/test_rubric_suite_unit_tests.py` | Present, with the same gating rule. |
| Gate failure produces no rubric score | `02-regression/distinct-attempt-1-CAL-REGRESSION-DISTINCT-001/distinct-regression-rubric-report.json` | Present: `"Deterministic gate failed; judge not called."` |

## 3. Successful after-fix evaluation

| Item | Path | Status |
|---|---|---|
| `CAL-REGRESSION-001` (lint) | `02-regression/lint-attempt-2-CAL-REGRESSION-001/` (transcript, run, `regression-fresh-deterministic-report.json`, `regression-rubric-report.json`) | Present. PASS 6/6, rubric 12/12, 39,423 tokens. |

## 4. Regression on a distinct, previously passing development task

| Item | Path | Status |
|---|---|---|
| Lint regression attempt 1 (`DEV-LINT-001`) | `02-regression/lint-attempt-1-DEV-LINT-001/` | Present. FAIL 5/6. Not distinct. |
| Distinct attempt 1 (`CAL-REGRESSION-DISTINCT-001`) | `02-regression/distinct-attempt-1-CAL-REGRESSION-DISTINCT-001/` | Present. FAIL 5/6 (89,854 tokens). Rubric not run. Includes the direct `npm run test` output (15/15, exit 0). |
| **Distinct attempt 2 (`CAL-REGRESSION-DISTINCT-002`)** | `02-regression/distinct-attempt-2-CAL-REGRESSION-DISTINCT-002-PASS/` | Present. **PASS 6/6** (22,094 tokens, 10,140 ms, 0 denials). **Rubric 11/12** (4/4/3). The Tester reported 15/15 passing, exit 0. |
| Historical baseline | `docs/iteration-log.md` (Module 3.1 Runs 1 and 2: "PASS — 15/15") | Documentation only. See Known limitations. |
| Write-up | `05-documentation/module-3-regression-summary.md`; `05-documentation/calibration-log.md` (Attempts 3 and 4) | Present |

## 5. Six holdout runs (fresh conversations, no tuning between them)

| Holdout | Path | Session | Notes |
|---|---|---|---|
| HO-01 | `03-holdouts/HO-01/HO-01-transcript.json` | `67c33dd5-…` | Post-calibration. 5 retrieval attempts denied in plan mode. The exploratory run from before calibration is kept as `historical-HO-01-exploratory-pre-calibration-transcript.json`. |
| HO-02 | `03-holdouts/HO-02/HO-02-transcript.json` | `a3ba9d68-…` | Stopped at the human-approval gate. |
| HO-03 | `03-holdouts/HO-03/HO-03-transcript.json` | `e0956ea3-…` | Execution run. The plan-mode planning session is `supplementary-HO-03-planning-session-transcript.json`. |
| HO-04 | `03-holdouts/HO-04/HO-04-transcript.json` | `e6e57424-…` | |
| HO-05 | `03-holdouts/HO-05/HO-05-transcript.json` | `8f402443-…` | Resumed session (3 `init` records). |
| HO-06 | `03-holdouts/HO-06/HO-06-transcript.json` | `28b78e2c-…` | |
| Frozen task definitions | `03-holdouts/holdout-task-set.md` | — | Copy. The original `docs/holdout-task-set.md` is unchanged. |

## 6. Measurements for each holdout

| Item | Path | Status |
|---|---|---|
| Duration, tokens, denials, verdict | `05-documentation/calibration-log.md` (Holdout run summary) | Present |
| Assertion-level results | `05-documentation/calibration-log.md` (Assertion-level results) | Present: 10 PASS, 2 FAIL, 4 BLOCKED, 5 NOT VERIFIED out of 21. Based on transcript inspection. |

## 7. Orchestration configuration and evaluation files

| Category | Path |
|---|---|
| **Modified during calibration** | `04-configuration-and-evaluation/modified-during-calibration/.claude/agents/tester.md` (Bash restored) |
| Least-privilege justification and remaining orchestration-layer risk | `05-documentation/module-3-reflection.md` (section 4); `05-documentation/calibration-log.md` ("Least-privilege assessment of the fix"). These are analysis only: the proposed restrictions are not implemented. |
| Unchanged reference configuration | `04-configuration-and-evaluation/unchanged-reference/` (`CLAUDE.md`, the other four agent definitions, `mcp/roles.allowlist.json`) |
| Original evaluation harness (unchanged) | `04-configuration-and-evaluation/evaluation-original-unchanged/` (`eval/test_deterministic.py`, `test_rubric_suite.py`, `rubric.json`, `test_harness_selftest.py`, `README.md`; `parse_agent_execution.py`, `evaluate_HO-01_retrieval_miss.py`) |
| **Created after calibration** (2026-11-02) | `04-configuration-and-evaluation/evaluation-created-after-calibration/eval/` (`test_deterministic_unit_tests.py`, `test_rubric_suite_unit_tests.py`, `rubric-unit-tests.json`) |

## 8. Written documentation

| Item | Path |
|---|---|
| Calibration log | `05-documentation/calibration-log.md` |
| Reflection answers | `05-documentation/module-3-reflection.md` |
| Regression summary | `05-documentation/module-3-regression-summary.md` |
| This checklist | `05-documentation/module-3-submission-checklist.md` |

## Known limitations

These are documented in the calibration log, the reflection and the regression summary.

- **Historical baseline:** the "previously passing" result for the distinct task is recorded only in `docs/iteration-log.md`. No Module 3.1 transcript or test output exists in the repository.
- **Before-fix configuration file:** the temporary faulted `tester.md` was never committed. According to the author's host git history, the file was committed only in `2c4f917` and `ff643f9`, so it can't be recovered. The faulted grant is shown at run time by the before-fix transcript's `init` record.
- **Narrowed prompt:** the distinct regression passed with a prompt limited to one test command. The Tester's default workflow (attempt 1) used 89,854 tokens.
- **Evaluator profile:** the unit-test evaluator was written after calibration, reusing the original logic and thresholds.
- **Holdout verification:** holdout verdicts come from the orchestrator's reports and from transcript inspection. No evaluator script was run on them.
- **MCP retrieval:** retrieval was denied by plan mode in every post-calibration holdout, so HO-01 fails, and HO-06's classification-ceiling check was never exercised.
- **HO-05** was a resumed session.
- **Sample size:** the passing lint regression and the passing distinct regression are each a single run.

## Before submitting

1. **Confirm the official requirements.** The lab instructions are not in the repository. Confirm the required file list and the upload format (`.json` vs `.jsonl`).
2. **Commit and push** to `module-3-calibration-lab` from the host. This package has not been committed.
3. **Privacy note:**
   - The packaged transcript copies are redacted for the host username. The original `.jsonl` transcripts under `eval/evidence/` and `module-3.3-evaluation-harness/` are unchanged and still contain it, along with the session `init` metadata naming the connected integrations.
   - A scan of the package found no API keys, tokens, cookies, private keys or passwords. The only match was the `USER:PASSWORD` placeholder from `tracker-api/.env.example`.
4. `eval/evidence/calibration/holdout/HO-03.jsonlls` is a stray empty file. It is not packaged.
