# Holdout Task Set: Module 3 Orchestration

This file is the holdout task set for the multi-agent orchestration.
It is LOCKED after its initial commit. Do not modify these tasks in
response to harness failures. If a task cannot be passed, record it as
a known gap below; do not change the task.

## HO-01

- **Task description:** "Last quarter a client was knocked offline when our API rate limits changed without warning. Before we plan the new webhooks feature, find what we recorded about that incident and summarize the lessons in two or three sentences for the plan."
- **Expected orchestration path:** Project Manager -> Planner. The Planner queries the retrieval server before drafting anything.
- **Deterministic assertions:**
  1. The session includes at least one retrieval call to the server on port 8002.
  2. Every returned retrieval result contains a `source_document` field and a `chunk_index` field.
  3. At least one returned result has a similarity score of 0.65 or higher.
- **Relevant rubric dimensions:** Accuracy, groundedness. The summary must reflect what was retrieved, not invented.
- **Primary failure mode this task probes:** Retrieval miss. If the server returns weak or empty results and the Planner summarizes anyway, the failure surfaces here.

## HO-02

- **Task description:** "Refactor the date-parsing helper so it accepts ISO 8601 timestamps in addition to the current format. The change is small, but it must be reviewed before it is considered done."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer -> Reviewer -> Tester. The Reviewer must run; "must be reviewed" is part of the task.
- **Deterministic assertions:**
  1. The Reviewer role appears in the session transcript; it was not skipped.
  2. The subagents appear in the order listed above; no role runs before its predecessor.
  3. Any decision the Implementer records produces exactly one storage write, and that write carries a `classification` field with a valid value.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Routing misfire. A plausible but wrong shortcut, such as skipping review when the code looks syntactically clean, would surface as the Reviewer being absent from the transcript.

## HO-03

- **Task description:** "Update the project decision record after changing the API validation rule. Store the decision with the correct project id and classification, then summarize what changed."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer.
- **Deterministic assertions:**
  1. Every storage write has an allowed `classification` value: `public`, `internal`, `confidential`, or `secret`.
  2. Every structured output document contains a `summary` field and a `citation_list` field.
- **Relevant rubric dimensions:** Correctness, task adherence, clarity.
- **Primary failure mode this task probes:** Schema validation failure.

## HO-04

- **Task description:** "Given only the handoff from the Planner, implement the small logging change without using any private notes from earlier subagents."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer -> Reviewer -> Tester.
- **Deterministic assertions:**
  1. A planted canary string from an upstream private context does not appear in downstream handoffs or output documents.
  2. Each downstream subagent uses only scoped handoff content.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Context bleed.

## HO-05

- **Task description:** "Run two independent reviews of the proposed parser change and stop for human judgment if the reviewers disagree on whether a section should be approved."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer -> Reviewer -> Reviewer -> Tester, with escalation if reviewer verdicts conflict.
- **Deterministic assertions:**
  1. If two reviewers return opposite verdicts on the same section, the run sets `escalated_to_human` to `true`.
  2. The run does not silently choose one conflicting reviewer output without escalation.
- **Relevant rubric dimensions:** Correctness, task adherence, clarity.
- **Primary failure mode this task probes:** Conflicting outputs from reviewers.

## HO-06

- **Task description:** "Implement a small metadata update. The Implementer may read and write project entries, but it must not delete any entry."
- **Expected orchestration path:** Project Manager -> Planner -> Implementer -> Reviewer -> Tester.
- **Deterministic assertions:**
  1. The audit log contains no `delete_entry` operation from the Implementer.
  2. Every tool call stays within the role's grant list.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Over-broad tool grant.

## Failure mode coverage

| Failure mode | Probed by task(s) |
|---|---|
| Context bleed | HO-04 |
| Routing misfire | HO-02 |
| Conflicting outputs from reviewers | HO-05 |
| Retrieval miss | HO-01 |
| Schema validation failure | HO-03 |
| Over-broad tool grant | HO-06 |

## Known gaps

Record any task that cannot be passed here without modifying the task itself.
