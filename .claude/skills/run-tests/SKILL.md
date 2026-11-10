---
name: run-tests
description: Run the MarketRadar tracker-api test suite (Vitest) and report the results. Tester role only; see Activation Scope.
allowed-tools:
  - Bash(npm --prefix tracker-api test)
---

# run-tests

## Activation Scope

Source: `docs/governance-policy.md`, each role's "Skill activation scope" table.

| Role | Activation permitted | Notes |
|---|---|---|
| tester | YES | The only role that may activate this skill. |
| planner | NO | Planning does not run tests. |
| implementer | NO | The Implementer must not evaluate its own work. |
| reviewer (`marketradar-code-reviewer`) | NO | Read-only review role; testing belongs to the Tester. |
| project-manager | NO | Records outcomes only. |
| orchestrator (main session) | NO | Verification belongs to the Tester. |
| dependency-auditor | NO | Inspects dependency manifests; test execution belongs to the Tester. |

Enforcement: the PreToolUse hook `scripts/enforce_skill_scope.py`, registered in `.claude/settings.json`, denies a `Skill` call for `run-tests` unless the hook input's `agent_type` is `tester`, denies the tester any other skill, and writes a `skill_activation_denied` audit record outside the repository. Only the tester's agent definition holds the `Skill` tool.

Not enforced by this skill scope: a human typing `/run-tests` (PreToolUse does not fire), and any role that holds Bash running the test command directly (governance policy D4, D5).

## Steps

1. Run `npm --prefix tracker-api test` with the Bash tool.
2. Report the pass and fail counts and the names of failing tests, verbatim.
3. Do not modify files, install packages, or run any other command. If the tests cannot run, report the error verbatim.
