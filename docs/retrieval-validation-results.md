# Retrieval-Validation Results — proj-lessons

Server: retrieval MCP on :8002. Corpus: 8 docs under `project: proj-lessons`
(indexed as 26 chunks). Threshold: 0.65 vector; FTS5 keyword fallback when no
vector hit clears threshold. Overall bar: ≥ 80% of applicable checks pass.
Run date: 2026-09-24.

| Q | Query | Expected doc | Doc(s) returned (rank order) | Method | Similarity | Pass? | Notes |
|---|---|---|---|---|---|---|---|
| Q1 | Why did SMS appointment reminders never reach patients? | sms-notifications-were-never-wired | sms-notifications-were-never-wired (ch0) | vector | 0.698 | PASS | Clean direct match on the vector path. |
| Q2 | How should we handle failures returned by the appointment API routes? | standardize-route-error-handling | 1) sms-notifications (ch0) 2) standardize-route-error-handling (ch0) 3) standardize-route-error-handling (ch2) | keyword | null | FAIL | Vector missed (<0.65) → keyword fallback ranked the SMS doc first on lexical overlap ("failed / returned / swallowed"). Intended doc at #2. |
| Q3 | cursor connection leak too many connections | mysql-cursor-and-connection-leaks | mysql-cursor-and-connection-leaks | keyword | null | PASS | Literal-keyword scenario — matched via FTS5 keyword exactly as designed. |
| Q4a | What is the monthly budget ceiling for patient notifications? (ceiling=confidential) | notification-cost-and-vendor-budget (confidential) | notification-cost-and-vendor-budget (classification=confidential) | keyword | null | PASS | Confidential doc IS returned when the caller is authorized. |
| Q4b | Same query, ceiling=internal | (excluded) | confidential doc absent; only internal docs (store-appointment-times-in-utc, cors-config) returned, none on-topic | — | — | PASS | Confidential doc correctly excluded at internal ceiling. Boundary enforced by the server, not the agent. |
| Q5 | How should appointment status changes be validated? | appointment-status-state-machine | appointment-status-state-machine | keyword | null | PASS | Direct match (via keyword fallback). |
| Q6 | Appointment shows the wrong time to patients in another timezone | store-appointment-times-in-utc | store-appointment-times-in-utc (ch2 0.757, ch0 0.735) | vector | 0.757 | PASS | Disambiguation held — the status doc did NOT surface. |

## Summary
- **Passed: 6 / 7 applicable checks (85.7%)** — above the 80% bar. (Q4 counts as two.)
- **Failure: Q2** (near-miss). Root cause: vector search returned no hit above the
  0.65 threshold, so the server fell back to FTS5 keyword, which ranked the
  lexically-similar SMS doc above the intended error-handling doc.
- **Fix (at the retrieval layer, not the answer key):** either (a) lower the vector
  similarity threshold so short paraphrased queries stay on the vector path
  instead of falling to keyword, or (b) add a query-shaped sentence to
  lesson-standardize-route-error-handling.md (e.g. "When an appointment API route
  fails, it must return a consistent error response with an HTTP status and error
  code") so both vector and keyword rank it first. Re-index and re-run Q2 to
  confirm the fix holds without regressing Q1/Q6.
- **Observation:** 4 of 7 queries fell back to keyword (Q3, Q4a, Q5, plus Q2).
  The 0.65 threshold is high for short paraphrased queries; correct docs still
  returned in the passing cases, but the system leans on keyword more than ideal.

## Classification-boundary evidence (Q4a vs Q4b)
The only variable changed between the two runs was `classification_ceiling`
(confidential → internal). Under confidential, lesson-notification-cost-and-vendor-budget
was the top hit; under internal, it did not appear at all. The exclusion is
therefore produced by the server's ceiling filter (rank(classification) >
ceiling_rank → dropped), not by the agent choosing to withhold it. This is the
core trust property of the workflow.
