# Lessons Learned Retrieval Validation

Project: `proj-lessons`

The frozen ground-truth benchmark contains 6 queries. Passing threshold: at least 80%.

## Results

### Q1 — PASS

Expected document: `lesson-marketplace-source-feasibility.md`

Returned:
- `lesson-source-adapter-isolation.md#1` — vector, 0.691
- `lesson-marketplace-source-feasibility.md#1` — vector, 0.685

The expected document appeared in the top 3 with a vector score above 0.65.

### Q2 — PASS

Expected document: `lesson-source-adapter-isolation.md`

Returned:
- `lesson-source-adapter-isolation.md#0` — vector, 0.784
- `lesson-source-adapter-isolation.md#1` — vector, 0.727
- `lesson-marketplace-source-feasibility.md#0` — vector, 0.709

The expected document ranked first and exceeded the required vector threshold.

### Q3 — PASS

Expected document: `lesson-authentication-vs-scrape-access.md`

Returned:
- `lesson-authentication-vs-scrape-access.md#0` — vector, 0.800
- `lesson-marketplace-source-feasibility.md#0` — vector, 0.771

The expected document ranked first and exceeded the required vector threshold.

### Q4 — PASS

Expected document: `lesson-empty-scrape-diagnostics.md`

Returned:
- `lesson-empty-scrape-diagnostics.md#0` — vector, 0.796
- `lesson-empty-scrape-diagnostics.md#1` — vector, 0.714

The expected document ranked first. The ground truth permits either vector or keyword retrieval for this literal-keyword case.

### Q5 — PASS

Classification-boundary query.

Returned at the `internal` ceiling:
- `lesson-shared-backend-clients.md#1` — keyword
- `lesson-shared-backend-clients.md#0` — keyword
- `lesson-source-adapter-isolation.md#1` — keyword

The confidential session-security lesson did not appear, so the classification boundary held.

A separate enforcement test also attempted to raise the Planner ceiling to `confidential` and was denied:

`planner may retrieve only up to internal`

### Q6 — FAIL

Expected document: `lesson-shared-backend-clients.md`

Returned:
- `lesson-shared-backend-clients.md#1` — keyword
- `lesson-shared-backend-clients.md#0` — keyword
- `lesson-source-adapter-isolation.md#1` — keyword

The expected document was returned, but only through keyword fallback. The frozen criterion requires vector retrieval with a score of at least 0.65, so this query fails.

The expected answer was not rewritten after evaluation. The failure indicates that the current embedding/chunking behavior does not produce sufficient semantic similarity for this phrasing.

## Overall

- Passed: 5
- Failed: 1
- Total: 6
- Pass rate: 83.3%
- Required minimum: 80%
- Result: PASS

The retrieval workflow meets the exercise minimum while preserving the frozen ground-truth benchmark and documenting the remaining Q6 retrieval-quality weakness.
