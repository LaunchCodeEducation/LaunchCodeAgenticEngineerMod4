# Agent Governance Policy

Version: v1.0.0  
Last updated: 2026-11-09  
Author: swarna  
Reviewed by: swarna (FashionMate agentic harness owner)

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map (`docs/routing-and-tool-grant-map.md`)
- Near-miss patterns observed in calibration (`docs/calibration-log.md`, section: Near-miss patterns)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit and justified. Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant, a concrete justification, and confirmation that the grant does not conflict with any near-miss pattern in the calibration log.
Near-miss references below point to `docs/calibration-log.md`, section "Near-miss patterns for Module 4 governance", and to the matching risk statements in `docs/near-miss-risks.md`. Denials without a near-miss reference stand on least-privilege grounds: the role's defined job does not need the operation.

Roles in this orchestration (7): orchestrator, planner, implementer, reviewer, tester, project-manager, dependency-auditor.

## Role: orchestrator

**Version:** v1.0.0
**Defined in:** .claude/agents/orchestrator.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Orchestrator reads subagent results to judge each phase gate |
| list_entries  | storage   | YES     | Orchestrator checks what state exists before delegating |
| write_entry   | storage   | YES     | Orchestrator records handoff briefs and the final run summary |
| update_entry  | storage   | YES     | Orchestrator updates the run record as phases pass or fail |
| delete_entry  | storage   | YES     | Orchestrator is the only role that manages entry lifecycle (e.g. removing a superseded record). Requires a human checkpoint (see Autonomy). This is the only role with delete, closing the over-broad grant risk for every other role (calibration-log.md, near-miss: over-broad grant only caught because a task asked for a delete) |
| audit_read    | storage   | YES     | Orchestrator must inspect denied operations in the audit log to detect policy violations |
| retrieve      | retrieval | YES     | Orchestrator retrieves reference docs to brief subagents; ceiling confidential |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | NO                   | Owned by implementer and tester; the orchestrator delegates and never does subagent work (CLAUDE.md) |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Orchestrator summarizes the run into docs/run-summary.md |
| rebuild-and-deploy   | YES                  | Only with a human checkpoint; deploy is outward-facing |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed to coordinate the workflow |

### Data classification ceiling

**Maximum level:** confidential
**Reason:** The orchestrator coordinates all roles and may need confidential context to route work correctly; it never forwards confidential material to roles capped at internal. No role is granted secret.

### Autonomy level

**Level:** medium
**Conditions for human checkpoint:** After the planner returns (plan approval); before the project-manager updates the ticket; before any delete_entry; before rebuild-and-deploy; whenever two reviewers return conflicting verdicts on the same section, the orchestrator must escalate instead of choosing one (calibration-log.md, near-miss: conflicting reviewers rarely exercised); a run may not be reported as passing on deterministic checks alone when the rubric suite has not run (calibration-log.md, near-miss: first dev run passed 14/14 deterministic but scored 0/5 on the rubric).
**Reason:** Coordination is reversible inside the container, but lifecycle, publication, and approval decisions need human accountability.
**Container permissions:** workspace read-write, memory mounted

## Role: planner

**Version:** v1.0.0
**Defined in:** .claude/agents/planner.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Planner reads prior decisions before planning |
| list_entries  | storage   | YES     | Planner checks existing project state |
| write_entry   | storage   | NO      | Planner produces a plan in its handoff, not in project state; the orchestrator records it |
| update_entry  | storage   | NO      | Planner must not change project state |
| delete_entry  | storage   | NO      | Planner must not remove project state (calibration-log.md, near-miss: over-broad grant) |
| retrieve      | retrieval | YES     | Planner must ground the plan in retrieved reference docs; ceiling internal |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | NO                   | Planner does not execute code |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Planner may summarize its own work |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed for planning |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Planning uses internal project docs and lessons; it does not need confidential data.

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Every plan is shown to the human for approval before any code is written (CLAUDE.md human-in-the-loop checkpoint). The planner works only from its scoped handoff and may not rely on private context from other roles (calibration-log.md, near-miss: context bleed only checked when a canary is planted).
**Reason:** A wrong plan propagates into every later phase, so it is reviewed before work begins.
**Container permissions:** workspace read-only, memory omitted

## Role: implementer

