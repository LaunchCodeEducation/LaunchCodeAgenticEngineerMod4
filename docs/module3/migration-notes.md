# Module 4.1 Migration Notes — MarketRadar

**Date:** 2026-11-03
**Source:** Module 3 MarketRadar worktree (`marketradar-module-3.3-exercise-1-eval-harness`), mounted read-only
**Destination:** Module 4 course repository (`/workspace`)

This file records how MarketRadar and the Module 3 agentic harness were brought into the Module 4 infrastructure, and the Module 3 failures that came with them. Known failures are **documented, not repaired**.

## 1. Layout

| Module 3 path | Module 4 path | Notes |
|---|---|---|
| `tracker-api/` | `tracker-api/` | Unchanged |
| `tracker-client/` | `tracker-client/` | Unchanged |
| `.claude/agents/{planner,implementer,tester,project-manager}.md` | `.claude/agents/` | Unchanged |
| `.claude/agents/code-reviewer.md` | `.claude/agents/marketradar-code-reviewer.md` | Renamed so it does not override the image-level `code-reviewer` agent. The frontmatter `name:` was changed to match; nothing else changed. |
| `.memory/` | `.memory/` | Unchanged. `SCOPE.md` says `/workspace`, which is still correct. |
| `mcp/` | `mcp/` | Reference only. Not wired into Module 4. Module 4's `mcp-servers/` stays authoritative. |
| `docs/*`, `README.md`, `setup.md`, `session_tasks.md` | `docs/module3/` | Unchanged. Module 4's `docs/calibration-log.md`, `docs/orchestration-diagram.md` and `docs/routing-and-tool-grant-map.md` kept their paths. |
| `eval/*` | `eval/module3/` | See §3 |
| `module-3.3-evaluation-harness/` | `eval/module3/module-3.3-evaluation-harness/` | See §3 |

**Path references in the Module 3 docs are historical.** Paths such as `eval/test_deterministic.py`, `module-3.3-evaluation-harness/…`, `docs/calibration-log.md` and `/workspace/marketradar/tracker-api` in the docs, evidence and reports describe the Module 3 layout at the time. They were deliberately left unedited. Use the commands in §4.

## 2. Infrastructure changes

- **`Dockerfile`:** added a build step that fails if Node.js is older than 20.19 (Vite 8 requirement). Node is still installed from Debian apt. Under the current `python:3.12-slim` (Debian trixie) base that is v20.19.2.
- **`.gitignore`:** added Node rules (`node_modules/`, `dist-ssr/`, `*.local`, npm/yarn/pnpm logs), `tracker-api/storage/facebook-state.json`, and re-included `tracker-api/src/lib/` and `tracker-client/src/lib/`. Without that re-include, the Python template's `lib/` rule silently ignored six source files.
- **`CLAUDE.md`, `README.md`:** MarketRadar sections appended. All existing Module 4 content is unchanged.
- **Not changed:** `.github/workflows/ci.yml`, `docs/governance-policy.md`, `docs/adr/`, `scripts/`, `mcp-servers/`, `schemas/`, `examples/`, `example-task-app/`, `agents/`, `skills/`, `.agents/`, `.skills/`, and all Module 4 tests.

## 3. Evaluation harness relocation

**Code changes needed to keep it working:**
- `eval/module3/test_deterministic.py`: `ROOT = Path(__file__).resolve().parents[1]` → `parents[0]`. The harness root is now `eval/module3/`. The other profiles import `ROOT` from this module.
- New `eval/module3/conftest.py`: excludes these unittest/CLI files from pytest collection. Without it, Module 4's documented `pytest eval/` fails, because of basename clashes with `eval/test_deterministic.py` and `eval/test_rubric_suite.py` and because the harness modules aren't on the import path.

**Evidence migrated:** all run manifests, deterministic and rubric reports, `distinct-regression-direct-vitest.txt`, the synthetic fixture, and the tester transcripts the run manifests reference (needed to re-run the deterministic checks). For the harness's HO-01 evaluator, `HO-01-retrieval.jsonl` is migrated as the sample input.

