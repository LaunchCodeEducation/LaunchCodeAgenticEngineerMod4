# CI Agentic Step Design: FashionMate harness

Author: swarna. Last updated: 2026-11-11.
Pipeline: `.github/workflows/ci.yml` (GitHub Actions, `ubuntu-latest` runners, course container built from the repo at the tested commit).

Rule used for every classification: deterministic checks may gate immediately; every new agentic (model-judged) step starts advisory and is promoted to gating only after its false-alarm rate has been measured over many runs.

## Baseline audit (2026-11-10)

| Job key | Display name | Runs when | Uses AI | Blocks merge | Produces |
|---|---|---|---|---|---|
| change-type-check | Change Classifier | every push and PR | no | no | job outputs (changed files, flags) |
| policy-gate | Policy Test Suite | every push and PR | no | yes | `policy-report.json` |
| governed-file-gate | Governed File Check | when governed files change | no | yes | governed-file report |
| advisory-review | Advisory Code Review | pull requests only | yes | no (`continue-on-error: true`) | `review-output.md`, review audit log |
| audit-trail | Audit Trail | always, after the others | no | no | combined audit-trail artifact |

Gaps found (resolved 2026-11-11): no evaluation-harness job existed, so agent-affecting changes were never re-checked; added as `eval-gate`. The review step read `ANTHROPIC_API_KEY`; migrated to `OPENROUTER_API_KEY` via OpenRouter's Anthropic-compatible endpoint.

MCP server credentials: none required. The coursetools, retrieval and storage FastMCP servers read only non-secret configuration from the environment: file paths (COURSETOOLS_ROOT, COURSETOOLS_ALLOWLIST, *_AUDIT_LOG, STORAGE_STORE) and the role label AGENT_ROLE. None are credentials, so none are registered as secrets (checked 2026-11-10). Only OPENROUTER_API_KEY is registered.

## Where gating is enforced

A job only blocks a merge if it is a required status check in branch protection for `main`. `continue-on-error: true` only stops a job from failing the run; it does not make anything gating.

| Job | Required status check | Effect |
|---|---|---|
| Policy Test Suite | yes | failure blocks merge |
| Governed File Check | yes | failure blocks merge |
| Pipeline Integrity Check | yes | failure blocks merge; always runs (`if: always()`) and inspects `ci.yml` itself |
| Evaluation Harness (deterministic) | yes | failure blocks merge; reports success when skipped for non-agent changes |
| Evaluation Harness (rubric) | no (step inside the required job, with step-level `continue-on-error: true`) | advisory: a rubric failure never fails the job |
| Advisory Code Review | no | advisory (`continue-on-error: true`) |
| Audit Trail | no | observational |

Change Classifier is the only job that does not need policy-gate: it runs first because policy-gate depends on it, and it only lists file names (no agent, no secrets).

## Step: Policy test suite

- Does: Confirms that `docs/governance-policy.md`, the storage/retrieval/coursetools allow-lists, the skill Activation Scopes, and both `run-agent` scripts all agree (40 checks across 7 roles).
- Input: the whole repository at the tested commit.
- Produces: `policy-report.json` artifact (pytest JSON report), uploaded even on failure.
- Classification: **gating, permanent.** Deterministic: the same files always give the same result, and it has passed 40/40 on every run since it was written. Policy drift is an invariant the team agrees must never merge.
- Time limit: 5 minutes.
- Credentials: none. Workspace mounted read-only.

## Step: Evaluation harness (deterministic layer)

