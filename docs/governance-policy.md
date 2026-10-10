# Agent Governance Policy

Version: v1.0.0  
Last updated: 2026-10-01  
Reviewed by: Vara

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map (`docs/routing-and-tool-grant-map.md`)
- Near-miss patterns observed in calibration (`docs/calibration-log.md`, section: Near-miss patterns)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit and justified. Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant, a concrete justification, and confirmation that the grant does not conflict with any near-miss pattern in the calibration log.

## Role: orchestrator

**Version:** v1.0.0
**Defined in:** agents/appt-orchestrator.md
**Container permissions:** workspace read-write, memory mounted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Coordinates; reads state to route work |
| list_entries | storage   | YES     | Checks what exists before delegating |
| write_entry  | storage   | YES     | May record run-level handoff/summary entries |
| update_entry | storage   | YES     | May correct a run-level entry it authored |
| delete_entry | storage   | YES     | Sole owner of entry lifecycle; destructive action kept to one auditable role (calibration-log.md, near-miss: implementer over-broad delete grant) |
| audit_read   | storage   | YES     | Must inspect what the enforcement point denied |
| retrieve     | retrieval | YES     | Needs full context to coordinate; ceiling confidential |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | NO        | Delegates execution to implementer/tester |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize the run it coordinated |

### Data classification ceiling
**Maximum level:** confidential
**Reason:** Coordinates across all roles and may need to reason over any lesson.

### Autonomy level
**Level:** medium
**Conditions for human checkpoint:** HALT after the planner for plan approval; HALT before finalizing any change (per its charter).
**Reason:** It drives irreversible delegation; human gates bound the blast radius.

## Role: planner

**Version:** v1.0.0
**Defined in:** agents/appt-planner.md
**Container permissions:** workspace read-only, memory omitted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | NO      | Proposes work; does not read project state (least-privilege) |
| list_entries | storage   | NO      | Same |
| write_entry  | storage   | NO      | Must not author state |
| update_entry | storage   | NO      | Must not mutate state |
| delete_entry | storage   | NO      | Must not remove state |
| retrieve     | retrieval | YES     | Needs reference lessons to plan; ceiling internal. (Requires adding `planner` to retrieval/allow-list.json — see enforcement step.) |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | NO        | Planning changes nothing in the workspace |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize its own plan |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Planning needs internal context only; confidential access would widen any leak (calibration-log.md, near-miss: retrieval zero-score fallback).

### Autonomy level
**Level:** low
**Conditions for human checkpoint:** Output is a proposed plan; it applies nothing. Orchestrator HALTs for human approval before implementation.
**Reason:** A plan is advisory; the human gate is at approval.

## Role: implementer

**Version:** v1.0.0
**Defined in:** agents/appt-implementer.md
**Container permissions:** workspace read-write, memory mounted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Reads prior decisions before changing code |
| list_entries | storage   | YES     | Checks existing state |
| write_entry  | storage   | YES     | Records the lesson/decision for a change |
| update_entry | storage   | YES     | Supersedes an outdated entry it owns |
| delete_entry | storage   | NO      | Must not remove project state; supersede via update instead (calibration-log.md, near-miss: implementer over-broad delete grant) |
| audit_read   | storage   | NO      | Not an auditor (least-privilege) |
| retrieve     | retrieval | YES     | Retrieves reference lessons; ceiling internal |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | YES       | Core implementer responsibility |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize its own work |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Implementation needs no confidential data; an internal ceiling means a retrieval miss cannot leak confidential material (calibration-log.md, near-miss: retrieval zero-score fallback).

### Autonomy level
**Level:** medium
**Conditions for human checkpoint:** Before any shell command outside the test suite; before writing any file outside the current feature-branch scope.
**Reason:** Code changes are reversible in-container; out-of-scope shell/writes are higher risk.

## Role: reviewer

**Version:** v1.0.0
**Defined in:** agents/appt-security-reviewer.md   (runs as AGENT_ROLE=reviewer)
**Container permissions:** workspace read-only, memory omitted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Reads decisions to review them |
| list_entries | storage   | YES     | Checks what exists before reviewing |
| write_entry  | storage   | NO      | Read-only role must not change project state (least-privilege) |
| update_entry | storage   | NO      | Same |
| delete_entry | storage   | NO      | Same |
| retrieve     | retrieval | YES     | Retrieves reference lessons for context; ceiling internal |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | NO        | Read-only role; running tests mutates the workspace it only inspects |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize its own review |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Reviews internal work; no confidential access required.

