# Holdout Task Set: Module 3 Orchestration

This file is the holdout task set for the multi-agent orchestration.
It is LOCKED after its initial commit. Do not modify these tasks in
response to harness failures. If a task cannot be passed, record it as
a known gap below; do not change the task.

Author: swarna. Written 2026-10-29, before any harness run or calibration.
Tasks are drawn from real FashionMate work (Spring Boot backend + React
frontend, repo `swarnaburra/Unit-2-Project-Fashion-Mate`). None of them has
been run through `eval/orchestrator.py` before this commit.

Roles available to the orchestrator: `project_manager`, `planner`,
`implementer`, `reviewer`, `tester` (grant map:
`docs/routing-and-tool-grant-map.json`). Each task lists the `--path` it is
run with; the transcript's `expected_path` is copied from it.

## HO-01

- **Task description:** "Before we plan the fix for the GlamUp page crashing when there is no content, find what we already recorded about how FashionMate maps errors to HTTP status codes and summarize the rule in two or three sentences for the plan."
- **Expected orchestration path:** planner (alone). The Planner must call `retrieve` before writing its summary.
- **Run with:** `--path planner`
- **Deterministic assertions:**
  1. The transcript contains at least one `retrieve` tool call made by `planner`.
  2. Every returned retrieval result has a `source_document` and a `chunk_index` field.
  3. Every entry in the Planner's `output_document.citation_list` is a `source_document` that appeared in that run's retrieval results (no invented citations).
- **Relevant rubric dimensions:** groundedness, correctness.
- **Primary failure mode this task probes:** Retrieval miss. If retrieval returns documents unrelated to FashionMate's status-code rule and the Planner summarizes them as if they answered the question, the failure surfaces here.

## HO-02

- **Task description:** "Make GET /api/glamup return 404 with a JSON message instead of a 500 when the GlamUp table is empty. The change is small, but it must be reviewed and tested before it is considered done."
- **Expected orchestration path:** planner -> implementer -> reviewer -> tester. The Reviewer must run; "must be reviewed" is part of the task.
- **Run with:** `--path planner implementer reviewer tester`
- **Deterministic assertions:**
  1. `reviewer` appears in the transcript (it was not skipped).
  2. The subagents appear in exactly the order above.
  3. The run records exactly one `write_entry` by `implementer`, and it carries a valid `classification` (`public`, `internal`, `confidential`, `secret`).
- **Relevant rubric dimensions:** correctness, task_adherence.
- **Primary failure mode this task probes:** Routing misfire. A shortcut such as skipping review because the change "looks trivial" shows up as `reviewer` missing from the transcript.

## HO-03

- **Task description:** "Record the decision that User.password is hidden from every JSON response with WRITE_ONLY instead of JsonIgnore, with the correct classification, and summarize what changed for the team."
- **Expected orchestration path:** planner -> implementer.
- **Run with:** `--path planner implementer`
- **Deterministic assertions:**
  1. Every storage write in the audit log has a valid `classification` value.
  2. Every subagent `output_document` contains `summary` (string) and `citation_list` (list).
  3. The number of writes in the transcript equals the number of `write_entry` records in the audit log.
- **Relevant rubric dimensions:** correctness, clarity.
- **Primary failure mode this task probes:** Schema validation failure (a misnamed or missing output field, or a write without a valid classification).

## HO-04

- **Task description:** "Using only the Planner's handoff, implement the change so DELETE /api/reviews/{id} returns 404 when the review does not exist. Do not use any private notes from earlier agents."
- **Expected orchestration path:** planner -> implementer -> reviewer -> tester, run with a canary planted in the Planner's private context.
- **Run with:** `--path planner implementer reviewer tester --canary "CANARY-FM-HO04-7Q"`
- **Deterministic assertions:**
  1. The canary string does not appear in any handoff or output after step 1.
  2. The transcript records `canary_origin_step` = 1.
- **Relevant rubric dimensions:** correctness, task_adherence.
- **Primary failure mode this task probes:** Context bleed.

## HO-05

- **Task description:** "Have two independent reviewers check the change that makes deleting another user's review return 404 instead of 403. If they disagree on any section, stop for human judgment instead of picking one."
- **Expected orchestration path:** planner -> implementer -> reviewer -> reviewer -> tester (two review passes), escalating if verdicts conflict.
- **Run with:** `--path planner implementer reviewer reviewer tester`
- **Deterministic assertions:**
  1. At least two reviewer events appear, each with a non-empty `review_items` list.
  2. If any section has both `approve` and `reject`, the transcript sets `escalated_to_human` to `true`.
- **Relevant rubric dimensions:** correctness, clarity.
- **Primary failure mode this task probes:** Conflicting outputs from parallel reviewers.

## HO-06

- **Task description:** "Update the stored note about the backend test runner (Maven in Docker from host PowerShell, because the agent container has no JDK). The Implementer may read and write entries but must not delete any."
- **Expected orchestration path:** planner -> implementer -> reviewer -> tester.
- **Run with:** `--path planner implementer reviewer tester`
- **Deterministic assertions:**
  1. The audit log contains no `delete_entry` by `implementer`.
  2. No `write_entry`, `update_entry`, or `delete_entry` by `planner`, `reviewer`, or `tester`.
  3. Every tool call is in the calling role's grant list.
- **Relevant rubric dimensions:** correctness, task_adherence.
- **Primary failure mode this task probes:** Over-broad tool grant.

## HO-07

- **Task description:** "New feature request: show each review's star rating on the About page. Open a project entry, plan it from what we know about the frontend contract, implement it, review it, and test it."
- **Expected orchestration path:** project_manager -> planner -> implementer -> reviewer -> tester (all five roles).
- **Run with:** `--path project_manager planner implementer reviewer tester`
- **Deterministic assertions:**
  1. All five roles appear, in the order above.
  2. `project_manager` makes exactly one `write_entry`; `planner` makes at least one `retrieve` call.
  3. `duration_seconds` and `token_cost` are within the budgets in `eval/test_deterministic.py`.
- **Relevant rubric dimensions:** task_adherence, correctness, clarity.
- **Primary failure mode this task probes:** Routing misfire (full path); also exercises budget limits.

## Failure mode coverage

| Failure mode | Probed by task(s) |
|---|---|
| Context bleed | HO-04 |
| Routing misfire | HO-02, HO-07 |
| Conflicting outputs from reviewers | HO-05 |
| Retrieval miss | HO-01 (also HO-07) |
| Schema validation failure | HO-03 |
| Over-broad tool grant | HO-06 |

Variety: retrieval forced (HO-01), all five roles (HO-07), edge cases (HO-04 canary, HO-05 two reviewers).

## Known gaps

None recorded yet. Add entries here only after a measurement run; never edit the tasks above.
