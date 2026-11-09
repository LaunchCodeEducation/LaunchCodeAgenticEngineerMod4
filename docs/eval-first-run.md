# Evaluation: First Run

Run: .eval-artifacts/runs/dev/RUN-20261105-003755.json
Path: planner -> implementer -> reviewer -> tester
Duration: 79.0s | Audit entries: 6
Budgets: MAX_DURATION_SECONDS=180, MAX_TOKEN_COST=40000 (defaults; no Module 1 baseline)

## Deterministic checks: 14/14 passed

[PASS] write_classifications (schema validation): All storage writes carried a valid classification.
[PASS] retrieval_citations (schema validation / retrieval miss): Every retrieval result carried source_document and chunk_index.
[PASS] output_schema (schema validation): all subagent output documents matched the result schema.
[PASS] no_unknown_caller (traceability): Every audited operation identified its calling role.
[PASS] audit_matches_writes (traceability): Audit log entries match the writes in the transcript.
[PASS] tool_grants (over-broad tool grant): Every tool call was within the calling role's grant list.
[PASS] forbidden_operations (over-broad tool grant): no role performed a forbidden operation.
[PASS] required_roles (routing misfire): All required subagents ran.
[PASS] role_order (routing misfire): Subagents ran in the expected order.
[PASS] context_bleed (context bleed): no canary planted; bleed check not exercised this run.
[PASS] reviewer_conflict (conflicting reviewers): fewer than two reviewers ran; no conflict possible.
[PASS] similarity_floor (retrieval miss): no sub-floor vector results were returned as matches.
[PASS] latency (latency): run took 79.0s, within budget.
[PASS] cost (cost): run used 0 tokens, within budget.

Notes:
- cost reports 0 tokens: token_cost is not being recorded, so this check passes vacuously.
- context_bleed and reviewer_conflict were not exercised (no canary, one reviewer).

## Rubric suite: 0/5 passed

[FAIL] correctness: 2/4 (needs 3). Citations claim grounding in incident-report-2024-q3.md, postmortem-lessons.md and api-design-guidelines.md, but those documents are about rate-limit notice periods while the decision is about permitting empty arrays in JSON validation. Reviewer and tester approved the mismatch.
[FAIL] task_adherence: 1/4 (needs 3). The task was a CSV-export feature per docs/prd.md; all four subagents worked on an unrelated "permit empty arrays" validation change instead.
[FAIL] groundedness: 1/4 (needs 3). Claims attributed to sources that never mention empty arrays. The reviewer noticed the retrieved chunks did not match the cited claims but approved anyway.
[FAIL] clarity: 2/4 (needs 3). The decision record is well structured, but every citation traces to unrelated rate-limit documents, and the reviewer's traceability observation was waved through.
[FAIL] aggregate: total 6 (needs 12).

## Observations for calibration

- Deterministic blind spot: no check verifies that citations support the claims or that retrieval matched the task. Candidate new check.
- The reviewer saw the source/content mismatch and approved anyway (likely a reviewer prompt issue).
- The judge flagged "suspicious identical tool outputs" from read_entry; inspect the transcript.