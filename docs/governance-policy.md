# Agent Governance Policy

Version: v1.0.0  
Last updated: 2026-06-06  
Reviewed by: Repository Owner

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map (`docs/routing-and-tool-grant-map.md`)
- Near-miss patterns observed in calibration (`docs/calibration-log.md`, section: Near-miss patterns)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit and justified. Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant, a concrete justification, and confirmation that the grant does not conflict with any near-miss pattern in the calibration log.

## Role: implementer

**Version:** v1.0.0  
**Defined in:** `.agents/implementer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | YES | Implementer must record decisions. |
| read_entry | storage | YES | Implementer reads prior decisions. |
| list_entries | storage | YES | Implementer checks existing state. |
| update_entry | storage | YES | Implementer updates state after changes. |
| delete_entry | storage | NO | Implementer must not remove project state (calibration-log.md, near-miss: implementer over-broad delete grant). |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | YES | Implementer retrieves reference documents for implementation context. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | YES | Core implementer responsibility. |
| draft-pr-description | NO | Owned by project-manager role. |
| summarize-session | YES | Implementer may summarize its own work. |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** Implementer does not require confidential data to perform implementation tasks.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:** Before running shell commands outside the test suite; before writing to any file outside the current feature branch scope.  
**Reason:** Implementation is reversible within the container; shell commands outside the test suite are higher risk.  
**Container permissions:** workspace read-write, memory mounted

## Role: reviewer

**Version:** v1.0.0  
**Defined in:** `.agents/reviewer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| read_entry | storage | YES | Reviewer reads decisions to review them. |
| list_entries | storage | YES | Reviewer checks what exists before reviewing. |
| write_entry | storage | NO | Reviewer must not change project state. |
| update_entry | storage | NO | Reviewer must not change project state. |
| delete_entry | storage | NO | Reviewer must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | YES | Reviewer retrieves reference documents for context. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | NO | Reviewer is read-only; running tests changes workspace state (calibration-log.md, near-miss: reviewer near-triggered run-tests). |
| draft-pr-description | NO | Owned by project-manager role. |
| summarize-session | YES | Reviewer may summarize its own review. |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** Reviewer does not require confidential data to review internal work.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Reviewer output is advisory only; it may not apply any change. Any action beyond producing review findings requires escalation to the orchestrator.  
**Reason:** A review role that can change state can quietly alter the work it is supposed to inspect independently.  
**Container permissions:** workspace read-only, memory omitted

## Role: tester

**Version:** v1.0.0  
**Defined in:** `.agents/tester.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| read_entry | storage | YES | Tester reads decisions and test context. |
| list_entries | storage | YES | Tester lists available state before reporting. |
| write_entry | storage | NO | Tester reports results but does not change stored project state. |
| update_entry | storage | NO | Tester reports results but does not update stored project state. |
| delete_entry | storage | NO | Tester must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | YES | Tester retrieves internal references for test context. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | YES | Core tester responsibility. |
| draft-pr-description | NO | Owned by project-manager role. |
| summarize-session | YES | Tester may summarize its own work. |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** Tester does not require confidential data to run or report tests.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Any write to tracked repository files or stored project state.  
**Reason:** Testing should inspect and report without altering source-controlled files.  
**Container permissions:** workspace read-only, memory omitted

## Role: project-manager

**Version:** v1.0.0  
**Defined in:** `.agents/project-manager.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| read_entry | storage | YES | Project-manager reads project state for summaries. |
| list_entries | storage | YES | Project-manager lists state before drafting descriptions. |
| write_entry | storage | NO | Project-manager does not update project state directly. |
| update_entry | storage | NO | Project-manager does not update project state directly. |
| delete_entry | storage | NO | Project-manager must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | NO | Project-manager does not perform retrieval in this sample workflow. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | NO | Planning and description work does not run tests. |
| draft-pr-description | YES | Project-manager owns pull-request descriptions. |
| summarize-session | YES | Project-manager may summarize its own work. |

### Data classification ceiling

**Maximum level:** public  
**Reason:** Retrieval is denied for this role; public is recorded as the default ceiling.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Before publishing text externally or changing repository state.  
**Reason:** Project-manager outputs are human-facing and should remain advisory.  
**Container permissions:** workspace read-only, memory omitted

## Role: orchestrator

**Version:** v1.0.0  
**Defined in:** `.agents/orchestrator.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | YES | Orchestrator records workflow decisions. |
| read_entry | storage | YES | Orchestrator reads state while coordinating roles. |
| list_entries | storage | YES | Orchestrator lists state while coordinating roles. |
| update_entry | storage | YES | Orchestrator updates state after coordinated work. |
| delete_entry | storage | YES | Orchestrator manages state lifecycle and is the only role permitted to delete. |
| audit_read | storage | YES | Orchestrator inspects authorization denials. |
| retrieve | retrieval | YES | Orchestrator retrieves references when coordinating. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | YES | Orchestrator may invoke tests while coordinating. |
| draft-pr-description | YES | Orchestrator may invoke PR drafting while coordinating. |
| summarize-session | YES | Orchestrator may summarize workflow state. |

### Data classification ceiling

**Maximum level:** confidential  
**Reason:** Orchestrator coordinates the full workflow and audits policy enforcement.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:** Before destructive operations, external publication, or any action outside the protected workflow.  
**Reason:** Orchestration is reversible within the container, but lifecycle and publication actions need human accountability.  
**Container permissions:** workspace read-write, memory mounted
## Role: documentation-writer

**Version:** v1.0.0
**Defined in:** `agents/documentation-writer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| read_entry | storage | YES | Documentation-writer reads project state for accurate documentation. |
| list_entries | storage | YES | Documentation-writer checks available project state before documenting it. |
| write_entry | storage | NO | Documentation-writer must not change stored project state; its job is documentation only. |
| update_entry | storage | NO | Documentation-writer must not alter existing project state under least privilege. |
| delete_entry | storage | NO | Documentation-writer must not remove project state; delete access could cause loss of information the role is only meant to describe. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator and is not required for documentation work. |
| retrieve | retrieval | YES | Documentation-writer retrieves approved reference documents needed for documentation. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| run-tests | NO | Documentation work does not require test execution, and running tests can change workspace state. |
| draft-pr-description | NO | Pull-request descriptions are owned by the project-manager role. |
| summarize-session | YES | Documentation-writer may summarize its own documentation work. |

### Data classification ceiling

**Maximum level:** internal
**Reason:** Documentation-writer may need internal project references but does not require confidential data.

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Before publishing documentation externally, changing repository state, or requesting access above the internal classification ceiling.
**Reason:** Documentation output should remain advisory and reviewable before it affects project state or external audiences.
**Container permissions:** workspace read-only, memory omitted

## Deterministic conversion history

- `validator`: converted from agent to deterministic code. See `docs/adr/ADR-001-json-schema-validation-deterministic-conversion.md`. No MCP access required.

## Policy maintenance

**Drift detection.** The policy test suite (`eval/test_policy.py`) runs automatically:

- locally, on every commit that changes a governed file, through the pre-commit hook, and
- on the shared repository, on every push and pull request, through CI.

**Cadence.** Governed changes are checked as they happen. A scheduled full run should be added quarterly if the deployed environment can drift outside of commits.

**Ownership.** The author of a change that touches a governed artifact resolves any drift before merge. The policy owner reviews and approves changes to this policy.

**Escalation in production.** If drift is detected in a deployed environment, treat it as an incident: revert or hotfix the offending change, notify the policy owner or on-call engineer, and record the event in the audit trail or incident log. No governed change ships while the suite is failing.
