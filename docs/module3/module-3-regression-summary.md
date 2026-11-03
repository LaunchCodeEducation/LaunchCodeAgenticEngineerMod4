# Module 3 Distinct Regression Summary

**Date:** 2026-11-02
**Runs:** `CAL-REGRESSION-DISTINCT-001` (attempt 1, FAIL) and `CAL-REGRESSION-DISTINCT-002` (final attempt, PASS)
**Status:** the final attempt **passed the deterministic gate (6/6) and the rubric (11/12)**. The distinct-regression requirement is **met, with one documented limitation:** the pre-calibration baseline is supported by documentation only.

Full details are in `docs/calibration-log.md`, under "Attempt 3" and "Attempt 4".

## 1. Historical baseline: documented, but no primary evidence found

| Candidate | Pre-calibration record | Primary evidence |
|---|---|---|
| Saved-search `maxPrice` validation (Module 3.1; the brief cites `d7c8444`, 2026-09-28) | `docs/iteration-log.md`, Module 3.1 Runs 1 and 2: "Tester verified … PASS — 15/15 tests passed." | None found. |
| Price-rescan regression tests (Module 2 Final Lab; the brief cites `0e336b4`, 2026-09-21) | `docs/iteration-log.md`: "All 3 tests passed." Self-reported, and not run through the Tester agent. | None found. |

Where primary evidence was looked for:
- There are no Module 3.1 transcripts, test output or reports in the repository.
- Local Claude session history begins 2026-10-27.
- The storage MCP (`proj-lessons`) has no entries.
- Neither commit hash appears in any file.
- Git history can't be read, because `.git` points to an unmounted host path.

**Missing evidence:** a Module 3.1 Tester transcript or test output, or host `git show d7c8444` plus a test run at that commit.

## 2. Regression task selected

The saved-search `maxPrice` validation task, verified by the Tester running `cd tracker-api && npm run test` without modifying files. It is the only candidate with a documented **Tester-agent** pass before calibration. The current suite has 15 tests: 3 in `listings.test.ts` and 12 in `searches.test.ts`, which matches the documented 15/15. The task is distinct from the calibration lint task in package, command and output.

## 3. Commands and agent workflows executed

1. `cd tracker-api && npm ci`. Installed dependencies from the lockfile; `node_modules` is gitignored.
2. A direct run outside the agent: `npm run test`. Result: 2 files, 15/15 passed, `EXIT_CODE=0` (`distinct-regression-direct-vitest.txt`).
3. **Attempt 1:** the Tester agent with the general task prompt, invoked the same way as the lint runs in `eval/README.md`. Session `fbd9005e-e1e1-4724-8e00-d0c00f606094`. It made 8 tool calls, including memory reads, retrieval, a failed `git status` and a `Grep`, and reported PASS 15/15.
4. **Attempt 2 (final):** the same invocation with a narrower prompt, asking for exactly one Bash call and no memory reads, retrieval, git or retries. Session `9331826a-97ea-435f-9440-5a6be3488269`. It made 1 tool call, `cd /workspace/marketradar/tracker-api && npm run test 2>&1; echo "EXIT_CODE=$?"`, and reported exit code 0, 2/2 files and 15/15 tests passed with none failing.
5. For each attempt, the deterministic gate (`eval/test_deterministic_unit_tests.py`) ran first. The rubric suite (`eval/test_rubric_suite_unit_tests.py`) was scored only after the gate passed.

**Evaluator profile.** This is a separate minimal profile, because the original lint evaluator requires the literal `npm run lint`. It reuses the original tool sets, check helper, judge call and score validation, with the **same thresholds**: 180,000 ms, 40,000 tokens including cache, at least 3 per dimension and at least 9/12. The original evaluator files were not modified.

## 4. Deterministic results

| Check | Attempt 1 (`…-001`) | Final attempt (`…-002`) |
|---|---|---|
| routing_order | PASS | PASS |
| real_transcript_present | PASS | PASS |
| tool_authorization | PASS (0 denials) | PASS (only `Bash`, 0 denials) |
| test_command_evidence | PASS | PASS |
| no_source_writes | PASS | PASS |
| execution_health | **FAIL**: 89,854 tokens | PASS: 22,094 tokens, 10,140 ms |
| **Gate** | **FAIL (5/6)** | **PASS (6/6)** |

Attempt 1's 89,854 tokens were confirmed as real cumulative usage, not an accounting error. The run made 6 API requests, each re-reading cached context of 10,000 to 17,400 tokens. The final attempt made 1 tool call and stayed within the limit.

## 5. Rubric results

- **Attempt 1:** not scored. The gate failed, so the judge was not called.
- **Final attempt:** **11/12, PASS** (threshold 9, at least 3 per dimension).
  - Test Result Accuracy: 4
  - Test and Failure Coverage: 4
  - Recommendation Quality: 3. The recommendation was a single conditional step and mentioned a "below minPrice" case that doesn't apply.

## 6. Is the distinct-regression requirement fully satisfied?

**Met, with one limitation.**
- **Distinct task:** yes.
- **Passes the deterministic gate and rubric under the corrected configuration and unchanged thresholds:** yes.
- **The Tester tool-grant fix generalizes beyond lint:** yes.
- **"Previously passing" backed by primary evidence:** no. It is supported only by `docs/iteration-log.md`. Primary evidence could only come from the Module 3.1 transcript or test output, or the host git history for `d7c8444`.

## 7. Remaining limitations

- **Documented baseline:** see section 6.
- **Narrowed prompt:** the pass needed a prompt that skipped the Tester's default memory reads (required by `CLAUDE.md`) and its retrieval step. The default workflow used 89,854 tokens. So the result shows the task fits the token budget when tightly scoped, not that the default Tester workflow does.
- **Two attempts:** this is a pass after one disclosed retry. Attempt 1's FAIL is kept.
- **Unconfirmed coverage in the final report:** because it was told not to read source, the Tester couldn't confirm from the output alone that the `maxPrice` cases exist. Attempt 1's `Grep` and the test file show they do: 10 `maxPrice` cases and 2 `resultsPerSearch` cases.
- **New evaluator:** the profile was written after calibration, though it reuses the original logic and thresholds.
- **Sample size:** n = 1 passing run.
- **Other open items:**
  - `.memory/SCOPE.md` still gives the path as `/workspace`.
  - The git worktree link is broken in the container, so commit and push state can't be confirmed.
