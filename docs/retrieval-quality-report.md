# Retrieval Quality Report

Corpus: `.memory/reference/` (15 documents)

Server: `mcp/retrieval/server.py` on port `8002`

Embedding model: `all-MiniLM-L6-v2`

Threshold: `0.65`

`top_k`: `3`

Ground truth: `docs/retrieval-ground-truth.md`

## Summary

| Run | Chunking | Pass Rate | Notes |
| --- | --- | --- | --- |
| Baseline | paragraph | 7/8 (87.5%) | Clears the 80% validation floor. Q8 remains below the vector confidence threshold and falls back to keyword retrieval. |
| Tuning experiment | semantic (boundary threshold 0.75) | 6/8 (75%) | Regression: Q4 and Q8 failed. |
| Final configuration | paragraph | 7/8 (87.5%) | Stable rerun reproduced the baseline result. Paragraph chunking retained. |

## Q1 — Export file format decision

- Query: "What file format did we choose for exporting the task list?"
- Expected: `decision-csv-format.md` in top 3 with score `>= 0.65`.
- Actual:
  1. `decision-csv-format.md` chunk 0 — vector, score `0.759`
- Result: **PASS**

## Q2 — CSV export implementation notes vs CSV import decoy

- Query: "How does the CSV export feature build its output file?"
- Expected: `feature-csv-export.md` in top 3 with score `>= 0.65`; `feature-csv-import.md` must not outrank it.
- Actual:
  1. `feature-csv-export.md` chunk 0 — vector, score `0.682`
- Result: **PASS**
- Note: The CSV import decoy did not outrank the expected export document.

## Q3 — Literal error-code lookup

- Query: "What does error E_EXPORT_417 mean?"
- Expected: `error-codes.md` returned; keyword fallback is acceptable if vector matching is not confident.
- Actual:
  1. `error-codes.md` chunk 2 — vector, score `0.779`
  2. `error-codes.md` chunk 0 — vector, score `0.656`
  3. `error-codes.md` chunk 3 — vector, score `0.650`
- Result: **PASS**
- Note: Vector retrieval was confident, so keyword fallback was not required.

## Q4 — Retry policy

- Query: "What retry policy should we use if CSV export generation fails?"
- Expected: `feature-csv-export.md` in top 3 with score `>= 0.65`.
- Actual:
  1. `feature-csv-export.md` chunk 1 — vector, score `0.843`
- Result: **PASS**

## Q5 — Classification ceiling enforcement

- Query: "What are the internal cost figures for the export feature?"
- Forbidden result: `cost-breakdown.md` because it is classified `confidential`.
- Ceiling: `internal`
- Actual:
  1. `decision-csv-format.md` chunk 0 — keyword, score `null`
  2. `feature-csv-import.md` chunk 0 — keyword, score `null`
  3. `error-codes.md` chunk 2 — keyword, score `null`
- Result: **PASS**
- Note: `cost-breakdown.md` did not appear, confirming that the classification ceiling prevented confidential data from leaking.

## Q6 — Review standards

- Query: "What review standards should be applied to the CSV export implementation?"
- Expected: `standards-review.md` in top 3 with score `>= 0.65`.
- Actual:
  1. `standards-review.md` chunk 0 — vector, score `0.866`
- Result: **PASS**

## Q7 — User-visible task scoping decision

- Query: "Which tasks are allowed to appear in a CSV export?"
- Expected: `security-export-visibility.md` in top 3 with score `>= 0.65`.
- Actual:
  1. `security-export-visibility.md` chunk 0 — vector, score `0.761`
  2. `decision-csv-format.md` chunk 0 — vector, score `0.702`
- Result: **PASS**

## Q8 — Spreadsheet library reference

- Query: "Which spreadsheet library do we use to generate exports?"
- Expected: `api-spreadsheet-library.md` in top 3 with vector score `>= 0.65`.
- Actual:
  1. `api-spreadsheet-library.md` chunk 1 — keyword, score `null`
  2. `api-spreadsheet-library.md` chunk 0 — keyword, score `null`
  3. `api-spreadsheet-library.md` chunk 2 — keyword, score `null`
- Result: **FAIL**
- Hypothesis: The correct document is indexed and keyword retrieval finds it reliably, but none of its paragraph chunks reaches the `0.65` vector confidence threshold for this query. The relevant answer exists in chunk 0, but the embedding match remains below the configured confidence threshold.
- Decision: Do not lower the confidence threshold merely to force this query to pass.

## Chunking Tuning Experiment

A single tuning experiment was performed using semantic chunking with a boundary threshold of `0.75`.

Semantic run results:

- Q1: PASS — `decision-csv-format.md`, vector `0.750`
- Q2: PASS — `feature-csv-export.md`, vector `0.765`
- Q3: PASS — `error-codes.md`, best vector `0.683`
- Q4: FAIL — results fell back to keyword retrieval
- Q5: PASS — confidential `cost-breakdown.md` remained absent
- Q6: PASS — `standards-review.md`, vector `0.866`
- Q7: PASS — `security-export-visibility.md`, vector `0.804`
- Q8: FAIL — `api-spreadsheet-library.md` returned through keyword fallback

Semantic pass rate: **6/8 (75%)**.

The semantic configuration introduced a regression in Q4 without fixing Q8. Therefore the experiment was reverted.

## Final Decision

Retain **paragraph chunking** as the retrieval server's configuration.

The final paragraph run reproduced the original result of **7/8 passing (87.5%)**, demonstrating a stable result above the required 80% validation floor.

The remaining Q8 gap is understood and documented: the correct source is retrieved through keyword fallback, but its vector similarity does not meet the pre-established `0.65` precision criterion. No confidence threshold was weakened to force a passing result.

Final validation status: **7/8 PASS — 87.5% — validation bar cleared with one documented retrieval-quality gap.**
