# Final Report — Lessons Learned Workflow (proj-lessons)

**Target Codebase:** Appointment scheduling app (Flask + MySQL + React).
**Scope identifier:** proj-lessons.
**Date:** 2026-09-25.

## 1. What was built
A lightweight Lessons Learned workflow layered onto the existing orchestration
(Planner, Implementer, Reviewer, plus Orchestrator and a Project Manager role).
Two MCP servers supply the knowledge layer: a retrieval server over a curated
reference corpus, and a storage server for durable, audited project knowledge.
Both run on the `agent-internal` bridge network (loopback allowed, egress
blocked), registered to the harness via a committed `.mcp.json`.

## 2. Reference corpus (curated input — 8 docs)
Grounded in real appointment-app findings: SMS never wired, route error-handling
standardization (decision-004), appointment status state machine, MySQL
cursor/connection leaks, input validation at the route boundary, storing times
in UTC, CORS config, and one **confidential** doc on notification vendor cost /
budget ceiling. All tagged `project: proj-lessons`. Indexed as 26 chunks.

## 3. Ground-truth evaluation
Six queries covering direct match, plausible near-miss, literal-keyword, and
classification-boundary scenarios. **Result: 6/7 applicable checks passed
(85.7%)**, above the 80% bar. The one failure (Q2, near-miss) is documented with
an enforcement-point fix in retrieval-validation-results.md and in Question 3.
The classification boundary (Q4a confidential ceiling returns the cost doc; Q4b
internal ceiling excludes it) passed — the core trust property.

## 4. Role access (enforced through tool grants, not instructions)
Enforced in each agent's `tools:` frontmatter (the harness exposes only listed
tools) and via the retrieval server's classification ceiling.

| Role | Tools granted | Storage/retrieval | Ceiling |
|---|---|---|---|
| Orchestrator | (main session) | logs decisions; delegates | n/a |
| Planner | Read, Grep, Glob, mcp__retrieval__retrieve | retrieval read only | internal |
| Implementer | Read, Write, Edit, mcp__storage__write_entry | storage write only | internal |
| Reviewer | Read, mcp__retrieval__retrieve | retrieval read only | internal |

The Implementer holds `write_entry` only — no `read_entry`/`list_entries`; the
Planner and Reviewer hold retrieval only — no storage write. An earlier run
attempt failed closed ("would be spawned with zero tools — refusing") when the
grants referenced unregistered tools, which is itself evidence the harness
enforces the grant list rather than trusting instructions.

## 5. Workflow run evidence
Task: add server-side validation of appointment status transitions on
`PATCH /appointments/<id>/status` (allowed states scheduled, confirmed,
completed, cancelled, no-show; only legal transitions).

- **Planner** retrieved and cited `lesson-appointment-status-state-machine.md`
  and `lesson-standardize-route-error-handling.md`, and flagged the
  coding-standards governance guard (no new state-machine pattern without a
  logged decision). Paused at the human checkpoint.
- **Human checkpoint** resolved four design questions (log decision-007 first;
  scheduled→no-show legal; same-status resubmit is an idempotent 200; frontend
  out of scope).
- **Orchestrator** logged decision-007.md, updated decision-003.md and
  MEMORY_INDEX.md.
- **Implementer** edited `appointment-backend/app.py` (widened VALID_STATUSES to
  5 states, added STATUS_TRANSITIONS, same-status no-op 200 + illegal-transition
  409 gates ahead of the update; 31 insertions / 4 deletions) and recorded one
  lesson via `write_entry` → **entry_id 59af3e10-4625-4c0a-90be-ed311617b2ad**
  (entry_type=lesson, classification=internal), titled "Order of gates matters
  when adding a transition check on top of an existing value check."
- **Reviewer** retrieved and cited `lesson-mysql-cursor-and-connection-leaks.md`
  and coding-standards.md; confirmed parameterized SQL and gate ordering, and
  **found a real bug**: `STATUS_TRANSITIONS[row["status"]]` could raise an
  uncaught KeyError because schema.sql stores status as unconstrained
  VARCHAR(20). Fixed with `.get(row["status"], set())`.
- **Follow-ups the review surfaced (not in scope):** TOCTOU race between SELECT
  and UPDATE (mitigation: compare-and-swap `WHERE status = %s`, treat 0 rows as
  409); no auth on routes (pre-existing); frontend missing no-show + 409
  handling.
