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

## Step: Automated code review
- Does: Reviewer subagent scores changed files against the rubric and posts a PR comment.
- Input: changed files in the pull request.
- Produces: a structured review comment.
- Classification: advisory (new; promote to gating once stable).
- Time limit: 15 minutes.
- Credentials: OPENROUTER_API_KEY, scoped to this step only.


## Step: Pipeline Integrity Check
- Does: Parses .github/workflows/ci.yml itself and fails the run if a required guardrail was removed or weakened in the same change the other jobs evaluate.
- Input: the workflow definition file (.github/workflows/ci.yml) — NOT the code diff.
- Produces: ci-artifacts/pipeline-integrity-report.json, uploaded as artifact "pipeline-integrity-report".
- Classification: GATING, permanent. It protects an invariant the team has agreed must always hold (the pipeline cannot be silently disabled), so — like the policy gate — it is never a candidate for demotion to advisory.
- Runs when: every run, with no needs: and if: always(), so an upstream failure or skip can never prevent it from running.
- Checks:
  1. change-type-check (classifier) still exists.
  2. policy-gate has NOT been given continue-on-error: true.
  3. governed-file-gate has NOT been given continue-on-error: true.
  4. audit-trail still runs with if: always().
  5. (self-protection) pipeline-integrity itself has NOT been given continue-on-error: true.
  Implemented in scripts/check-pipeline-integrity.py: loads the YAML, inspects each job, writes the report, then exits 1 if any check failed so the job fails.
- Required status check: YES — added to branch protection for main alongside Policy Test Suite and Governed File Check.
- Audit-trail wiring: added to audit-trail's needs: [...] list; its report is downloaded into ci-artifacts by download-artifact (merge-multiple) alongside the other *-report.json files, and build-audit-trail.py reads it via --integrity-result. A not-run/skipped state is reported as "not triggered" (parallel to the eval harness reporting "not triggered" rather than "failed"); a violation is status "fail" with the failing check names in "violations".
- Artifact shape: { "job": "pipeline-integrity", "status": "pass"|"fail", "checks": [{ "name", "passed", "detail" }], "violations": [names], "timestamp" }.
- Verified: Verified (2026-10-09): On branch wip-weaken-gate, added continue-on-error: true to policy-gate and opened a PR to main. Pipeline Integrity Check failed with “gating job ‘policy-gate’ has continue-on-error: true, which disables the gate” (exit 1). The sabotage was independently caught by the Policy Test Suite as well (eval/test_policy.py::test_policy_gate_is_not_continue_on_error — 1 failed, 4 passed). Audit Trail ran and recorded the run. PR closed without merging; main stayed green.
