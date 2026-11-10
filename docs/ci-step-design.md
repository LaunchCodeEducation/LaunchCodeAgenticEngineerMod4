# CI Agentic Step Design: FashionMate harness

Author: swarna. Last updated: 2026-11-10.
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

Gaps found: no evaluation-harness job exists, so agent-affecting changes (prompts, agents, skills, allow-lists, `eval/`) are never re-checked against the Module 3 harness; and the review step reads `ANTHROPIC_API_KEY` while this course provisions `OPENROUTER_API_KEY`.

## Step: Policy test suite

- Does: Confirms that `docs/governance-policy.md`, the storage/retrieval/coursetools allow-lists, the skill Activation Scopes, and both `run-agent` scripts all agree (40 checks across 7 roles).
- Input: the whole repository at the tested commit.
- Produces: `policy-report.json` artifact (pytest JSON report), uploaded even on failure.
- Classification: **gating, permanent.** Deterministic: the same files always give the same result, and it has passed 40/40 on every run since it was written. Policy drift is an invariant the team agrees must never merge.
- Time limit: 5 minutes.
- Credentials: none. Workspace mounted read-only.

## Step: Evaluation harness (deterministic layer)

- Does: Runs `eval/test_deterministic.py` (14 structural checks: tool grants, forbidden operations, role order, context bleed, reviewer conflict, similarity floor, output schema, budgets) against the committed holdout transcripts in `.eval-artifacts/runs/holdout/`.
- Input: whole repository plus the classifier's "agent-affecting change" flag (runs only when `.claude/agents/`, `agents/`, `skills/`, `mcp/`, `mcp-servers/`, `eval/`, or `CLAUDE.md` change).
- Produces: `deterministic-report.json` artifact.
- Classification: **gating, conditional.** Deterministic, and it already catches the six calibrated failure modes. Known gap recorded in `docs/calibration-log.md` (HO-05 latency, HO-07 crash) is excluded from the gate until fixed rather than silently ignored.
- Time limit: 10 minutes.
- Credentials: none (reads saved transcripts; makes no model call).

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
- Produces: a PR comment, `review-output.md`, and `review-audit.json`.
- Classification: **advisory** (`continue-on-error: true`; not a required status check). Its output needs human judgment and its false-positive rate is unmeasured. Promote to gating only after its comments are shown to be reliable over many PRs.
- Time limit: 15 minutes.
- Credentials: `OPENROUTER_API_KEY`, scoped to the reviewer step only; the review script must be migrated from `ANTHROPIC_API_KEY`.

## Step: Audit trail

- Does: Combines the policy, governed-file, evaluation, and review artifacts into one JSON trail and posts a PR summary.
- Input: artifacts from all earlier jobs, including failed ones.
- Produces: `ci-audit-trail-[sha].json` artifact (90-day retention) and a PR comment.
- Classification: **observational; always runs** (`if: always()`), never blocks.
- Time limit: 5 minutes.
- Credentials: GitHub token with pull-request comment permission only.