- Does: Runs three deterministic pytest files: `test_deterministic.py` (3 repo smoke tests: handoff-validator CLI, least-privilege wording in the policy, required directories), `test_deterministic_router.py` (5 routing tests), and `test_deterministic_step.py` (7 handoff-schema tests, including 3 holdout handoff cases). 15 tests, plus `test_audit_trail.py` (4 tests: trail sections present, denials collected, secrets redacted, skipped eval recorded as not_triggered) so a broken audit-trail script blocks the merge. 39 tests, no model call: the 19 above plus `test_citation_assembly.py` (20 tests for the ADR-003 deterministic citation step, including a replay over every committed transcript).
- Input: whole repository; runs only when the Change Classifier flags an agent-affecting change (`.github/workflows/`, `.agents/`, `.skills/`, `.claude/agents/`, `agents/`, `skills/`, `mcp/`, `mcp-servers/`, `eval/`, `CLAUDE.md`, governance docs, `scripts/`). Workflow files are included because editing a gate must re-run that gate.
- Produces: `deterministic-report.json` artifact.
- Classification: **gating, conditional.** Deterministic: same inputs, same result. Verified on PR #1 (ran in 6m 36s on an `eval/` change) and on commit 6e18ae6 (skipped on a `ci.yml`-only change, before workflow files were added to the trigger list).
- Time limit: 10 minutes.
- Credentials: none.
- Known gap: the 14 transcript-level checks from Module 3 (context_bleed, role_order, similarity_floor, forbidden_operations, etc.) are scored when transcripts are produced, not re-scored in CI. The 62 committed files in `.eval-artifacts/` could be re-checked here; that is a follow-up. HO-05 (latency) and HO-07 (crash) remain open in `docs/calibration-log.md`.

## Step: Evaluation harness (rubric layer)

- Does: Runs `eval/test_rubric_suite.py`, an agent-as-judge score of correctness, task adherence, groundedness, and clarity, on runs that pass the deterministic gate.
- Input: transcripts that cleared the deterministic layer.
- Produces: `rubric-report.json` artifact with each score and the judge's justification.
- Classification: **advisory.** The rubric scored 38/80 on the holdout set with 1/6 tasks passing both layers, and the judge loads project context that may bias it, so it is not yet calibrated enough to block a merge. Promote to gating once holdout scores are stable at or above the 12/16 threshold over repeated runs.
- Time limit: 15 minutes.
- Credentials: `OPENROUTER_API_KEY`, injected from repository secrets into this step only.

## Step: Automated code review

- Does: The reviewer subagent reads the changed files, scores them against the quality rubric, and posts a structured review comment on the pull request.
- Input: changed files from the Change Classifier.
- Produces: a PR comment, `review-output.md`, and `review-audit.json`. The comment is created or updated by a hidden marker (`scripts/upsert_pr_comment.py`), so reruns update one comment and the review and audit summary never overwrite each other.
- Classification: **advisory** (`continue-on-error: true`; not a required status check). Its output needs human judgment. First measured false-positive rate: 2 of 7 findings (29%) on PR #1, see `docs/calibration-log.md`. Promote to gating only after a human reviewer has labelled its findings on at least 20 PRs and fewer than 10% are false alarms. Results are tracked in `docs/calibration-log.md`.
- Time limit: 15 minutes.
- Credentials: `OPENROUTER_API_KEY`, scoped to the reviewer step only. Migrated from `ANTHROPIC_API_KEY` to OpenRouter's Anthropic-compatible endpoint on 2026-11-11; verified by a real review on PR #1.
- Permissions: job-level `contents: read` and `pull-requests: write` only, so the automatic token can post the review comment and nothing else.
- Audit record: this reviewer calls the model directly and makes no MCP calls, so there is no MCP audit log to collect. `review-audit.json` (files reviewed, why each was included or skipped, key present true/false, never the value) is its audit record and is uploaded in the `advisory-review` artifact.
- Two advisory layers seen in practice: on PR #1 an indentation error made the script exit non-zero; job-level `continue-on-error: true` contained it and nothing was blocked. After the fix, the script exited 0 while reporting high-priority findings.

## Step: Pipeline integrity check

- Does: Reads `.github/workflows/ci.yml` **from the commit under test** (so a PR that weakens the pipeline is judged against its own version of the file) and runs 11 structural checks with `scripts/check_pipeline_integrity.py`. Any failed check fails the job and the run. It inspects the workflow definition itself, not the code change.
- Checks (each is one entry in the report):

