# 

Iteration Log

## Run — storage grant/denial verification

- Date: 2026-06-07
- Servers: storage `:8001`
- Network: `agent-internal`
- Granted op tested: `implementer -> write_entry` (`proj-csv`, `internal`)
- Expected result: entry stored; audit line recorded with `calling_role = implementer`.
- Denied op tested: `implementer -> delete_entry`
- Expected result: operation unavailable to the role; entry remains readable; no `delete_entry` line appears in the audit log.
- Status: ready to verify in the course harness.

## Run — end-to-end integration (storage + retrieval live)

- Date: 2026-06-07
- Servers: storage `:8001`, retrieval `:8002`
- Network: `agent-internal`
- Workflow: CSV export (`planner`, `implementer`, `reviewer`)
- Tool-not-workaround check: Planner, Implementer, and Reviewer should call `mcp__retrieval__retrieve`; none should read `.memory/reference/` directly.
- Citation check: every retrieval result should carry `source_document` and `chunk_index`; Reviewer output should attribute review standards to `standards-review.md`.
- Ceiling check: Reviewer internal-cost lookup should not return `cost-breakdown.md`.
- Audit check: `write_entry` records should exist for Planner, Implementer, and Reviewer with `calling_role` populated.
- Status: ready to verify in the course harness.

## Run 0 — Tool-scope verification (pre-run check)

- Date: 2026-11-03
- Role tested: implementer
- Tool attempted: mcp__coursetools__task_tracker
- Expected: denied (task_tracker is owned by project-manager)
- Result: blocked at the harness layer. task_tracker was not in the
  implementer's tools allow-list, so the agent never attempted the call and
  the request never reached the server. Tools available to the implementer:
  file_read, file_write, codebase_search.
- Conclusion: the denial is enforced, not merely declared. The server-side
  allow-list was not exercised because the harness stopped the call first.
- Side finding: implementer.md also lists mcp__storage__* and
  mcp__retrieval__* tools, but those MCP servers are not registered in this
  project, so they are unavailable.


## Run 1 — CSV export, full orchestration (2026-11-03)

Outcome: completed. Plan approved at checkpoint, one review loop, tests
passed (aggregate), ticket CSV-EXPORT-1 set to Done after human confirmation.

What worked as designed
- Order: planner → implementer → reviewer → tester → project-manager.
- Both human checkpoints fired (plan approval, before ticket update).
- Halt and escalate: planner found example-task-app/ missing; orchestrator
  paused and asked instead of scaffolding a fake app.
- Evaluation gate: after an implementer API error, the orchestrator read the
  files to verify completion before moving on.
- Loop: reviewer reported 4 issues (>3), orchestrator looped to implementer;
  round 2 review dropped to 1 low issue and passed.
- Tool scoping: only project-manager called task_tracker; no role called a
  tool outside its grant.

### Misfire 1: missing ticket ID (routing / handoff gap)
- What happened: project-manager could not update the ticket because no
  ticket ID was passed to it. Human had to supply one mid-run.
- Roles involved: orchestrator (brief), project-manager.
- Cause: neither the PRD nor the orchestrator's standard sequence included a
  ticket ID as a required input for project-manager.
- Proposed fix: add a Ticket field to docs/prd.md, update the orchestrator's
  standard sequence so project-manager receives the ticket ID from the PRD,
  and add a Ticket ID field to the orchestrator-to-subagent template.

### Misfire 2: handoff templates not found (output format risk)
- What happened: orchestrator reported the templates directory was not
  present and wrote its own briefs.
- Roles involved: orchestrator.
- Cause: templates live in .memory/knowledge/; likely not visible to the
  coursetools file_read tool, or the orchestrator looked in the wrong path.
- Also: written briefs exist only for planner and implementer
  (docs/orchestrator/). Reviewer, tester, and project-manager briefs were not
  saved, so their context cannot be audited after the run.
- Proposed fix: confirm the path from inside the container, reference the
  exact path in the orchestrator instructions, and require a saved brief for
  every subagent.

### Misfire 3: context bleed via memory file
- What happened: planner read .memory/reference/security-export-visibility.md
  (not in its brief); the orchestrator then passed "ignore this file" into the
  implementer's brief, adding context the implementer did not need.
- Roles involved: planner, orchestrator, implementer.
- Proposed fix: limit planner search to the app path; do not mention
  irrelevant files in downstream briefs.

### Misfire 4: review loop rule too blunt
- What happened: 4 issues (0 high, 1 medium, 3 low) forced a full rework
  round.
- Proposed fix: loop only on any high issue or more than one medium issue.

### Misfire 5: reviewer missing human-approval context
- What happened: reviewer flagged the status-message change as beyond the
  PRD, though the human approved it at the plan checkpoint.
- Proposed fix: include human-approved plan decisions in the reviewer's brief.

### Misfire 6: thin test evidence
- What happened: test_runner returned aggregate PASS only; the gate passed on
  a summary that could not be checked per test.
- Proposed fix: require per-test output in the tester's output format, or run
  npm test manually to confirm.

### Observation: file outside the approved plan
- tests/app.test.js was created in round 2 to satisfy reviewer feedback. It
  was reasonable, but it went past the approved file list with no human check.

### Environment issue
- example-task-app/ was missing from the working copy; restored with
  git checkout f320153 -- module_3/example-task-app.

### Rerun (project-manager phase only) — 2026-11-04
- Change tested: ticket ID added to docs/prd.md ("Ticket: CSV-EXPORT-1");
  orchestrator v1.1.0 passes it to project-manager; template has a
  Ticket ID field.
- Result: orchestrator read CSV-EXPORT-1 from the PRD and passed it to
  project-manager without asking the human. The human checkpoint before the
  ticket update still fired. No other subagents ran. Fix holds for Misfire 1.
- Watch for: no regression observed; other phases were not re-run.


