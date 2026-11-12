# CI Agentic Step Design

Module 4.2, Try It: Identify and Classify Agentic Steps to Add. Target codebase: MarketRadar.

This document classifies three CI steps as gating or advisory. It describes what exists in the repository today and marks what does not exist yet. The Evaluation Harness job (`eval-gate`) described in Step 2 was added to `.github/workflows/ci.yml` in Module 4.2 ("Evaluation Harness as a Gating Job").

## Current workflow (as of this document)

`.github/workflows/ci.yml` defines these jobs:

| Job | Name | What it runs | Gate behaviour |
|---|---|---|---|
| `change-type-check` | Change Classifier | `git diff --name-only` against the PR base (or `HEAD~1` on push); emits `changed-files`, `requires-governed-check`, `touches-policy` and `agent-affecting` | Not a gate |
| `policy-gate` | Policy Test Suite | `python -m pytest eval/test_policy.py -v` in the course image, workspace mounted read-only | Gating (no `continue-on-error`) |
| `eval-gate` | Evaluation Harness | Deterministic pytest in Docker (gating) and the Module 3 rubric judge via OpenRouter (advisory step) on agent-affecting changes; a skip notice on documentation-only changes | Gating (deterministic step); rubric step `continue-on-error: true` |
| `governed-file-gate` | Governed File Check | `python -m pytest eval/test_governed_files.py -v`, only when governed files changed | Gating when it runs |
| `advisory-review` | Advisory Code Review | `python scripts/run-reviewer.py`, pull requests only | Advisory (`continue-on-error: true`) |
| `audit-trail` | Audit Trail | `scripts/build-audit-trail.py` over the downloaded artifacts | Always runs (`if: always()`) |

Gaps found while inspecting the repository:

- **No Pipeline Integrity job exists.** `scripts/check-pipeline-integrity.py` expects jobs named `eval-gate` and `pipeline-integrity`, and `README.md` lists "Evaluation Harness" and "Pipeline Integrity Check" as required status checks. `eval-gate` now exists; `pipeline-integrity` does not.
- **No job sets `timeout-minutes`**, so GitHub's default job timeout applies.
- **The workflow has no `permissions:` block**, so the repository's default `GITHUB_TOKEN` permissions apply.
- **The automated review does not use the reviewer subagent.** `scripts/run-reviewer.py` calls the Anthropic Messages API directly; `.claude/agents/marketradar-code-reviewer.md` is not involved in CI.

Classification rule used below: a step is **gating** only if it is deterministic and has been run repeatedly with stable results; a model-backed step, or one that has not been shown to be stable, is **advisory**.

## Step 1: Policy Test Suite

- **What it does:** Checks that `docs/governance-policy.md` and the enforcement artifacts agree. `eval/test_policy.py` parses each role's MCP operation table, classification ceiling, `run-tests` skill scope and container-permission line from the policy, and compares them with `mcp-servers/storage/allow-list.json`, `mcp-servers/retrieval/allow-list.json`, `.claude/skills/run-tests/SKILL.md`, the agent definitions in `.claude/agents/`, the PreToolUse hooks (`scripts/enforce_skill_scope.py`, `scripts/enforce_bash_scope.py`) and `scripts/run-agent.sh` (run with a fake `docker`). It also makes in-memory MCP calls against both servers and checks audit-record fields, and checks the CI workflow's own properties. Mismatches are reported as overgrants and missing grants.
- **Input:** The repository at the commit under test, mounted read-only into the course image (`agentic_engineer_4`, built in the job).
- **Output:** pytest exit code; `policy-report.json` (pytest JSON report) uploaded as the `policy-report` artifact; the job result is passed to the audit trail.
- **Classification: gating.** Every check is deterministic: no model call, no network, no clock dependence. Local runs on 2026-11-10 returned 185 passed in 2.4–2.6 s, and the suite has caught every planted fault tried in this repository (allow-list overgrants and missing grants, policy-only edits, launcher changes, skill-scope changes). A failure means the policy and the enforcement disagree, which must block a merge. The step is already wired without `continue-on-error`.
- **Time limit:** 5 minutes for the test step. Measured runtime is under 3 seconds; the limit leaves room for a slow runner without hiding a hang. The job also builds the course image, whose build time on GitHub runners has not been measured here. No timeout is configured today.
- **Credentials:** None. The tests make no API calls and need no secrets. The job only needs to read the repository.

## Step 2: Evaluation Harness

- **What it does:** Runs the repository's existing stable deterministic checks (gating step):
  - `eval/test_deterministic.py`: the handoff validator CLI accepts a valid handoff; the policy states the least-privilege default; required directories exist.
  - `eval/test_deterministic_router.py`: the deterministic task router (`scripts/route_task_deterministic.py`) routes paths to the expected roles.
  - `eval/test_deterministic_step.py`: the deterministic handoff validator (`scripts/validate_handoff_deterministic.py`, ADR-001) accepts holdout handoffs and rejects empty, whitespace-only and missing required fields.

  It then runs, as a separate advisory step, the Module 3 rubric suite `eval/module3/test_rubric_suite.py --judge openrouter` against the recorded `eval/module3/evidence/development-run.json`. That manifest is the recorded Module 3 development run: it is **not** this change's agent output and **not** the holdout set, so the rubric step does not evaluate the change under test. The suite runs its own deterministic pre-check first and calls the judge only if that passes. With the current evidence the pre-check fails (`execution_health`: 74,566 tokens against a 40,000 limit), so the judge is not called and the step reports a failure that does not fail the job.

  **Not included:**
  - `eval/test_rubric_suite.py` is a placeholder. It checks that two documents contain particular words; it is not a rubric evaluation and must not be reported as one.
