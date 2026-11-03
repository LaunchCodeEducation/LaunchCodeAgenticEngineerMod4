# Holdout Task Set: Module 3.3 Orchestration

This file is the holdout task set for the multi-agent orchestration.
It is LOCKED after its initial commit. Do not modify these tasks in
response to harness failures. If a task cannot be passed, record it
as a known gap below; do not change the task.


## HO-01 — Retrieval Miss

- **Task description:** "Before proposing changes to how MarketRadar handles marketplace sources, find our previous lessons about source limitations and explain how they should affect the implementation plan."
- **Expected orchestration path:** Planner. The Planner retrieves relevant lessons before proposing an approach.
- **Deterministic assertions:**
  1. The Planner calls the retrieval MCP server with project `proj-lessons`.
  2. At least one returned result cites `lesson-marketplace-source-feasibility.md`.
  3. Every returned result includes a source document and chunk identifier.
- **Relevant rubric dimensions:** Error and Warning Coverage, Recommendation Quality.
- **Primary failure mode this task probes:** Retrieval miss.

## HO-02 — Routing Misfire

- **Task description:** "Add validation to reject an invalid saved-search price range where the minimum price exceeds the maximum. The change must be planned, implemented, reviewed, and tested before completion."
- **Expected orchestration path:** Planner -> Implementer -> Code Reviewer -> Tester -> Project Manager.
- **Deterministic assertions:**
  1. All five roles appear in the orchestration transcript.
  2. The roles execute in the expected order.
  3. The Tester runs the relevant automated tests.
  4. The Project Manager receives the final verification result.
- **Relevant rubric dimensions:** Lint Result Accuracy, Error and Warning Coverage, Recommendation Quality.
- **Primary failure mode this task probes:** Routing misfire.

## HO-03 — Schema Validation Failure

- **Task description:** "Investigate a saved-search execution failure and produce a structured diagnostic report containing the search ID, error category, evidence, and recommended next action."
- **Expected orchestration path:** Planner -> Tester.
- **Deterministic assertions:**
  1. The diagnostic report contains `search_id`, `error_category`, `evidence`, and `recommended_action`.
  2. None of the required fields are missing.
  3. The report can be parsed as valid JSON.
- **Relevant rubric dimensions:** Error and Warning Coverage, Recommendation Quality.
- **Primary failure mode this task probes:** Output format mismatch and schema validation failure.

## HO-04 — Context Bleed

- **Task description:** "Start a fresh investigation into a saved-search failure. Use only the current task and relevant MarketRadar documentation. Do not reuse assumptions or conclusions from previous unrelated investigations."
- **Expected orchestration path:** Planner -> Tester.
- **Deterministic assertions:**
  1. The run starts in a fresh agent conversation.
  2. The report references the current saved-search investigation.
  3. No unrelated project identifiers appear in the final report.
- **Relevant rubric dimensions:** Error and Warning Coverage, Recommendation Quality.
- **Primary failure mode this task probes:** Context bleed.

## HO-05 — Conflicting Reviewer Outputs

- **Task description:** "Have two independent reviewers inspect a proposed change to saved-search error handling. Compare their findings and identify any disagreements before approving the change."
- **Expected orchestration path:** Planner -> Code Reviewer A and Code Reviewer B -> Planner.
- **Deterministic assertions:**
  1. Two independent reviewer outputs are recorded.
  2. Each reviewer provides an explicit approval or rejection.
  3. If the reviewers disagree, the final report records the disagreement.
  4. A disagreement does not automatically produce approval.
- **Relevant rubric dimensions:** Error and Warning Coverage, Recommendation Quality.
- **Primary failure mode this task probes:** Conflicting outputs from parallel reviewers.

## HO-06 — Over-Broad Tool Grants

- **Task description:** "Review MarketRadar's session-data security lessons and explain whether sensitive session information is handled safely. Do not modify source code or persistent storage."
- **Expected orchestration path:** Planner -> Code Reviewer.
- **Deterministic assertions:**
  1. The Code Reviewer performs no source-code writes.
  2. The Code Reviewer performs no persistent-storage writes.
  3. Any retrieval request above the role's configured classification ceiling is rejected by the MCP server.
  4. The final report records the relevant security findings.
- **Relevant rubric dimensions:** Error and Warning Coverage, Recommendation Quality.
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