**Version:** v1.0.0
**Defined in:** .claude/agents/implementer.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| write_entry   | storage   | YES     | Implementer must record decisions |
| read_entry    | storage   | YES     | Implementer reads prior decisions |
| list_entries  | storage   | YES     | Implementer checks existing state |
| update_entry  | storage   | YES     | Implementer updates state after changes |
| delete_entry  | storage   | NO      | Implementer must not remove project state (calibration-log.md, near-miss: implementer over-broad delete grant, cycle 6, fix 034729f) |
| retrieve      | retrieval | YES     | Implementer retrieves reference docs; ceiling internal |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | YES                  | Core implementer responsibility |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Implementer may summarize its own work |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed for implementation |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Implementer does not require confidential data to perform implementation tasks.

### Autonomy level

**Level:** medium
**Conditions for human checkpoint:** Before running any shell command outside the test suite; before writing to any file not in the current feature branch scope.
**Reason:** Implementation is reversible within the container; shell commands outside the test suite are higher risk.
**Container permissions:** workspace read-write, memory mounted

## Role: reviewer

**Version:** v1.0.0
**Defined in:** .claude/agents/reviewer.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Reviewer reads decisions to review them |
| list_entries  | storage   | YES     | Reviewer checks what exists before reviewing |
| write_entry   | storage   | NO      | Reviewer must not change project state |
| update_entry  | storage   | NO      | Reviewer must not change project state |
| delete_entry  | storage   | NO      | Reviewer must not remove project state (calibration-log.md, near-miss: over-broad grant) |
| retrieve      | retrieval | YES     | Reviewer retrieves reference docs for context; ceiling internal |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | NO                   | Reviewer is read-only; running tests changes workspace state |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Reviewer may summarize its own review |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed for review |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Reviewer does not require confidential data to review internal work.

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Reviewer output is advisory only; it may not apply any change. Any action beyond producing review findings requires escalation to the orchestrator. When parallel reviewers disagree, the reviewer reports its verdict and the orchestrator escalates to a human (calibration-log.md, near-miss: conflicting reviewers).
**Reason:** A review role that can change state can quietly alter the very work it is supposed to inspect independently.
**Container permissions:** workspace read-only, memory omitted

## Role: tester

**Version:** v1.0.0
**Defined in:** .claude/agents/tester.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Tester reads the implementation entry it verifies |
| list_entries  | storage   | YES     | Tester checks which entries exist for the run |
| write_entry   | storage   | NO      | Tester reports results in its handoff; it must not change project state |
| update_entry  | storage   | NO      | Tester must not change project state |
| delete_entry  | storage   | NO      | Tester must not remove project state (calibration-log.md, near-miss: over-broad grant) |
| retrieve      | retrieval | YES     | Tester retrieves the standards it verifies against; ceiling internal |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | YES                  | Core tester responsibility |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Tester may summarize its own results |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed for testing |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Testing internal features does not require confidential data.

### Autonomy level

**Level:** medium
**Conditions for human checkpoint:** Tester may run the test suite without approval; any command outside the test suite, or any change to test fixtures, requires escalation to the orchestrator.
**Reason:** Running tests is reversible and is the tester's job; altering what is tested would undermine the result.
**Container permissions:** workspace read-only, memory omitted

## Role: project-manager

**Version:** v1.0.0
**Defined in:** .claude/agents/project-manager.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Project manager reads the run results it reports on |
| list_entries  | storage   | YES     | Project manager checks what the run produced |
| write_entry   | storage   | NO      | Project manager reports through the ticket and run summary, not project state. Resolves a conflict with the earlier grant map, which granted write_entry; the map was corrected (see below) |
| update_entry  | storage   | NO      | Project manager must not change project state |
| delete_entry  | storage   | NO      | Project manager must not remove project state (calibration-log.md, near-miss: over-broad grant) |
| retrieve      | retrieval | NO      | Project manager does not perform retrieval |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | NO                   | Owned by implementer and tester |
| draft-pr-description | YES                  | Project manager owns the PR description |
| summarize-session    | YES                  | Project manager may summarize the run |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | YES                  | Project manager owns status communication; requires human confirmation |
| send-email           | YES                  | Project manager owns status communication; requires human confirmation |
| check-gmail          | NO                   | Reading the inbox is not needed to report status |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Status reporting uses internal run results only; nothing confidential may be sent outward.

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Before updating the ticket, sending any Slack message, or sending any email (CLAUDE.md human-in-the-loop checkpoint: changing the shared ticket is consequential and outward-facing).
**Reason:** Everything this role does is visible outside the team, so a human confirms each outward action.
**Container permissions:** workspace read-only, memory omitted