**Left in the Module 3 repository (bulky, and the harness doesn't need them):**
- `eval/evidence/calibration/holdout/*.jsonl` (about 2.5 MB of holdout transcripts)
- `eval/evidence/submission/` (about 4.6 MB). This was the course-upload bundle: copies of the evidence, docs and config already migrated, plus transcripts in `.json` form.
- `module-3.3-evaluation-harness/HO-02-planner.jsonl`, `planner-diagnostic.jsonl`

**Excluded as temporary artifacts:** `*.backup.py`, `eval/evidence/calibration/holdout/HO-03.jsonlls` (empty stray file), `__pycache__/`.

**Also not copied:** `.git` (a worktree pointer to an unmounted host path), `node_modules/`, `dist/`, `tracker-api/storage/*` (only its `.gitignore`), and the Module 3 `Dockerfile`, which Module 4's replaces.

**Secret scan:** no credentials found. The matches were regex patterns inside a HO-03 transcript and the placeholder DSN `postgresql://USER:PASSWORD@HOST/DB`. Host usernames in transcripts were already `[REDACTED_USER]`.

## 4. How to run (from the repository root)

```bash
# Harness offline self-test (unittest; run from the harness root)
cd eval/module3 && python3 -m unittest test_harness_selftest -v

# Re-evaluate a recorded run (write output outside evidence/ to keep records intact)
cd eval/module3 && python3 test_deterministic.py evidence/calibration/regression-run.json
cd eval/module3 && python3 test_deterministic_unit_tests.py evidence/calibration/distinct-regression-2-run.json

# Application
cd tracker-api && npm ci && npm test
cd tracker-client && npm ci && npm run lint && npm run build
```

## 5. Verification at migration time

| Check | Result |
|---|---|
| Module 4 `pytest eval/` | 26 passed (same as before the migration) |
| Module 3 harness self-test | 4/4 OK |
| Deterministic re-evaluation of the 6 recorded runs | All 6 match the recorded verdicts and every per-check result |
| HO-01 evaluator on `HO-01-retrieval.jsonl` | Runs; reports `passed: true` for that exploratory transcript |
| `tracker-api`: `npm test` | 15/15 passed (matches the Module 3 baseline) |
| `tracker-api`: `npm run build` | OK |
| `tracker-client`: `npm run build` | OK |
| `tracker-client`: `npm run lint` | **FAIL: 7 errors, 0 warnings.** Pre-existing; see §6. |
| Node.js | v20.19.2 |

## 6. Known Module 3 failures and limitations (not repaired)

Sources: `docs/module3/calibration-log.md`, `module-3-reflection.md`, `module-3-regression-summary.md`, `module-3-submission-checklist.md`.

1. **`tracker-client` lint fails: 7 errors, 0 warnings.** These are `react-hooks/set-state-in-effect` and `react-refresh/only-export-components` in `src/context/AppDataContext.tsx` and `src/context/FacebookConnectionContext.tsx`. This is the same output recorded in the Module 3 lint calibration transcripts. It was the *subject* of the lint evaluation task, not a migration regression.
2. **HO-01 retrieval:** the post-calibration run never reached the retrieval MCP server (plan mode denied it). Assertions 1–2 FAIL and assertion 3 is NOT VERIFIED.
3. **Holdout totals:** of 21 assertions, 10 PASS, 2 FAIL, 4 BLOCKED and 5 NOT VERIFIED. HO-06's classification-ceiling check was never exercised.
4. **Token budget:** the Tester's default workflow exceeds the 40,000-token execution-health limit (59,566–89,854 tokens observed), largely from the mandatory memory reads in `CLAUDE.md`. The distinct regression passed only with a narrowed prompt. The passing lint regression had a 577-token margin.
5. **Sample size:** each passing regression is a single run (n = 1). The distinct regression passed after one disclosed retry.
6. **Baseline evidence:** the "previously passing" baseline is backed only by `docs/module3/iteration-log.md`. There is no primary evidence (no Module 3.1 transcript and no readable git history for `d7c8444` or `0e336b4`).
7. **Git history unavailable:** the Module 3 `.git` was a worktree pointer to an unmounted host path, so Module 3 commit history is not carried into this repository.
8. **Role model mismatch:** Module 3 roles (`planner`, `verifier`, `project_manager` and `code-reviewer` in `mcp/roles.allowlist.json`, with a SQLite store under `/memory`) don't match Module 4's governed roles (`orchestrator`, `implementer`, `reviewer`, `tester`, `project-manager`). `scripts/run-agent.sh` rejects `planner`. Reconciling them is future Module 4 governance work.
9. **Scraper runtime:** `tracker-api`'s Playwright scraper needs Chromium, which the course image doesn't install. The Vitest suite mocks Prisma and doesn't need it. A real `DATABASE_URL` is needed for anything beyond the tests.
10. **Agent references:** Module 3 docs and evidence still call this agent `code-reviewer`. Those are historical references and were left unedited.
