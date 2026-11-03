# Lessons Learned Retrieval Ground Truth

Project: `proj-lessons`

This file defines the fixed retrieval benchmark for the MarketRadar Lessons
Learned corpus. Expected answers must not be changed merely to make retrieval
results pass.

## Q1 — Direct semantic match

Query:
"What should we verify before committing MarketRadar to a new marketplace source?"

Expected document:
`lesson-marketplace-source-feasibility.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
Expected document appears in the top 3 results with vector similarity >= 0.65.

## Q2 — Plausible near-miss

Query:
"How should MarketRadar be designed so Facebook could later be replaced by another marketplace?"

Expected document:
`lesson-source-adapter-isolation.md`

Plausible near-miss:
`lesson-marketplace-source-feasibility.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
Expected document app in the top 3 results with vector similarity >= 0.65.

## Q3 — Authentication distinction

Query:
"If Facebook login succeeds, does that prove MarketRadar can scrape listings?"

Expected document:
`lesson-authentication-vs-scrape-access.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
Expected document appears in the top 3 results with vector similarity >= 0.65.

## Q4 — Empty scrape diagnostics

Query:
"What evidence should we capture when a scraper unexpectedly returns zero listings?"

Expected document:
`lesson-empty-scrape-diagnostics.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
Expected document appears in the top 3 results. Vector or keyword retrieval is acceptable.

## Q5 — Classification boundary

Query:
"How should reusable marketplace cookies, tokens, credentials, and session data be protected?"

Sensitive document:
`lesson-session-data-security.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
`lesson-session-data-security.md` MUST NOT appear in the results because it is classified `confidential`.

## Q6 — Shared clients

Query:
"Where should business logic live so the React web app and a future mobile client can share it?"

Expected document:
`lesson-shared-backend-clients.md`

Filters:
- project: `proj-lessons`
- classification ceiling: `internal`

Pass criterion:
Expected document appears in the top 3 results with vector similarity >= 0.65.

## Overall pass criterion

At least 80% of the ground-truth queries must pass without changing the expected answers after evaluation begins.
