# CI Agentic Step Design

## Step: Policy test suite

- Does: Confirms `docs/governance-policy.md`, MCP allow-lists, skill scopes, and container permissions agree.
- Input: whole repository.
- Produces: `policy-report.json` artifact.
- Classification: gating, permanent.
- Time limit: 5 minutes.
- Credentials: none.

## Step: Evaluation harness

- Does: Runs deterministic and rubric checks on agent-affecting changes.
- Input: whole repository plus changed-file classifier output.
- Produces: `deterministic-report.json` and `rubric-report.json`.
- Classification: gating, conditional.
- Time limit: 10 minutes.
- Credentials: `ANTHROPIC_API_KEY` only for model-backed rubric runs.

## Step: Agent code review

- Does: Reviewer subagent scores changed files and posts an advisory PR comment.
- Input: changed files from the shared classifier.
- Produces: PR comment, `review-output.md`, and review audit log.
- Classification: advisory; not a required status check.
- Time limit: 15 minutes.
- Credentials: `ANTHROPIC_API_KEY`, scoped to the reviewer step only.

## Step: Audit trail

- Does: Combines policy, harness, and review artifacts into one JSON trail and posts a PR summary.
- Input: CI artifacts from earlier jobs.
- Produces: `ci-audit-trail-[sha].json` artifact and PR comment.
- Classification: required operational evidence; always runs.
- Credentials: GitHub token with pull-request comment permission.
## Step: Pipeline Integrity Check

- Does: Inspects `.github/workflows/ci.yml` to confirm that required CI/CD guardrails have not been weakened or removed.
- Input: The workflow definition in `.github/workflows/ci.yml`.
- Produces: `pipeline-integrity-report.json`, which records the integrity check configuration and is uploaded as a CI artifact.
- Classification: Gating and permanent.
- Rationale: This check protects an invariant that must always hold. A pull request must not be able to weaken or remove the same CI/CD guardrails that are supposed to evaluate it.
- Checks:
  - Confirms `policy-gate` and `governed-file-gate` have not been weakened with `continue-on-error: true`.
  - Confirms `audit-trail` still runs with `if: always()`.
  - Confirms the `change-type-check` classifier job still exists.
- Required Status Check: Pipeline Integrity Check must be configured as a required status check for the `main` branch.
- Audit Trail Wiring: `pipeline-integrity` is included in the `audit-trail` job's `needs:` list so its result is part of the durable CI record.
- Artifact: `pipeline-integrity-report.json`; the report identifies the job, display name, gating classification, and the guardrail checks performed.
- Credentials: None. This is a deterministic workflow integrity check and does not require an API key.
- Verified: The check is designed to fail if a required gate receives `continue-on-error: true`, if `if: always()` is removed from `audit-trail`, or if `change-type-check` is removed. Verification will be completed using a throwaway branch without merging the weakened configuration.