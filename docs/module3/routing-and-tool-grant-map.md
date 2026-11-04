# MarketRadar Routing and Tool-Grant Map

| Role | Receives from Orchestrator | Produces | Tools Granted | Tools Denied | Context Isolation Reason | Autonomy |
|---|---|---|---|---|---|---|
| Planner | Task, acceptance criteria, repository context | Implementation plan and explicit file list | Read, Grep, Glob | Edit, Write, Bash | Planning should not change code or execute commands | High within planning scope |
| Implementer | Approved plan, file list, acceptance criteria | Code changes and implementation summary | Read, Grep, Glob, Edit, Write | Test execution and unrelated tools | Implementation is limited to the approved plan | Medium |
| Tester | Acceptance criteria, implementation summary, modified files | PASS/FAIL verification report | Read, Grep, Glob, Bash | Edit, Write | Testing must remain independent from implementation | High within verification scope |
| Orchestrator | Task plus outputs from each role | Routing decisions, approvals, retries, escalation | Delegation and evaluation only | Specialized implementation work | Coordinates specialists instead of doing their work | High for routing |
 
## Routing

1. Orchestrator sends the task to Planner.
2. Planner returns a plan and explicit file list.
3. Human approves the plan.
4. Orchestrator sends the approved plan to Implementer.
5. Implementer makes the approved changes and returns a summary.
6. Orchestrator sends the implementation to Tester.
7. Tester returns PASS or FAIL.
8. On PASS, the workflow completes.
9. On FAIL, the Orchestrator routes the findings back to Implementer.
10. After changes, Tester verifies again.
11. Repeated failure is escalated to the human.

## Current policy clarification (Module 4.1)

The role table and Routing list above are the historical Module 3 record. They are kept unchanged. `docs/governance-policy.md` names this map as its basis, so this section states the current policy. Where the sections above conflict with this section or with `docs/governance-policy.md`, this section and the policy govern. The policy's per-role entries are authoritative for exact grants.

### Autonomy

The Module 3 ratings described how much freedom a role had within its scope. Current policy rates what a role can bring about without a human.

| Role | Module 3 rating (historical) | Current policy rating |
|---|---|---|
| Planner | High within planning scope | Low |
| Implementer | Medium | Medium |
| Tester | High within verification scope | Low |
| marketradar-code-reviewer | (not in the Module 3 table) | Low |
| project-manager | (not in the Module 3 table) | Low |
| Orchestrator | High for routing | Medium |

### Tool-grant clarifications for the historical rows

- **Planner:** also granted `retrieve` at `internal`.
- **Implementer:** also granted `retrieve` at `internal`, and storage `write_entry` for one `internal` lesson per change. Edit and Write are limited to the approved file list. This limit is not yet enforced (policy D13). Bash is denied.
- **Tester:** Bash is limited to the project's validation commands (`npm run test`, `npm run lint` and the type check, in `tracker-api/` and `tracker-client/`), and all other Bash use is denied. This scoping is not yet enforced (policy D5). Also granted `retrieve` at `internal`.
- **Orchestrator:** "Delegation and evaluation only" means:
  - Read, Grep and Glob
  - the Agent tool
  - storage `read_entry`, `list_entries` and `audit_read`
  - the `summarize-session` skill

  Edit and Write on application code, and Bash, are denied. This is not yet enforced (policy D14).
- **All roles:** direct Read of `.memory/reference/` files above the role's ceiling is denied (policy D8).

### Additional roles

| Role | Receives from Orchestrator | Produces | Tools Granted | Tools Denied | Context Isolation Reason | Autonomy |
|---|---|---|---|---|---|---|
| marketradar-code-reviewer | Changed files or diff, approved plan, acceptance criteria | Up to five findings (severity, location, issue, impact, fix) and an overall assessment | Read, Grep, Glob; `retrieve` at `internal` | Edit, Write, Bash (Bash is still granted in frontmatter; policy D4), all storage operations | Review must stay independent of the work it inspects | Low (advisory) |
| project-manager | Task identifier, implementation summary, code review outcome, test results, requested final status | Task outcome report and one `internal` `task_outcome` storage record | Storage `write_entry` only | Read, Grep, Glob, Edit, Write, Bash, `retrieve` | Records the outcome from the evidence it is given, not from its own inspection | Low |

### Current routing

Steps 1–11 of the historical Routing list remain the base sequence. When a task or its acceptance criteria require review or outcome recording, the Orchestrator extends the sequence as follows:

1. Orchestrator sends the task to Planner.
2. Planner returns a plan and explicit file list.
3. Human approves the plan.
4. Orchestrator sends the approved plan to Implementer.
5. Implementer makes the approved changes and returns a summary.
6. *If review is required:* Orchestrator sends the changes to marketradar-code-reviewer. The Reviewer returns findings and an overall assessment.
   - The findings are advisory: the Reviewer cannot change or block the work.
   - The Orchestrator routes High-severity findings, or a rejecting assessment, back to Implementer (step 5).
   - The Orchestrator escalates disagreements to the human.
   - A rejecting review never becomes an automatic approval.
7. Orchestrator sends the implementation to Tester.
8. Tester returns PASS or FAIL.
9. On FAIL, the Orchestrator routes the findings back to Implementer. After changes, review (if required) and testing run again. Repeated failure is escalated to the human.
10. *If outcome recording is required:* once the required stages have finished, the Orchestrator sends the evidence to project-manager. The project-manager records the outcome. It does not record completion if review or testing failed, and it reports a blocker if evidence is missing.
11. The workflow completes only on Tester PASS with no unresolved failed review.

Evidence and limits:
- The order Implementer → Reviewer → Tester → Project Manager is the frozen HO-02 path (`docs/module3/holdout-task-set.md` line 23). It has not been run end to end: HO-02 was BLOCKED at the approval gate (`docs/module3/calibration-log.md` lines 305–308 and 360).
- Both roles are conditional. HO-03, HO-04 and HO-06 use paths without one or both of them (`docs/module3/holdout-task-set.md` lines 35, 46 and 69).
- The failed-review routing rule is inferred from `.claude/agents/project-manager.md` line 17 (never record completion over a failed review), HO-05 assertion 4 (`docs/module3/holdout-task-set.md` line 62: a disagreement does not automatically produce approval) and the policy's advisory Reviewer entry. It has not been observed in a run.
- The Project Manager's storage write cannot succeed today (policy D2, D9).
- `CLAUDE.md` "Standard Sequence" (lines 206–216) is unchanged and does not yet route either role. An Orchestrator that follows `CLAUDE.md` literally will not invoke them. Changing `CLAUDE.md` is a separate, behaviour-changing decision.