- **Input:** The `agent-affecting` output of the Change Classifier and the repository at the commit under test, mounted read-only into the course image. The job runs its checks only when `agent-affecting` is `true` (changes under `.claude/`, `.agents/`, `.skills/`, `mcp-servers/`, `eval/`, `scripts/`, `.github/workflows/`, or to `docs/governance-policy.md`, `docs/routing-and-tool-grant-map.md`, `CLAUDE.md`, `Dockerfile`, `docker-entrypoint.sh`, `requirements.txt`). Otherwise it prints a skip notice and passes, so the job has no job-level condition and reports a status on every run. It `needs: policy-gate`, so the Policy Test Suite stays the first gate.
- **Output:** The deterministic step's pytest exit code and `deterministic-report.json` (pytest JSON report for the three files). The rubric step writes `rubric-report.json` (deterministic pre-check result, whether the rubric ran, scores and pass/fail if it did, and the reason if it did not). Both reports are uploaded with `if: always()` and `if-no-files-found: ignore` as the `eval-reports` artifact. The job result and both step outcomes are passed to the audit trail.
- **Classification: gating for the deterministic step; advisory for the rubric step.** The deterministic checks have no model or network dependency and are stable: a local run on 2026-11-10 returned 15 passed in under 0.1 s for these three files. The step has no `continue-on-error`, so a failure fails the job. The rubric step is model-backed, has not been shown to give stable scores, and evaluates recorded evidence rather than the change, so it has `continue-on-error: true` and runs only if the deterministic step succeeded.
- **Time limit:** 5 minutes for the deterministic step (measured runtime well under 1 second) and 5 minutes for the rubric step, which sets a 120-second timeout on its single OpenRouter request. No timeout is configured in the workflow today. The job also builds the course image.
- **Credentials:** `OPENROUTER_API_KEY` only, and only for the rubric step:
  - Stored as a repository secret and exposed only in the `env:` of the "Run rubric evaluation (advisory)" step, not at job or workflow level; passed into the container by name (`-e OPENROUTER_API_KEY`). The judge code never logs it.
  - Optional repository variable `OPENROUTER_MODEL` selects the judge model; if unset, the code's default slug is used, which has not been verified against OpenRouter's model list.
  - The deterministic step has no `env:` and needs no key.
  - If the key is missing (for example on fork PRs) and the deterministic pre-check passes, the judge raises an error and the rubric step fails without failing the job. With the current evidence the pre-check fails first, so the judge, and the key, are never used.

## Step 3: Automated Code Review

- **What it does:** `scripts/run-reviewer.py` reviews the files changed in the pull request. It reads `CHANGED_FILES` (from the Change Classifier), includes only text-like files (up to 20,000 characters per file and 60,000 in total), sends one request to the Anthropic Messages API asking for correctness, security, CI/Docker, governance-drift and missing-test findings, and writes the answer. If `ANTHROPIC_API_KEY` is missing or the API call fails, it writes an explanatory note instead of a review. It always exits 0.
- **Input:** The changed-file list from the Change Classifier and the repository mounted read-only; the model is `ANTHROPIC_MODEL` if set, otherwise the script's default. The job runs only for `pull_request` events.
- **Output:** `/out/review-output.md` and `/out/review-audit.json` (which files were included or skipped and why, whether a key was present, and that the exit behaviour is always zero), uploaded together as the `advisory-review` artifact. **It does not post a PR comment**; the earlier version of this document said it did. The job result is passed to the audit trail.
- **Classification: advisory.** Model output is non-deterministic, and the review has not been evaluated for accuracy or consistency in this repository. A false positive must not block a merge, and a model outage must not fail the pipeline. This is enforced twice: the script always exits 0, and the job has `continue-on-error: true`. It must not be a required status check.
- **Time limit:** 10 minutes for the job. The script sets a 90-second timeout on its single API request and caps output at 1,200 tokens. The job also builds the course image. No job timeout is configured today.
- **Credentials:** `ANTHROPIC_API_KEY` only, following least privilege:
  - Stored as a repository secret and exposed only in the `env:` of the single "Run advisory agentic review" step, not at job or workflow level.
  - Passed into the container by name (`-e ANTHROPIC_API_KEY`); the workspace is mounted read-only and the only writable mount is the output directory.
  - Not available to the policy, Evaluation Harness, governed-file or audit-trail jobs.
  - GitHub does not pass secrets to workflows triggered from forks, so on fork PRs the script writes the "no review performed" note instead of a review.
  - Recommended, not yet applied: use a key dedicated to CI review with a spend limit, and add a workflow-level `permissions: contents: read` block, since no job needs to write to the repository.

## Not verified here

- No GitHub Actions run was inspected from this environment, so it is not confirmed that the advisory review has produced a real review in CI.
- Course-image build time on GitHub runners is unmeasured.
- Job timeouts and the `permissions:` block are design decisions in this document, not yet implemented in `ci.yml`.
- The `eval-gate` job and the OpenRouter judge have not run on GitHub Actions; the OpenRouter model slug is unverified.
