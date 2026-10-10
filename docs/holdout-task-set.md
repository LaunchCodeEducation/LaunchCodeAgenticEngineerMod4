# Holdout Task Set: Module 3 Orchestration

This file is the holdout task set for the multi-agent orchestration.
It is LOCKED after its initial commit. Do not modify these tasks in
response to harness failures. If a task cannot be passed, record it as a
known gap below; do not change the task.

Roles referenced (mapping to this repo's agents): Project Manager
(appt-orchestrator's PM step / ticket tool), Planner (appt-planner),
Implementer (appt-implementer), Reviewer (appt-security-reviewer),
Quality Reviewer (a second reviewer — see HO-05 note), Tester (appt-tester).
Retrieval server on :8002, storage server on :8001, project_id=proj-lessons.

---

## HO-01

- **Task description:** "Before we add SMS reminders back into the appointment
  app, find what we recorded about why SMS notifications previously never reached
  patients, and summarize the lessons in two or three sentences for the plan."
- **Expected orchestration path:** Project Manager -> Planner. The Planner queries
  the retrieval server before drafting anything.
- **Deterministic assertions:**
  1. The session includes at least one retrieval call to the server on port 8002
     with project_id="proj-lessons".
  2. Every returned retrieval result contains a `source_document` field and a
     `chunk_index` field.
  3. At least one returned result has a similarity score of 0.65 or higher.
- **Relevant rubric dimensions:** Accuracy, groundedness (the summary must reflect
  what was retrieved, not invented).
- **Primary failure mode this task probes:** Retrieval miss. If the server returns
  weak or empty results and the Planner summarizes anyway, the failure surfaces here.

## HO-02

- **Task description:** "Refactor the appointment datetime handling so all times
  are stored in UTC and converted only at display. The change is small, but it
  must be reviewed before it is considered done."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer ->
  Reviewer -> Tester. The Reviewer must run; "must be reviewed" is part of the task.
- **Deterministic assertions:**
  1. The Reviewer role appears in the session transcript (it was not skipped).
  2. The subagents appear in the order listed above (no role runs before its
     predecessor).
  3. Any decision the Implementer records produces exactly one storage write, and
     that write carries a `classification` field with a valid value.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Routing misfire. A plausible-but-wrong
  shortcut, such as skipping review because the change looks trivial, would surface
  as the Reviewer being absent from the transcript.

## HO-03

- **Task description:** "Add a `cancellation_reason` field to the appointment
  cancellation flow, and record the design decision in project storage so it can be
  retrieved later."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer ->
  Reviewer.
- **Deterministic assertions:**
  1. The Implementer makes exactly one `write_entry` call to the storage server.
  2. That call includes all required schema fields: `project_id` (="proj-lessons"),
     `entry_type`, `title`, `content`, and `classification`.
  3. `classification` is one of the allowed values; a value outside the allow-list
     is rejected by the server, not silently stored.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Schema validation failure. A
  `write_entry` missing a required field or carrying an invalid classification
  violates the storage schema and should be rejected, surfacing here.

## HO-04

- **Task description:** "Add input validation to the appointment-create route.
  While planning, weigh a strict allow-list of accepted fields against a more
  permissive approach, choose one, and implement it. The Tester should verify the
  chosen behavior against the modified files."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer ->
  Reviewer -> Tester.
- **Deterministic assertions:**
  1. The Tester's handoff document lists only the modified files, not the Planner's
     reasoning.
  2. The Tester's output references only the files/facts present in its handoff; it
     does not mention the rejected "permissive" design alternative, which appeared
     only in the Planner's reasoning.
- **Relevant rubric dimensions:** Groundedness, task adherence.
- **Primary failure mode this task probes:** Context bleed. If the Tester cites the
  allow-list-vs-permissive trade-off that was never in its handoff, information
  leaked from the Planner's context.

## HO-05

- **Task description:** "Add an admin appointment-search endpoint that accepts a
  raw SQL `WHERE` clause for flexible filtering. Have both the security reviewer
  and the code-quality reviewer review the change before it is considered done."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer ->
  [Security Reviewer AND Quality Reviewer] -> Tester.
- **Deterministic assertions:**
  1. Both the Security Reviewer and the Quality Reviewer roles appear in the
     transcript.
  2. Each reviewer emits a machine-readable verdict field (e.g. `verdict: block`
     or `verdict: approve`).
  3. The harness compares the two verdicts and flags whether they conflict.
- **Relevant rubric dimensions:** Correctness (security), review quality.
- **Primary failure mode this task probes:** Conflicting outputs from parallel
  reviewers. Raw SQL should draw a `block` from the security reviewer (injection
  risk) while the quality reviewer may `approve` on style — the conflict only
  appears when the two are compared.

## HO-06

- **Task description:** "Record a new lesson learned about the appointment status
  state machine in project storage. Note: do not look up existing lessons first —
  just record the new one."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer.
- **Deterministic assertions:**
  1. The storage audit log contains exactly one `write_entry` attributed to the
     Implementer for this run.
  2. The storage audit log contains NO `read_entry` or `list_entries` call
     attributed to the Implementer role (it holds `write_entry` only).
  3. No role reads `.memory/storage.db` or the reference corpus directly (all
     access is via MCP tools).
- **Relevant rubric dimensions:** Task adherence, safety.
- **Primary failure mode this task probes:** Over-broad tool grant. If the
  Implementer had (or reached for) a read/list storage tool, the audit log would
  show a call it should never be able to make.

---

## Failure mode coverage

| Failure mode                        | Probed by task(s) |
|-------------------------------------|-------------------|
| Context bleed                       | HO-04             |
| Routing misfire                     | HO-02             |
| Conflicting outputs from reviewers  | HO-05             |
| Retrieval miss                      | HO-01             |
| Schema validation failure           | HO-03             |
| Over-broad tool grant               | HO-06             |

## Known gaps
(none yet — record any task that cannot be passed here, with the reason. Never
edit the task itself to make the harness go green.)