| Check | Looks for | Why |
|---|---|---|
| `classifier_exists` | `change-type-check` job exists and still outputs `changed-files`, `requires-governed-check`, `touches-policy` | Every conditional gate reads these; without them gates silently skip |
| `required_jobs_present` | All seven jobs are still defined | Deleting a gate is the bluntest bypass |
| `gates_not_soft` | No `continue-on-error` on `policy-gate`, `governed-file-gate`, `eval-gate`, `pipeline-integrity`, at job or step level. Only allowed exception: the `Run rubric harness (advisory)` step | `continue-on-error` turns a gate into an advisory check while it still looks green |
| `gates_not_conditionally_skipped` | No job-level `if:` on the three gates; `pipeline-integrity` must be exactly `if: always()` | GitHub counts a skipped required job as passing, so `if: false` would disable a gate invisibly |
| `policy_tests_unconditional` | The `policy-gate` step that runs `eval/test_policy.py` exists and has no `if:` | The policy gate is permanent and must run on every change |
| `eval_gate_runs_deterministic_harness` | `eval-gate` still runs `eval/test_deterministic.py` | Stops the gate from being hollowed out to an empty job |
| `policy_gate_runs_first` | `governed-file-gate`, `eval-gate`, `advisory-review`, `pipeline-integrity` all `needs: policy-gate` | Agent steps must not run under unverified permissions |
| `audit_trail_always` | `audit-trail` has `if: always()` | Without it, a failing run (the one you most need to review) produces no trail |
| `audit_trail_needs_all` | `audit-trail` `needs:` lists all six other jobs | A job left off the list drops off the record |
| `no_trigger_path_filters` | No `paths` / `paths-ignore` on the `push` or `pull_request` triggers | A trigger-level filter skips the whole workflow, including required gates |
| `secrets_step_scoped` | No secret referenced in workflow-level or job-level `env` | Secrets must reach only the step that calls the model |

- Input: the PR's `.github/workflows/ci.yml`. Runs on every push and PR with `needs: [change-type-check, policy-gate]` and `if: always()`, so it runs and reports even when other jobs fail. It needs no container, no model and no secret (Python + PyYAML on the runner, about 30 seconds after the policy gate).
- Produces: `pipeline-integrity-report.json`, uploaded as the `pipeline-integrity-report` artifact with `if: always()` (90-day retention). Same shape as the pytest JSON reports the other gates emit, so the audit trail reads it the same way:
  `{"exitcode": 0|1, "workflow": "...", "summary": {"total", "passed", "failed"}, "tests": [{"nodeid": "pipeline-integrity::<check>", "outcome": "passed"|"failed", "detail": "<what was found>"}]}`.
  If the workflow cannot be parsed, the report has a single failed `workflow_parses` entry. This job always runs, so it is never `not_triggered`; if its report is missing, the audit summary says "not run".
