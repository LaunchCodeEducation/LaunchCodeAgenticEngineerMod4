# Lessons Learned Workflow Final Report

Project: `proj-lessons`

## Retrieval Corpus

The curated reference corpus contains six Lessons Learned documents based on real MarketRadar work. Five are classified `internal` and one session-security lesson is classified `confidential`.

The frozen ground-truth benchmark contains six queries covering direct matches, near misses, keyword fallback, and a classification boundary.

## Retrieval Validation

Results:

- Passed: 5
- Failed: 1
- Total: 6
- Pass rate: 83.3%
- Required minimum: 80%
- Result: PASS

Q6 failed because `lesson-shared-backend-clients.md` was returned only through keyword fallback. The frozen criterion required vector retrieval with a score of at least 0.65.

The expected answer was not rewritten after evaluation.

## Role Access and Enforcement

Role grants are defined in `mcp/roles.allowlist.json` and agent tool exposure is restricted in `.claude/agents/`.

- Planner: retrieval only, internal ceiling.
- Implementer: retrieval plus `write_entry`, internal ceiling.
- Code Reviewer: retrieval only, internal ceiling.
- Tester: retrieval only, internal ceiling.
- Verifier: storage `read_entry` and `list_entries` only, internal ceiling.

A Planner attempt to request a `confidential` retrieval ceiling was denied:

`planner may retrieve only up to internal`

Storage enforcement also denied operations not granted to the calling role.

## Orchestration Run

A real MarketRadar task was run through the configured Planner -> human approval -> Implementer -> Tester workflow.

Task:

Improve `RunSearchError` diagnostics in `tracker-api/src/services/search-runner.ts` so failed saved-search runs include both the saved search name and ID.

Planner:
- Retrieved relevant prior lessons before proposing an approach.
- Identified `lesson-empty-scrape-diagnostics.md` and `lesson-shared-backend-clients.md` as relevant.
- Proposed a one-file change.
- Stopped for human approval.

Human checkpoint:
- Plan approved before implementation.

Implementer:
- Updated the `RunSearchError` message to include both `search.name` and `search.id`.
- Stored a new lesson through the storage MCP.

Stored lesson:
- Entry ID: `eda14c5f-4517-424f-874e-7c5f4d5ba543`
- Project: `proj-lessons`
- Type: `lesson`
- Classification: `internal`

Tester:
- Retrieved relevant lessons before verification.
- Confirmed the scoped code change.
- `npm run build` passed.
- Full Vitest suite passed: 15/15 tests.
- Reported PASS against all acceptance criteria.

Both Planner and Tester observed prompt-injection-like text in tool output and ignored it because it conflicted with their configured role and workflow.

## Persistence Verification

The original Docker container was exited and destroyed.

A new container was started with the same `marketradar-memory` volume.

Using the storage MCP as `verifier`, `list_entries` returned the real Implementer-created lesson:

`eda14c5f-4517-424f-874e-7c5f4d5ba543`

A completely fresh Claude conversation, started without `--resume` or `--continue`, then used only the storage MCP to:

1. find the lesson with `list_entries`
2. read the exact lesson with `read_entry`

No SQLite database inspection or direct `/memory` access was used as persistence evidence.

## Audit Evidence

`/memory/storage-audit.log` recorded the real Implementer write:

- calling role: `implementer`
- operation: `write_entry`
- project: `proj-lessons`
- entry ID: `eda14c5f-4517-424f-874e-7c5f4d5ba543`
- classification: `internal`

## Classification Boundary

After restarting the retrieval service, a Planner request for a `confidential` ceiling was rejected:

`Error calling tool 'retrieve': planner may retrieve only up to internal`

This confirms the configured internal ceiling remained enforced after restart.

## Sandbox Network Observation

The `agent-internal` Docker network was verified as an internal bridge network.

Because that network blocks external DNS/API access, Claude Code could not reach the external Claude API while attached only to that network.

The orchestration run therefore used the same container and mounted persistence volumes on the default Docker network so Claude Code could reach the external API.

This limitation is documented rather than hidden.

## Trust Boundary Note

Role enforcement is provided by:

- agent tool allow-lists
- MCP role allow-list checks
- classification ceilings
- storage operation checks
- audit logging

The current MCP interface still accepts `calling_role` as a caller-supplied field, so role identity is enforced by configuration and tool exposure rather than cryptographically authenticated identity.

## Written Responses

### Q1 — Curated corpus vs persistent storage

The curated corpus contains reviewed reference documents intended for retrieval and evaluation.

Persistent storage holds runtime-created lessons and state that must survive container and conversation restarts.

### Q2 — Trust boundary and enforcement evidence

The trust boundary is enforced through narrow agent tool exposure plus server-side MCP checks for role permissions and classification ceilings.

Evidence includes:
- denied Planner confidential retrieval
- denied unauthorized storage operations
- successful Implementer-only write
- audit log entry for the write
- prompt-injection-like retrieved content being ignored by Planner and Tester because it conflicted with their configured role

A remaining limitation is that `calling_role` is caller-supplied rather than cryptographically authenticated.

### Q3 — Ground-truth result and improvement

The benchmark passed 5 of 6 queries for 83.3%, above the required 80%.

Q6 failed because the expected shared-backend lesson was returned only through keyword fallback instead of vector retrieval at the required threshold.

The answer key remained frozen. Improvement should target embeddings, chunking, indexing, or query behavior and then rerun the same benchmark without changing the expected answer.