- **Audit log line:** `{"calling_role": "unknown", "classification":
  "internal", "entry_id": "59af3e10-...", "operation": "write_entry",
  "project_id": "proj-lessons", "timestamp": "2026-09-25T18:28:20Z"}`.

## 6. Verification results (Step 6)
- [x] Retrieval results include citations to source documents/chunks — shown in
      Steps 3 and 5.
- [x] The Implementer's new lesson was written through the storage MCP server —
      entry_id 59af3e10-..., audit-logged.
- [x] The entry survives in a NEW `claude` conversation started without
      --continue/--resume — a fresh session `read_entry` returned the full
      lesson, proving storage-system persistence rather than reused context.
- [x] The audit log records the storage activity — verified.
- [x] A role at an internal ceiling cannot retrieve the confidential document —
      Q4b returned only internal docs; the confidential cost doc was excluded.
- [x] No role bypassed the MCP servers to touch storage.db / audit log /
      reference files directly — enforced by tool grants (Read/Write/Edit/MCP
      only; no shell for these roles).

**Limitation found:** the audit entry recorded `calling_role: "unknown"` because
the Implementer's `write_entry` did not pass `calling_role`. The operation is
logged, but role attribution is only as reliable as the caller's input. The
enforcement-point fix is to have the storage server require a valid
`calling_role` and reject writes without one, rather than defaulting to
"unknown."

---

## Question 1 — Corpus vs. persistent storage
I placed **curated, reviewed, durable lessons** in the reference corpus: stable
knowledge vetted for accuracy and classification, meant to be retrieved
read-only across many runs (e.g. "store appointment times in UTC," "standardize
route error handling," and the confidential notification-cost lesson). I wrote a
**newly discovered finding from the run itself** to persistent storage via
`write_entry` — the gate-ordering lesson (entry_id 59af3e10-...), which did not
exist before this run and was produced as a side effect of doing the work. The
two belong in different places because they differ in trust and lifecycle: the
corpus is human-reviewed input that agents may read but not mutate, so it stays
authoritative and its classification is controlled at ingest; storage is
append-time output that must be captured immediately and audited, but has not
yet been curated. Mixing them would let unreviewed run output silently become
authoritative reference and would lose the audit trail that makes new writes
accountable.

## Question 2 — Most impactful boundary + evidence of system enforcement
The **classification ceiling on the retrieval server** had the greatest effect
on trustworthiness, with the Implementer's single-tool storage grant a close
second. The evidence that the ceiling is enforced by the system, not an
instruction, is the Q4 pair: with a confidential ceiling the cost doc was the
top hit; with the internal ceiling used by every workflow role, the identical
query returned only internal docs and excluded the confidential doc entirely.
The only thing that changed between the two runs was the ceiling value passed to
the server, so the exclusion came from the server's filter
(`rank(classification) > ceiling_rank` → dropped), not from an agent choosing to
withhold it. For the tool grant, the enforcement showed twice: the Implementer
recorded its lesson through `write_entry` but never had `read_entry`/`list_entries`
to inspect storage, and an earlier misconfigured run failed closed with "would be
spawned with zero tools — refusing" rather than falling back to a broader
toolset. Both are harness-level enforcement, not honor-system compliance.

## Question 3 — What the ground-truth evaluation revealed
The evaluation showed the retrieval system is reliable on direct and
disambiguation queries but exposed a weakness in how it falls back to keyword
search. One clear PASS: Q6 ("appointment shows the wrong time in another
timezone") returned `lesson-store-appointment-times-in-utc.md` by vector
similarity at 0.757 and correctly ranked the appointment-status doc below it —
the disambiguation held. One FAIL: Q2 ("how should we handle failures returned
by the appointment API routes?"), a deliberate near-miss, returned
`lesson-sms-notifications-were-never-wired.md` on top instead of the intended
`lesson-standardize-route-error-handling.md`. The cause is mechanical: the vector
score for the paraphrased query fell below the 0.65 threshold, so the server fell
back to FTS5 keyword search, and the SMS doc — dense with "failed / returned /
swallowed" — won on lexical overlap. To improve this without changing the answer
key, I would fix it at the retrieval layer: lower the vector threshold so short
paraphrases stay on the semantic path instead of dropping to keyword, or add a
query-shaped sentence to the error-handling doc so it matches both paths. I would
not relabel Q2's expected document to whatever the server currently returns —
that would hide the weakness rather than fix it. More broadly, four of seven
queries fell back to keyword, so the 0.65 threshold is likely tuned high for this
short-query corpus; that is the first knob I would adjust and re-measure against
the same ground-truth set.