- Audit trail: `pipeline-integrity` is in `audit-trail`'s `needs:` list, and its result is passed as `--integrity-result`. `build-audit-trail.py` adds a `pipeline_integrity` section (per-check outcome and detail) to `ci-audit-trail-<sha>.json`, plus a **Pipeline Integrity Check** row and a "Pipeline integrity checks: X/11 passed (failed: ...)" line to the PR summary.
- Classification: **gating, permanent.** Deterministic, and it protects an invariant the team has agreed must always hold: the gates themselves stay intact. Same reasoning as the policy gate; never a candidate for demotion to advisory.
- Required status check: **Pipeline Integrity Check** is required in the branch protection rule for `main`, alongside Policy Test Suite, Governed File Check and Evaluation Harness.
- Self-protection: the job's own `continue-on-error`, `if: always()` and its place in `audit-trail` `needs:` are themselves checked. `eval/test_pipeline_integrity.py` runs in this job on every run and proves the checker still catches 8 weakened variants, so the checker cannot quietly stop detecting.
- Time limit: 5 minutes.
- Credentials: none.
- Verified (automated, every run): `test_pipeline_integrity.py` passes the real `ci.yml` (11/11) and fails each weakened copy on the expected check: `continue-on-error` on policy-gate → `gates_not_soft`; `if: always()` removed from audit-trail → `audit_trail_always`; change-type-check deleted → `classifier_exists`; `if: false` on eval-gate → `gates_not_conditionally_skipped`; `continue-on-error` on the deterministic step → `gates_not_soft`; `paths:` on the PR trigger → `no_trigger_path_filters`; secret in job-level env → `secrets_step_scoped`; pipeline-integrity removed from audit-trail needs → `audit_trail_needs_all`.
- Verified (live PR): PR #8 (`test/weaken-policy-gate`, commit cd1f986, run #38) added `continue-on-error: true` to `policy-gate`. Result: **Pipeline Integrity Check failed after 7 seconds** with `FAIL gates_not_soft: policy-gate has job-level continue-on-error` (10/11 checks passed), and as a required check it **blocked the merge**. The Policy Test Suite caught it independently (`test_policy_gate_is_not_continue_on_error` failed, 39/40 passed), a second layer. The audit trail for that run recorded `| Pipeline Integrity Check | failure |` and `Pipeline integrity checks: 10/11 passed (failed: gates_not_soft)` in `ci-audit-summary.md` (commit aac383d), so the failure is in the durable record, not only the PR checks UI. Real finding from this run: because of the weakening, `needs.policy-gate.result` was reported as `success` even though a policy test failed, so the audit gate table showed "Policy Test Suite | success" while the per-check line showed 39/40. The weakening disguised the policy failure; only the per-check count and the integrity check exposed it. The weakening also let downstream jobs start despite the failed policy gate. Reverting on the same PR (commit 2c24874) returned every check to green, and PR #8 was then merged (not closed, by mistake). Because it contained both the weakening and its revert, the net change to ci.yml is zero (confirmed with git diff against 750c84b), and the merge was only possible after the revert turned every required check green.
- Known limit: a PR can also edit `check_pipeline_integrity.py` itself. Changes to `scripts/` trigger the eval gate and the self-test, and the diff is visible in review, but a CODEOWNERS rule requiring a second reviewer on `.github/` and `scripts/` would close this fully. As repository owner I can also bypass branch protection; every bypass is shown in the push output.

## Step: Audit trail

- Does: Runs after every other job (`needs:` lists all six other jobs, including `pipeline-integrity`; `if: always()`), downloads every artifact (`download-artifact@v4` with `merge-multiple: true`), and `scripts/build-audit-trail.py` combines them into one record: CI metadata (SHA, event, PR, timestamp), change classification (including `touches_policy`), every gate result including the pipeline integrity check, per-check policy results, per-check integrity results, per-check deterministic results, rubric results and any recorded scores, and MCP activity with any authorization denials.
- Input: job results passed as arguments, plus the uploaded reports and any MCP audit logs. In CI the jobs make no MCP calls, so the trail says "No MCP audit logs in this run" instead of showing an unexplained empty list. Denials are collected whenever MCP audit logs are present (covered by `test_audit_trail.py`).
- Produces: `ci-audit-trail-<sha>.json` and `ci-audit-summary.md` in the `audit-trail` artifact (90-day retention), plus a PR summary comment updated in place by a hidden marker.
- Honest gate reporting: a conditional gate whose heavy steps were skipped is recorded as `not_triggered`, not `success`.
- Secrets: the script never reads the environment, and every string it writes passes through a redaction filter for token-shaped values (`sk-or-`, `sk-ant-`, GitHub tokens, Bearer values). Verified by a test and by scanning a downloaded trail.
- Classification: **observational; always runs** (`if: always()`), never blocks. The script itself is tested by the deterministic gate, so a change that would break the record blocks the merge.
- Time limit: 5 minutes.
- Credentials: none. Job-level `contents: read` and `pull-requests: write` for the automatic token only.

## Considered and not added

- **Dependency auditor in CI:** not added. Its role is advisory by design and it has no output a PR author can act on yet. Revisit once it can write a findings artifact.
- **Rubric suite as a gate:** not added as a gate. It scored 38/80 on holdout; it stays advisory until it calibrates (see rubric step above).
- **Live-agent runs on every push:** not added. Too slow and costly for a check that must finish in under 10 minutes; the gate runs deterministic tests instead, and re-scoring the committed holdout transcripts is a listed follow-up.