## Role: dependency-auditor

**Version:** v1.0.0
**Defined in:** agents/dependency-auditor.md

### MCP server and operation access

| Operation     | Server    | Granted | Justification / Denial reason |
|---------------|-----------|---------|-------------------------------|
| read_entry    | storage   | YES     | Auditor reads prior dependency decisions so it does not re-flag an accepted exception |
| list_entries  | storage   | YES     | Auditor checks which decisions exist before reporting |
| write_entry   | storage   | NO      | Auditor reports findings in its handoff; it records no project state (least privilege) |
| update_entry  | storage   | NO      | Auditor must not rewrite an existing decision, e.g. silently marking a vulnerable dependency as accepted (least privilege) |
| delete_entry  | storage   | NO      | Auditor must not remove project state (calibration-log.md, near-miss: over-broad grant; only caught because a task asked for a delete) |
| retrieve      | retrieval | YES     | Auditor retrieves internal standards and lessons that define what counts as a dependency problem; ceiling internal |

### Skill activation scope

| Skill                | Activation permitted | Reason if denied |
|----------------------|----------------------|------------------|
| run-tests            | NO                   | Auditing reads manifests; running tests writes output and changes workspace state, and is owned by implementer and tester |
| draft-pr-description | NO                   | Owned by project-manager role |
| summarize-session    | YES                  | Auditor may summarize its own audit |
| rebuild-and-deploy   | NO                   | Outward-facing; orchestrator only, with checkpoint |
| send-slack-message   | NO                   | External communication is owned by project-manager |
| send-email           | NO                   | External communication is owned by project-manager |
| check-gmail          | NO                   | Not needed for auditing |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Dependency rules and standards are internal documents. Confidential material (for example the cost breakdown and open security exposures in the reference corpus) is not needed to judge a dependency, and an auditor that could read open exposures could leak them into a report that travels further than the source (docs/near-miss-risks.md, risk 3: a role gaining access it was never granted).

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Every finding is advisory. Any dependency change the auditor recommends is handed to the orchestrator, routed to the implementer, and reviewed; the auditor never applies it. The auditor works only from its scoped handoff (calibration-log.md, near-miss: context bleed only checked when a canary is planted).
**Reason:** A dependency bump is a code change with supply-chain risk, so it must go through implementation and review rather than be applied by the role that found it.
**Container permissions:** workspace read-only, memory omitted

## Conflicts resolved against the routing map (2026-11-09)

- **project-manager write_entry:** the earlier `docs/routing-and-tool-grant-map.json` granted it; this policy denies it on least-privilege grounds, matching `mcp-servers/storage/allow-list.json`. The map was corrected. Known gap: holdout task HO-07 asserts that the project manager makes exactly one write_entry; the locked holdout task is not edited, so HO-07 is expected to fail that assertion until the holdout set is formally revised.
- **planner:** missing from `mcp-servers/storage/allow-list.json` and `mcp-servers/retrieval/allow-list.json`; it must be added there (read_entry, list_entries, retrieve at internal) when enforcement is configured.
- **tester and reviewer:** the earlier map omitted list_entries (and retrieve for tester); the map now matches this policy.

## Deterministic conversion history

- `validator`: converted from agent to deterministic code. See `docs/adr/ADR-001-json-schema-validation-deterministic-conversion.md`. No MCP access required.

## Policy maintenance

**Drift detection.** The policy test suite (`eval/test_policy.py`) runs automatically:

- locally, on every commit that changes a governed file, through the pre-commit hook, and
- on the shared repository, on every push and pull request, through CI.

**Cadence.** Governed changes are checked as they happen. A scheduled full run should be added quarterly if the deployed environment can drift outside of commits.

**Ownership.** The author of a change that touches a governed artifact resolves any drift before merge. The policy owner reviews and approves changes to this policy.

**Escalation in production.** If drift is detected in a deployed environment, treat it as an incident: revert or hotfix the offending change, notify the policy owner or on-call engineer, and record the event in the audit trail or incident log. No governed change ships while the suite is failing.
