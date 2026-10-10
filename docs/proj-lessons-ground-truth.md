# Ground-Truth Query Set — proj-lessons (Appointment app)

Retrieval evaluation set for the Lessons Learned corpus. Threshold: a query
passes when the expected document is the top vector hit (or, for the
keyword-literal case, the top hit by the FTS5 fallback) **and** the
classification filter behaves as specified. Overall bar: ≥ 80% of applicable
queries pass (matching the Module 3 Lesson 2 standard).

Project filter for every query: `proj-lessons`.

---

## Q1 — Direct match
- **Query:** "Why did SMS appointment reminders never reach patients?"
- **Expected document:** lesson-sms-notifications-were-never-wired.md
- **Filters:** project_id=proj-lessons, classification ceiling=internal
- **Scenario:** Direct match — the query restates the lesson's subject.
- **Pass criterion:** the SMS lesson is the top hit with similarity ≥ 0.65.

## Q2 — Plausible near-miss
- **Query:** "How should we handle failures returned by the appointment API routes?"
- **Expected document:** lesson-standardize-route-error-handling.md
- **Near-miss competitor:** lesson-validate-input-at-the-route-boundary.md
  (also about routes; must rank below the error-handling doc).
- **Filters:** project_id=proj-lessons, classification ceiling=internal
- **Scenario:** Plausible near-miss — two route-related docs; the error-handling
  doc must win.
- **Pass criterion:** error-handling doc is top hit; input-validation doc may
  appear lower but must not outrank it.

## Q3 — Literal-keyword query
- **Query:** "cursor connection leak too many connections"
- **Expected document:** lesson-mysql-cursor-and-connection-leaks.md
- **Filters:** project_id=proj-lessons, classification ceiling=internal
- **Scenario:** Literal-keyword — exact phrases from the doc, tests the FTS5
  keyword path as much as the vector path.
- **Pass criterion:** the MySQL leak doc is the top hit by either vector
  similarity or keyword fallback; record which method returned it.

## Q4 — Classification-boundary query
- **Query:** "What is the monthly budget ceiling for patient notifications?"
- **Expected document (if authorized):** lesson-notification-cost-and-vendor-budget.md
  (classification=confidential)
- **Filters:** project_id=proj-lessons
- **Scenario:** Classification boundary. Run this query twice:
  - With a **confidential-ceiling** role: the confidential cost doc SHOULD be
    returned.
  - With an **internal-ceiling** role: the confidential cost doc MUST be
    excluded — expect either no hit above threshold or an internal doc, never
    the confidential doc.
- **Pass criterion:** the confidential doc is returned only to the
  confidential-ceiling role and is excluded for the internal-ceiling role. This
  is the boundary test that proves the server, not the agent, enforces the
  ceiling.

## Q5 — Direct match (scheduling)
- **Query:** "How should appointment status changes be validated?"
- **Expected document:** lesson-appointment-status-state-machine.md
- **Filters:** project_id=proj-lessons, classification ceiling=internal
- **Scenario:** Direct match.
- **Pass criterion:** the status state-machine doc is the top hit, similarity ≥ 0.65.

## Q6 — Cross-topic disambiguation
- **Query:** "Appointment shows the wrong time to patients in another timezone"
- **Expected document:** lesson-store-appointment-times-in-utc.md
- **Near-miss competitor:** lesson-appointment-status-state-machine.md
  (also about appointments; must rank lower).
- **Filters:** project_id=proj-lessons, classification ceiling=internal
- **Pass criterion:** the UTC/timezone doc is the top hit.
