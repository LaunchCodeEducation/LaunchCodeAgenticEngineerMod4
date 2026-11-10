# Agent Governance Policy

Version: v1.0.0  
Last updated: 2026-11-03  
Reviewed by: Hector Trillo

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map
  (docs/module3/routing-and-tool-grant-map.md)
- Near-miss patterns observed in calibration
  (docs/module3/calibration-log.md)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit
and justified.
Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant,
a concrete justification, and confirmation that the grant does
not conflict with any near-miss pattern in the calibration log.

## Scope and evidence

- **Roles in scope:** the six MarketRadar roles below. They replace the earlier Module 4 sample-role sections, which pointed to `.agents/<role>.md` files that do not exist (`.agents/` contains only `.gitkeep`). Git history keeps the earlier sections.
- **Runtime role names:** Module 4 servers authorize on the `AGENT_ROLE` environment variable set by `scripts/run-agent.sh` (line 73; read at `mcp-servers/storage/server.py` line 27 and `mcp-servers/retrieval/server.py` line 27). They do not use the `calling_role` an agent declares for itself.

  | Role (this policy) | Agent definition | Module 4 runtime role (`AGENT_ROLE`) | Self-declared `calling_role` |
  |---|---|---|---|
  | planner | `.claude/agents/planner.md` | `planner` (`run-agent.sh` lines 23–27); retrieval allow-list only, no storage grants | `planner` |
  | implementer | `.claude/agents/implementer.md` | `implementer` | `implementer` |
  | tester | `.claude/agents/tester.md` | `tester` | `tester` |
  | marketradar-code-reviewer | `.claude/agents/marketradar-code-reviewer.md` | `reviewer` | `code-reviewer` |
  | project-manager | `.claude/agents/project-manager.md` | `project-manager` | `project_manager` |
  | orchestrator | `CLAUDE.md` "Orchestrator Workflow" (no agent file) | `orchestrator` | n/a |

- **MCP servers in scope:**
  - `mcp-servers/storage`, with operations `write_entry`, `read_entry`, `list_entries`, `update_entry`, `delete_entry` and `audit_read`. All six are implemented in `server.py` (lines 71–124).
  - `mcp-servers/retrieval`, with operation `retrieve` (`server.py` lines 76–99).
  - `mcp/` is Module 3 reference material only and is not wired in (`docs/module3/migration-notes.md` §1, line 18).
  - The image-level `slack` and `gmail` MCP servers are denied to every MarketRadar role.
- **Evidence:**
  - `docs/module3/calibration-log.md` records no near-miss patterns (`docs/module3/governance-risk-notes.md`, "Near-miss section status", lines 6–10). The preamble's pull-request check is therefore applied against findings B1–B5 in those risk notes.
  - No near-miss is claimed for MarketRadar.
  - The near-miss patterns in `docs/calibration-log.md` are Module 4 template material, not MarketRadar evidence, and are not cited here.
- **Status:** these entries state policy intent. The storage and retrieval allow-lists match the MCP tables below and are enforced in server code (`_authorize`, `mcp-servers/storage/server.py` lines 61–68; `_retrieval_ceiling`, `mcp-servers/retrieval/server.py` lines 51–60), but no agent session can reach those servers yet (D2). The `run-tests` skill activation scope is enforced by a PreToolUse hook (`scripts/enforce_skill_scope.py`, registered in `.claude/settings.json`); its decisions are tested deterministically in `eval/test_policy.py` but have not been observed in a live Claude Code session (D16). Other skill grants and tool grants are not yet enforced; see Deferred enforcement work. Container permissions are enforced only for containers started with `scripts/run-agent.sh`, as checked by `scripts/verify-container-permissions.sh`. Subagents started through the Claude Code Agent tool, which is the normal orchestration workflow, do not use the launcher: they run inside the Orchestrator's container and inherit its read-write workspace, environment and MCP configuration, so they have no container-level isolation (D15). Today:
  - the `mcp__storage__*` and `mcp__retrieval__*` tools named in `.claude/agents/*.md` are not connected to any configured MCP server. Only `slack` and `gmail` are configured, in the `/workspace` project entry of `/root/.claude.json`.
  - only the Tester holds the Skill tool (`.claude/agents/tester.md` line 4), for `run-tests` only.
  - `run-tests` is defined in `.claude/skills/run-tests/SKILL.md`; `draft-pr-description` has no skill definition. `skills/` defines only `check-gmail`, `rebuild-and-deploy`, `send-email`, `send-slack-message` and `summarize-session`.