### Autonomy level
**Level:** low
**Conditions for human checkpoint:** Advisory only; may not apply changes. Any action beyond findings escalates to the orchestrator.
**Reason:** A review role that can change state can quietly alter the work it is meant to inspect.

## Role: tester

**Version:** v1.0.0
**Defined in:** agents/appt-tester.md
**Container permissions:** workspace read-only, memory omitted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Reads state to know what to test |
| list_entries | storage   | YES     | Checks existing entries |
| write_entry  | storage   | NO      | Reports pass/fail; must not mutate state (least-privilege) |
| update_entry | storage   | NO      | Same |
| delete_entry | storage   | NO      | Same |
| retrieve     | retrieval | YES     | Retrieves reference context; ceiling internal |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | YES       | Core tester responsibility |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize its own test run |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Testing internal work needs no confidential data.

### Autonomy level
**Level:** low
**Conditions for human checkpoint:** Reports results only; does not apply fixes. Failures route back through the orchestrator.
**Reason:** Separating test execution from code change keeps the verification signal trustworthy.
**Note:** The test-execution tool is not yet wired in this environment (recorded gap); this grant is written ahead of enforcement.

## Cross-cutting enforcement rules

These come from near-misses that are not per-role (calibration-log.md):
- Every storage/retrieval call MUST carry a resolved AGENT_ROLE. A call logging
  calling_role "unknown" is a policy violation; the server MUST reject it, never default-allow
  (near-miss: calling_role unknown / shared-process role / mis-set role).
- Retrieval MUST return empty on a zero-score query, never fall back to top_k
  (near-miss: retrieval zero-score fallback).

## Role: project-manager

**Version:** v1.0.0
**Defined in:** agents/appt-project-manager.md
**Container permissions:** workspace read-only, memory omitted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Reads decisions to report status and draft PR descriptions |
| list_entries | storage   | YES     | Checks what exists before reporting |
| write_entry  | storage   | NO      | Coordinates and reports; must not author project state (least-privilege) |
| update_entry | storage   | NO      | Must not mutate project state |
| delete_entry | storage   | NO      | Must not remove project state |
| audit_read   | storage   | NO      | Not an auditor (least-privilege) |
| retrieve     | retrieval | NO      | Works from storage state and the current change; does not perform reference retrieval (least-privilege) |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | NO        | Does not execute or change the workspace |
| draft-pr-description | YES       | This role owns PR descriptions |
| summarize-session    | YES       | May summarize the run for reporting |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Reports on internal work; no confidential access required, and retrieval is denied entirely.

### Autonomy level
**Level:** low
**Conditions for human checkpoint:** Produces reports and PR text only; applies no code or state changes. Any action beyond reporting escalates to the orchestrator.
**Reason:** A reporting role with no write path cannot alter the work it describes.

## Role: dependency-auditor

**Version:** v1.0.0
**Defined in:** agents/appt-dependency-auditor.md
**Container permissions:** workspace read-only, memory omitted

### MCP server and operation access
| Operation    | Server    | Granted | Justification / Denial reason |
|--------------|-----------|---------|-------------------------------|
| read_entry   | storage   | YES     | Reads prior dependency-audit lessons before reporting |
| list_entries | storage   | YES     | Checks which audit entries already exist |
| write_entry  | storage   | NO      | Reports findings only; must not author project state (least-privilege) |
| update_entry | storage   | NO      | Must not mutate stored state (least-privilege) |
| delete_entry | storage   | NO      | Destructive; reserved to orchestrator (calibration-log.md, near-miss: implementer over-broad delete grant) |
| audit_read   | storage   | NO      | Not an auditor of the audit log (least-privilege) |
| retrieve     | retrieval | YES     | Retrieves internal reference/security lessons; ceiling internal |

### Skill activation scope
| Skill                | Permitted | Reason |
|----------------------|-----------|--------|
| run-tests            | NO        | Reporting role; must not execute or change the workspace |
| draft-pr-description | NO        | Owned by project-manager role |
| summarize-session    | YES       | May summarize its own audit |

### Data classification ceiling
**Maximum level:** internal
**Reason:** Dependency metadata is not confidential; an internal ceiling means a retrieval miss cannot surface confidential material to this role (calibration-log.md, near-miss: retrieval zero-score fallback).

### Autonomy level
**Level:** low
**Conditions for human checkpoint:** Produces a findings report only; applies no upgrades or file changes. Any action beyond reporting escalates to the orchestrator.
**Reason:** An auditor that could act on its own findings might change dependencies no one reviewed; separating audit from action keeps the report trustworthy.
