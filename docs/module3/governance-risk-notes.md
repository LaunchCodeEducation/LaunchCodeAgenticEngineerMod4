# Governance Risk Notes — MarketRadar Module 3 Calibration

**Date:** 2026-11-03
**Purpose:** Input to `docs/governance-policy.md` (Module 4.1). Lists the agent access-control findings recorded in the Module 3 calibration log, so that future grant changes can be checked against them.

## Near-miss section status

`docs/module3/calibration-log.md` has no "Near-miss patterns" section, and it labels no incident as a near-miss. **No near-miss patterns are listed here for that reason.**

The entries below are documented access-control *findings* from the Module 3 calibration and holdouts. The source does not call them near-misses, and they must not be cited as near-misses.

## Findings

Line references are to `docs/module3/calibration-log.md` unless stated otherwise.

### B1. Unscoped Tester Bash

The calibration fix restored `Bash` to the Tester. That grant gives the whole shell, so Bash can change files even though `Edit` and `Write` are excluded. Plan mode partly limited it when the Tester ran as an orchestrated subagent (9 Tester Bash calls denied in HO-03, 3 in HO-04). The standalone `dontAsk` runs used for calibration and regression did not limit it.

- **Risk:** a verification role with unscoped shell access can change the workspace it is supposed to verify independently.
- **Evidence:**
  - `docs/module3/calibration-log.md` lines 52–54 and 56
  - `docs/module3/module-3-reflection.md` §4, lines 69–76 ("Why broad Bash is a risk")
- **Status:** the Tester made no writes in any post-fix run (line 56). That is observed behaviour, not enforcement. Scoping Bash to `npm run lint` and `npm run test` was proposed but not implemented (line 60).

### B2. `no_source_writes` cannot see writes made through Bash

The `no_source_writes` check looks only for named write tools, so it cannot detect a file write made through Bash.

- **Risk:** the evaluation gate can report "no source writes" even when files were changed through Bash.
- **Evidence:**
  - `docs/module3/calibration-log.md` line 55
  - `docs/module3/module-3-reflection.md` §4, line 74
- **Status:** detecting Bash file writes in the evaluator was proposed but not implemented (line 64).

### B3. Code Reviewer holds Bash it does not need

The Code Reviewer has Bash, which a read-only review does not need. In HO-06 it used Bash only for `ls`, `grep` and `wc`.

- **Risk:** a read-only review role holding a state-changing capability can alter the work it inspects.
- **Evidence:**
  - `docs/module3/calibration-log.md` lines 57, 319 and 364
  - `docs/module3/module-3-reflection.md` §4, lines 78–81
- **Status:** removing Bash from the Code Reviewer was proposed but not implemented (line 61). The agent is now `.claude/agents/marketradar-code-reviewer.md` (renamed during migration; see `docs/module3/migration-notes.md` §1).

### B4. Direct `Read` bypassed the classification ceiling (HO-06)

In HO-06, `.memory/reference/lesson-session-data-security.md`, which is classified `confidential`, was read directly with `Read`. That bypassed the `internal` ceiling the retrieval MCP server is meant to enforce. **This actually happened. It is a finding, not a near-miss.**

- **Risk:** a role that can read files directly can pull material above its classification ceiling into its context, bypassing MCP enforcement.
- **Evidence:**
  - `docs/module3/calibration-log.md` line 321 (HO-06 assertion 3), line 352 and line 364
  - Proposed mitigation, deny direct `Read` of `.memory/reference/` (not implemented): line 63
  - Contrast: in HO-01 the Planner refused the same fallback, saying a direct read would bypass the retrieval check (line 289)
  - `docs/module3/module-3-reflection.md` §4, line 92
- **Note on attribution:** the log is not consistent. Line 321 says "The Planner" read the file. Line 352 says "an agent" did. The reflection (line 92) says "the Planner". These notes do not resolve the discrepancy; the HO-06 transcript that would settle it was not migrated (see Evidence provenance).

### B5. Retrieval ceiling enforcement was never exercised

Every subagent `mcp__retrieval__retrieve` call in the post-calibration holdouts was denied by Claude Code's permission mode (`plan` or `dontAsk`) before it reached the MCP server. The server's role and classification checks therefore never ran.

- **Risk:** the role ceilings in `mcp/roles.allowlist.json` are untested and cannot be counted as a working control.
- **Evidence:**
  - `docs/module3/calibration-log.md` line 58, lines 336–353 (denial counts per holdout; line 351 states enforcement was "never exercised") and line 382
  - `docs/module3/module-3-reflection.md` §4, lines 83–92
- **Status:** explicitly allowing retrieval for the roles that need it was proposed but not implemented (line 62). `mcp/` is reference-only in Module 4 and is not wired in (`docs/module3/migration-notes.md` §1).

## Excluded

- **HO-06 unauthenticated `/debug` endpoints** (line 364): an application-security finding, not an agent-governance finding.
- **Induced Tester Bash-removal fault** (lines 14–45): a deliberately induced calibration fault, not a near-miss or a governance finding.

## Evidence provenance

- No evaluation was re-run for these notes. Line references are to the 2026-11-02 revision of `docs/module3/calibration-log.md`.
- The holdout transcripts (`eval/evidence/calibration/holdout/*.jsonl`) were **not migrated** (`docs/module3/migration-notes.md` §3). For B3, B4 and B5, the log text and the reflection are the only evidence in this repository.
- Paths in the log are historical. `eval/evidence/calibration/*` now lives at `eval/module3/evidence/calibration/*`, and `docs/module-3-reflection.md` is now `docs/module3/module-3-reflection.md`.

## Open item: policy basis mismatch

The preamble of `docs/governance-policy.md` names `docs/module3/routing-and-tool-grant-map.md` and `docs/module3/calibration-log.md` as its basis. However:

- The per-role sections cover the Module 4 `.agents/` roles and MCP operations from `docs/routing-and-tool-grant-map.md`, not the Module 3 roles.
- Its near-miss citations (`docs/governance-policy.md` lines 40 and 85) refer to patterns that exist only in `docs/calibration-log.md` ("Near-miss patterns for Module 4 governance"), not in the named basis file.
- The basis file contains no near-miss patterns, so the PR rule's check against "any near-miss pattern in the calibration log" currently has no MarketRadar entries to check against.

Reconciliation is deferred. See the role model mismatch in `docs/module3/migration-notes.md` §6, item 8.