- **Basis legend:**
  - **[B#]:** finding B1–B5 in `docs/module3/governance-risk-notes.md`.
  - **[LP]:** least-privilege default (preamble). The role has no task that needs the access.
  - **[Def]:** the role's agent definition or `CLAUDE.md`.
- **Changelog:** v1.1.0 (2026-11-04): per-role entries replaced with the MarketRadar roles; preamble unchanged from v1.0.0.
  - v1.1.1 (2026-11-04): documentation reconciliation notes resolved; role entries and preamble unchanged.
  - v1.1.2 (2026-11-05): Enforcement Layer 1 (container permissions): `run-agent.sh` line citations updated, `planner` launchable, D1 launcher part resolved; grants, allow-lists and role entries otherwise unchanged.
  - v1.1.3 (2026-11-05): `run-agent.sh` stores `/logs` in the named volume `agent-logs` instead of the repository; container permissions documented as launcher-only (D15); grants, allow-lists and role entries otherwise unchanged.
  - v1.2.0 (2026-11-05): Enforcement Layer 2 (MCP server allow-lists): storage and retrieval allow-lists aligned with the role tables (`planner` granted retrieval at `internal`; orchestrator retrieval denied); retrieval denials name the role and operation; successful retrievals are audited; the storage store defaults next to the audit log; D1 resolved, D3, D9 and D11 updated; grants and role entries otherwise unchanged.
  - v1.3.0 (2026-11-09): Enforcement Layer 3 for `run-tests`: skill defined with an Activation Scope, Tester given the Skill tool for `run-tests` only, PreToolUse hook denies every other caller and audits outside the repository; D6 updated, D16 added; no grant changes other than giving the Tester the Skill tool, which puts its existing run-tests grant into effect.
  - v1.3.1 (2026-11-10): D11 resolved: `eval/test_policy.py` parses the per-role tables and compares them with the enforcement artifacts; grants unchanged.

### Documentation reconciliation notes

1. **Autonomy ratings: resolved (Module 4.1).** The Module 3 routing map's ratings (`docs/module3/routing-and-tool-grant-map.md` lines 5–8) are kept as a historical record. The map's "Current policy clarification (Module 4.1)" section restates the ratings for all six roles as this policy sets them: Planner low, Implementer medium, Tester low, Reviewer low, Project Manager low, Orchestrator medium. It also states that this policy governs.
2. **Standard sequence: resolved in the routing map (Module 4.1).** The map's "Current policy clarification (Module 4.1)" section adds Reviewer and Project Manager rows and a conditional extended sequence: Implementer → Reviewer (when review is required) → Tester → Project Manager (when outcome recording is required). That order is the frozen HO-02 path, which has not been run end to end (`docs/module3/calibration-log.md` line 360). `CLAUDE.md` "Standard Sequence" (lines 206–216) is unchanged and does not yet route either role; that remains an open item for a separate, behaviour-changing decision.

## Role: planner

**Version:** v1.1.0  
**Defined in:** `.claude/agents/planner.md`  
**Module 4 runtime role:** `planner` (`scripts/run-agent.sh` lines 23–27). Named in `mcp-servers/retrieval/allow-list.json` (lines 23–26); no storage grants.

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | NO | The plan is returned to the Orchestrator (`planner.md` line 51); nothing needs to be recorded. | [LP] |
| read_entry | storage | NO | Prior lessons arrive through retrieval, not stored entries. | [LP] |
| list_entries | storage | NO | No planning step enumerates stored entries. | [LP] |
| update_entry | storage | NO | The Planner must not change project state (`planner.md` line 22). | [LP] [Def] |
| delete_entry | storage | NO | The Planner must not delete anything (`planner.md` line 22). | [LP] [Def] |
| audit_read | storage | NO | Audit inspection is owned by the Orchestrator, the only role granted audit access. | [LP] |
| retrieve | retrieval | YES | The definition requires lesson retrieval from `proj-lessons` at `internal` (`planner.md` lines 15–18). Not effective today: plan mode denied all 5 HO-01 calls (`calibration-log.md` lines 287 and 302). | [Def] [B5] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | NO | The definition says "Do not run tests" (`planner.md` line 24). [Def] |
| draft-pr-description | NO | The plan is the Planner's only output. [LP] |
| summarize-session | NO | The plan is the Planner's only output; there is no session summary to produce. [LP] |
| check-gmail | NO | No MarketRadar use, and it brings external personal data into context. [LP] |
| send-email | NO | No MarketRadar use; external publication. [LP] |
| send-slack-message | NO | No MarketRadar use; external publication. [LP] |
| rebuild-and-deploy | NO | No MarketRadar use; pushes an image to DockerHub. [LP] |

The Planner subagent does not hold the Skill tool (`planner.md` line 4).

### Data classification ceiling

**Maximum level:** internal  
**Reason:** The definition passes `classification_ceiling: internal` (`planner.md` line 17). The lessons planning needs are classified `internal`. Among the `.memory/reference/lesson-*.md` files, only `lesson-session-data-security.md` is `confidential`; `.memory/reference/lessons-ground-truth.md` carries no `classification:` field.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** The plan has no effect until a human approves it (`CLAUDE.md` "Human Checkpoints", line 236; `planner.md` line 53).  
**Reason:** The Planner only proposes. All effect is gated by human approval.  
**Container permissions:** workspace read-only, memory omitted (`scripts/run-agent.sh` lines 23–27). Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| Read, Grep, Glob | YES | Repository inspection is needed to plan (`planner.md` lines 4 and 19). [Def] |
| Edit, Write | NO | "Do not modify, create, or delete files" (`planner.md` line 22); Module 3 map line 5. [LP] [Def] |
| Bash | NO | Planning does not execute commands (Module 3 map line 5). [LP] [Def] |
| Direct Read of `.memory/reference/` files above `internal` | NO | Bypasses the retrieval ceiling. The log does not consistently attribute the HO-06 read: line 321 says "The Planner", line 352 says "an agent". In HO-01 the Planner refused this fallback (`calibration-log.md` line 289). | [B4] |

## Role: implementer

**Version:** v1.1.0  
**Defined in:** `.claude/agents/implementer.md`  
**Module 4 runtime role:** `implementer`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | YES | Stores one `internal` lesson in `proj-lessons` after each real code change (`implementer.md` lines 25–29). | [Def] |
| read_entry | storage | NO | Not in the definition's tool list (`implementer.md` line 4); lessons arrive through retrieval. | [LP] |
| list_entries | storage | NO | Not in the definition's tool list; no implementation step enumerates entries. | [LP] |
| update_entry | storage | NO | The Implementer writes new lessons only; it never revises stored entries. | [LP] |
| delete_entry | storage | NO | Must not delete project state without authorization. No MarketRadar step needs deletion. | [LP] |
| audit_read | storage | NO | Audit inspection is owned by the Orchestrator. | [LP] |
| retrieve | retrieval | YES | The definition requires lesson retrieval at `internal` before implementing (`implementer.md` lines 15–18). | [Def] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | NO | "Do not evaluate your own work with the test runner" (`implementer.md` line 23). The Module 3 map denies test execution (line 6). [Def] |
| draft-pr-description | NO | No workflow step asks the Implementer to draft PRs. [LP] |
| summarize-session | NO | The output template (`implementer.md` lines 39–50) already covers this. [LP] |
| check-gmail | NO | No MarketRadar use; brings external personal data into context. [LP] |
| send-email | NO | No MarketRadar use; external publication. [LP] |
| send-slack-message | NO | No MarketRadar use; external publication. [LP] |
| rebuild-and-deploy | NO | No MarketRadar use; pushes an image to DockerHub. [LP] |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** The definition passes `classification_ceiling: internal` (`implementer.md` line 17) and stores lessons as `internal` (line 28). No implementation task needs confidential material.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:**
- A human approves the plan before work starts (`CLAUDE.md` line 208).
- If files outside the approved list are needed, the Implementer returns to the Orchestrator (`implementer.md` line 24).
- Explicit human authorization is required before deleting any file or any project state.

**Reason:** `permissionMode: acceptEdits` (`implementer.md` line 6) applies edits automatically. Those edits are limited to the approved scope and can be reverted with git.  
**Container permissions:** workspace read-write except `.memory/knowledge` and `.memory/reference` (read-only, lines 58–61), memory mounted (`scripts/run-agent.sh` lines 18–22). Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| Read, Grep, Glob, Edit, Write | YES, within the approved file list | Needed to implement the approved plan (`implementer.md` lines 4 and 19–22). [Def] |
| Bash | NO | Not in the definition. Test execution belongs to the Tester. [LP] [Def] |
| Direct Read of `.memory/reference/` files above `internal` | NO | Bypasses the retrieval ceiling. [B4] |

## Role: tester

**Version:** v1.1.0  
**Defined in:** `.claude/agents/tester.md`  
**Module 4 runtime role:** `tester`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | NO | The Tester reports PASS/FAIL to the Orchestrator (`tester.md` lines 52–54) and must not change project state. | [LP] |
| read_entry | storage | NO | Its inputs arrive in the handoff (`tester.md` lines 26–32). | [LP] |
| list_entries | storage | NO | Its inputs arrive in the handoff. | [LP] |
| update_entry | storage | NO | The Tester must not change project state. | [LP] |
| delete_entry | storage | NO | The Tester must not change project state. | [LP] |
| audit_read | storage | NO | Audit inspection is owned by the Orchestrator. | [LP] |
| retrieve | retrieval | YES | The definition requires lesson retrieval at `internal` (`tester.md` lines 15–18). Denied by permission mode (`plan` or `dontAsk`) in every post-calibration holdout (`calibration-log.md` lines 336–353). | [Def] [B5] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | YES (intent) | Running tests is the Tester's core duty (`tester.md` line 20). Defined in `.claude/skills/run-tests/SKILL.md`; the Tester holds the Skill tool and the hook allows it `run-tests` and no other skill. Runtime behaviour is tested deterministically only (D16). The Tester's Bash can still run tests without the skill (D5). [Def] |
| draft-pr-description | NO | No workflow step asks the Tester to draft PRs. [LP] |
| summarize-session | NO | The verification report is the Tester's output (`tester.md` lines 34–48). [LP] |
| check-gmail | NO | No MarketRadar use; brings external personal data into context. [LP] |
| send-email | NO | No MarketRadar use; external publication. [LP] |
| send-slack-message | NO | No MarketRadar use; external publication. [LP] |
| rebuild-and-deploy | NO | No MarketRadar use; pushes an image to DockerHub. [LP] |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** The definition passes `classification_ceiling: internal` (`tester.md` line 17). Verification needs no confidential material.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Escalate before any command other than the project's test, lint or type-check commands, and before any write to tracked files or stored state.  
**Reason:** Verification must stay independent of the work it checks. Unscoped Bash is the main exposure [B1].  
**Container permissions:** workspace read-only, memory omitted (`scripts/run-agent.sh` lines 23–27). Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| Read, Grep, Glob | YES | Needed to inspect changed files (`tester.md` line 19). [Def] |
| Skill: `run-tests` only | YES | Needed to activate `run-tests`, which this policy grants under Skill activation scope. The hook `scripts/enforce_skill_scope.py` denies the Tester every other skill. [Def] |
| Edit, Write | NO | "Do not modify, create, or delete source files" and "Do not fix failures yourself" (`tester.md` lines 22–23). [Def] |
| Bash: validation commands only (`npm run test`, `npm run lint` and the type check, in `tracker-api/` and `tracker-client/`) | YES | Running tests needs process execution (`docs/module3/module-3-reflection.md` line 65). [Def] |
| Bash: everything else, including redirection, `rm`, `sed -i`, git writes and package installs | NO | Unscoped shell access can change the workspace under verification. `no_source_writes` cannot see Bash writes (`calibration-log.md` lines 52–56; reflection lines 69–76 and 95). This scoping is not enforced today (D5). [B1] [B2] |
| Direct Read of `.memory/reference/` files above `internal` | NO | Bypasses the retrieval ceiling. [B4] |

## Role: marketradar-code-reviewer

**Version:** v1.1.0  
**Defined in:** `.claude/agents/marketradar-code-reviewer.md`  
**Module 4 runtime role:** `reviewer` (self-declares `calling_role: code-reviewer`, `marketradar-code-reviewer.md` line 15)

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | NO | The Reviewer is read-only (`marketradar-code-reviewer.md` lines 18–19). HO-06 confirmed it made no storage writes (`calibration-log.md` line 320). | [LP] [Def] |
| read_entry | storage | NO | Code review reads code, not stored entries. | [LP] |
| list_entries | storage | NO | Code review reads code, not stored entries. | [LP] |
| update_entry | storage | NO | The Reviewer is read-only. | [LP] [Def] |
| delete_entry | storage | NO | The Reviewer is read-only. | [LP] [Def] |
| audit_read | storage | NO | Audit inspection is owned by the Orchestrator. | [LP] |
| retrieve | retrieval | YES | The definition requires lesson retrieval at `internal` (`marketradar-code-reviewer.md` lines 12–15). Denied by permission mode in HO-05 and HO-06 (reflection line 88). | [Def] [B5] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | NO | Read-only role; testing belongs to the Tester. The definition forbids commands that change repository or application state (`marketradar-code-reviewer.md` line 19). [Def] [LP] Enforced: the reviewer definition has no Skill tool, and the hook denies `run-tests` to any caller other than the Tester. Neither stops the reviewer's Bash (D4). |
| draft-pr-description | NO | Review findings are the Reviewer's only output. [LP] |
| summarize-session | NO | The review ends with its own overall assessment (`marketradar-code-reviewer.md` line 27). [LP] |
| check-gmail | NO | No MarketRadar use; brings external personal data into context. [LP] |
| send-email | NO | No MarketRadar use; external publication. [LP] |
| send-slack-message | NO | No MarketRadar use; external publication. [LP] |
| rebuild-and-deploy | NO | No MarketRadar use; pushes an image to DockerHub. [LP] |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** The definition passes `classification_ceiling: internal` (`marketradar-code-reviewer.md` line 14). Reviewing internal work needs no confidential material.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Review output is advisory only. Any action beyond producing findings escalates to the Orchestrator.  
**Reason:** A review role that can change state can quietly alter the work it is supposed to inspect independently.  
**Container permissions:** workspace read-only, memory omitted (`scripts/run-agent.sh` lines 28–33; launch name `marketradar-code-reviewer` or alias `reviewer`). Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| Read, Grep, Glob | YES | These cover everything a read-only review needs (reflection line 79). [Def] |
| Bash | NO | Not needed. In HO-06 it was used only for `ls`, `grep` and `wc` (`calibration-log.md` lines 57, 319 and 364). The frontmatter still grants it (`marketradar-code-reviewer.md` line 4; D4). [B3] |
| Edit, Write | NO | "Do not modify, create, or delete any project files" (`marketradar-code-reviewer.md` line 18). [Def] |
| Direct Read of `.memory/reference/` files above `internal` | NO | Bypasses the retrieval ceiling. [B4] |

## Role: project-manager

**Version:** v1.1.0  
**Defined in:** `.claude/agents/project-manager.md`  
**Module 4 runtime role:** `project-manager` (self-declares `calling_role: project_manager`, `project-manager.md` line 22)

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | YES | Its sole job is to record an `internal` `task_outcome` (`project-manager.md` lines 18–24). | [Def] |
| read_entry | storage | NO | Evidence arrives from the Orchestrator (`project-manager.md` lines 14 and 31–37). | [LP] |
| list_entries | storage | NO | Evidence arrives from the Orchestrator. | [LP] |
| update_entry | storage | NO | It records new outcomes only. | [LP] |
| delete_entry | storage | NO | No outcome-recording step needs deletion. | [LP] |
| audit_read | storage | NO | Audit inspection is owned by the Orchestrator. | [LP] |
| retrieve | retrieval | NO | "Do not retrieve reference documents" (`project-manager.md` line 27). This matches the allow-list denial (`mcp-servers/retrieval/allow-list.json` lines 19–22). | [Def] [LP] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | NO | "Do not run tests or shell commands" (`project-manager.md` line 26). [Def] |
| draft-pr-description | NO | The MarketRadar Project Manager records outcomes; it does not draft PRs. It has no Skill tool (`project-manager.md` line 4). [LP] |
| summarize-session | NO | The outcome report is its output (`project-manager.md` lines 39–53). [LP] |
| check-gmail | NO | No MarketRadar use; brings external personal data into context. [LP] |
| send-email | NO | External publication is not its role. [LP] |
| send-slack-message | NO | External publication is not its role. [LP] |
| rebuild-and-deploy | NO | No MarketRadar use; pushes an image to DockerHub. [LP] |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** It receives internal task evidence and writes `classification: internal` (`project-manager.md` line 21).

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** It must not mark a task complete when review or testing failed. If evidence is missing or contradictory, it reports a blocker instead (`project-manager.md` lines 17 and 28).  
**Reason:** It runs in `permissionMode: dontAsk` (`project-manager.md` line 6), so calls outside its tool list are refused rather than prompted. Its single permitted action is a new internal record.  
**Container permissions:** workspace read-only, memory omitted (`scripts/run-agent.sh` lines 23–27). See D9. Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| `mcp__storage__write_entry` | YES | Its only tool (`project-manager.md` line 4). [Def] |
| Read, Grep, Glob | NO | Evidence arrives in the handoff. [LP] |
| Edit, Write | NO | "Do not modify application code" (`project-manager.md` line 25). [Def] |
| Bash | NO | "Do not run tests or shell commands" (`project-manager.md` line 26). [Def] |

## Role: orchestrator

**Version:** v1.1.0  
**Defined in:** `CLAUDE.md` "Orchestrator Workflow" (lines 200–242) and `docs/module3/routing-and-tool-grant-map.md`. There is no agent definition file.  
**Module 4 runtime role:** `orchestrator`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason | Basis |
|---|---|---|---|---|
| write_entry | storage | NO | The Orchestrator coordinates rather than performing specialized work (`CLAUDE.md` line 232). Outcomes are recorded by the Project Manager and lessons by the Implementer. | [LP] [Def] |
| read_entry | storage | YES | Needed to verify the Project Manager's recorded outcome when evaluating completion (`CLAUDE.md` line 232: "evaluates"). | [Def] |
| list_entries | storage | YES | Needed to locate recorded outcomes when evaluating completion. | [Def] |
| update_entry | storage | NO | No orchestration step revises stored entries. | [LP] |
| delete_entry | storage | NO | No blanket permissions, and no MarketRadar step deletes state. Deletion is a human action outside the agent workflow. | [LP] |
| audit_read | storage | YES | Evaluating and escalating need visibility of authorization denials (`CLAUDE.md` line 232: "evaluates … and escalates"). Read-only. | [Def] |
| retrieve | retrieval | NO | `CLAUDE.md` gives the Orchestrator no retrieval step; it loads memory through the startup reads (lines 188–196). Lessons are retrieved by the roles that use them. | [LP] |

### Skill activation scope

| Skill | Activation permitted | Reason / Basis |
|---|---|---|
| run-tests | NO | Verification belongs to the Tester. The evaluation gate requires a Tester PASS (`CLAUDE.md` lines 240–242). [Def] Enforced by the hook, which denies `run-tests` in the main session (no `agent_type`). |
| draft-pr-description | NO | No workflow step drafts PRs, and the skill is undefined. [LP] |
| summarize-session | YES | A read-only, human-facing summary (`skills/summarize-session/SKILL.md`) used for completion and escalation reports (`CLAUDE.md` lines 213 and 216). [Def] |
| check-gmail | NO | Brings external personal data into context; not part of the MarketRadar workflow. [LP] |
| send-email | NO | External publication outside the MarketRadar workflow. [LP] |
| send-slack-message | NO | External publication outside the MarketRadar workflow. [LP] |
| rebuild-and-deploy | NO | Pushes an image to DockerHub; outside the MarketRadar workflow. [LP] |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** The startup reads cover project memory and knowledge files. No orchestration step needs the confidential lesson [LP]. B4 shows how confidential material can enter context through a direct Read.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:**
- Human approval after the Planner phase and before implementation (`CLAUDE.md` line 236).
- Escalation after repeated FAIL (`CLAUDE.md` line 216).
- Human approval before any storage deletion, any external publication, any skill activation outside these grants, and any change to permissions, `CLAUDE.md` or configuration.

**Reason:** Routing is autonomous, but every effectful action is gated by a human.  
**Container permissions:** workspace read-write except `.memory/knowledge` and `.memory/reference` (read-only, lines 58–61), memory mounted (`scripts/run-agent.sh` lines 18–22). Applies only when launched with `scripts/run-agent.sh`; not to Agent-tool subagents (D15).

### Agent tool grants

| Tool | Granted | Reason / Basis |
|---|---|---|
| Read, Grep, Glob | YES | Needed for startup memory reads and evaluation (`CLAUDE.md` lines 188–196). [Def] |
| Agent (subagent delegation) | YES | Needed to route work to specialists (`CLAUDE.md` lines 202 and 206–216). [Def] |
| Edit, Write on application code | NO | The Orchestrator does not perform specialized work (`CLAUDE.md` lines 232 and 242). Not enforced; see D14. [Def] |
| Bash | NO | Not granted; implicit deny under the least-privilege default. Not enforced; see D14. [LP] |
| Direct Read of `.memory/reference/` files above `internal` | NO | Bypasses the retrieval ceiling. [B4] |
| `slack` and `gmail` MCP operations | NO | Configured for the `/workspace` session but unused by MarketRadar (D10). [LP] |

## Deterministic conversion history

- `validator`: converted from agent to deterministic code. See `docs/adr/ADR-001-json-schema-validation-deterministic-conversion.md`. No MCP access required.

## Deferred enforcement work

This section records gaps between this policy and the current configuration. No change has been made for any item below unless the item says it is partly resolved. Until an item is resolved, this policy states the intended grant, and the configuration may be broader.

| ID | Gap | Proposed action | Basis |
|---|---|---|---|
| D1 | Resolved (Module 4.1). Layer 1: `scripts/run-agent.sh` launches `planner` with workspace read-only and memory omitted (lines 23–27). Layer 2: `planner` is in `mcp-servers/retrieval/allow-list.json` with ceiling `internal` (lines 23–26). | None. | `docs/module3/migration-notes.md` line 91 |
| D2 | The MCP tools in `.claude/agents/*.md` resolve to no configured server. The agent bodies use Module 3 argument shapes (`project_id`, `calling_role`, …), but Module 4 uses `write_entry(key, value)` (`storage/server.py` line 72) and `retrieve(query, top_k)` (`retrieval/server.py` line 77). | Register the Module 4 servers and update the agent bodies. | [Def] |
| D3 | Allow-list part resolved (Module 4.1, Layer 2): `mcp-servers/storage/allow-list.json` and `mcp-servers/retrieval/allow-list.json` match the MCP tables in this policy, and `eval/test_policy.py` checks them against both a hard-coded matrix and the parsed policy tables (D11). Remaining: the self-declared `calling_role` names in the agent definitions (`code-reviewer`, `project_manager`) still differ from the runtime names (`reviewer`, `project-manager`). The Module 4 servers authorize on `AGENT_ROLE` and ignore them. | Align the self-declared names with the runtime names when the agent bodies are updated (D2); agent definitions were out of scope for Layer 2. | [LP] |
| D4 | `marketradar-code-reviewer` frontmatter still grants Bash (line 4). | Remove Bash. | [B3] |
| D5 | Tester Bash is unscoped. | Scope it to the validation commands with command-scoped permission rules. | [B1] |
| D6 | `no_source_writes` cannot detect writes made through Bash. A scoped `run-tests` skill now exists (Layer 3), but skill scope does not cover Bash. | Detect Bash writes in the evaluator, for example with a working-tree diff. A scoped `run-tests` skill exists (Layer 3); detecting Bash writes remains open. | [B2] [B1] |
| D7 | Retrieval is denied by permission mode for the Planner, Tester and Reviewer. | Explicitly allow `mcp__retrieval__retrieve` for those roles under their permission modes. | [B5] |
| D8 | Direct Read of `.memory/reference/` can bypass the classification ceiling. | Deny direct Read of `.memory/reference/` files above the role's ceiling. | [B4] |
| D9 | Fixed in the server (Module 4.1, Layer 2): when `STORAGE_STORE` is unset, the store defaults to the audit log's directory (`storage/server.py` line 32). Under `run-agent.sh` (`STORAGE_AUDIT_LOG=/logs/storage-audit-log.jsonl`, line 64) that is `/logs/storage-store.json` on the `agent-logs` volume, which stays writable when the workspace is read-only. Not yet exercised in a container, because the servers are not registered (D2). | Verify a `project-manager` `write_entry` in a launched container once D2 is resolved. | Configuration |
| D10 | `slack` and `gmail` are configured for `/workspace` (`/root/.claude.json`) and inherited by the Orchestrator session. | Remove them, deny them, or scope them with permission rules for MarketRadar sessions. | [LP] |
| D11 | Resolved (Module 4.1): `eval/test_policy.py` parses each role's MCP server and operation access table, data classification ceiling, `run-tests` row of the Skill activation scope table, and Container permissions line, and compares them with `mcp-servers/storage/allow-list.json`, `mcp-servers/retrieval/allow-list.json`, the `run-tests` Activation Scope in `.claude/skills/run-tests/SKILL.md`, the agent definitions that hold the Skill tool, the skill-scope hook's decisions and `scripts/run-agent.sh`. A mismatch is reported as overgrants and missing grants. The hard-coded matrices in the same file are checked against the parsed tables. Not covered: the Agent tool grant tables and autonomy levels, which are not parsed, and the activation scope of skills other than `run-tests`, whose cells are parsed but have no enforcement artifact. No pre-commit hook is installed. | Install the pre-commit hook described under Policy maintenance, or remove that claim. | Repository state |
| D12 | `docs/routing-and-tool-grant-map.md` (lines 5–9) and `eval/red-team-*.md` describe the sample-role grants. | Update them after this policy is approved. | Repository state |
| D13 | Implementer Edit/Write scoping is not enforced. The `tools:` line in `.claude/agents/implementer.md` (line 4) grants unrestricted Edit/Write. The approved-file-list limit comes only from the prompt instructions (`implementer.md` lines 20 and 24). | Enforce the scope with path-scoped permission rules or a review gate. | [LP] |
| D14 | The Parent Orchestrator session holds Bash, Edit and Write because it runs as the main Claude Code session. This policy grants none of them, so they are denied by the least-privilege default, but nothing restricts them at runtime. | Restrict them with session permission rules, or document narrow read-only Bash exceptions through a PR. | [LP], `CLAUDE.md` role boundaries |
| D15 | Subagents started through the Claude Code Agent tool (the normal orchestration workflow) do not use `scripts/run-agent.sh`. They run inside the Orchestrator's container and inherit its read-write workspace, environment and MCP configuration, so the container permissions in the role entries do not isolate them. The Orchestrator cannot start role containers itself without access to the Docker socket, which is denied. | Until a launch path that does not expose the Docker socket exists, in-process subagents are limited only by their `tools:` lists and permission rules (D4, D5, D13, D14). A role gets container-level isolation only when a human starts it with `scripts/run-agent.sh`. | Configuration |
| D16 | Layer 3 runtime behaviour is unverified. The hook's decisions are tested deterministically (`eval/test_policy.py`) using the Skill tool's `skill` parameter and the documented `agent_type` field, but no hook input has been captured from a live Claude Code session. A human typing `/run-tests` bypasses PreToolUse. If `python3` is unavailable the hook errors and Claude Code may let the call proceed. Roles with a read-write workspace can edit the hook or `.claude/settings.json` (D13, D14). | Capture one live hook input for a Tester and a non-Tester Skill call and confirm `agent_type` and `tool_input.skill`. | Configuration |

## Policy maintenance

**Drift detection.** The policy test suite (`eval/test_policy.py`) runs automatically:

- locally, on every commit that changes a governed file, through the pre-commit hook, and
- on the shared repository, on every push and pull request, through CI.

**Current status.** `eval/test_policy.py` parses each role's MCP server and operation access, data classification ceiling, `run-tests` skill activation scope and container permission entries from this policy and compares them with the enforcement artifacts (the storage and retrieval allow-lists, the `run-tests` skill, the agent definitions that hold the Skill tool, the skill-scope hook and `scripts/run-agent.sh`), reporting overgrants and missing grants. It also checks its hard-coded matrices against the parsed tables. The Agent tool grant tables and autonomy levels are not checked. No pre-commit hook is installed in this repository (no `.pre-commit-config.yaml` or `.git/hooks/pre-commit`); see Deferred enforcement work.

**Cadence.** Governed changes are checked as they happen. A scheduled full run should be added quarterly if the deployed environment can drift outside of commits.

**Ownership.** The author of a change that touches a governed artifact resolves any drift before merge. The policy owner reviews and approves changes to this policy.

**Escalation in production.** If drift is detected in a deployed environment, treat it as an incident: revert or hotfix the offending change, notify the policy owner or on-call engineer, and record the event in the audit trail or incident log. No governed change ships while the suite is failing.
