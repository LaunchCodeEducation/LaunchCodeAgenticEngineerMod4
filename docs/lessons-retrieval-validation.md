# Lessons Learned Retrieval Validation Report

Project: `proj-lessons`

Ground truth: `docs/lessons-retrieval-ground-truth.md`

Embedding model: `all-MiniLM-L6-v2`

Similarity threshold: `0.65`

Top K: `3`

## Baseline — Paragraph Chunking

| Query | Result | Evidence |
|---|---|---|
| Q1 | FAIL | Correct `lesson-role-tool-scoping.md` retrieved through keyword fallback; no vector score >= 0.65 |
| Q2 | FAIL | Correct `lesson-readonly-reviewer.md` ranked first through keyword fallback; no vector score >= 0.65 |
| Q3 | PASS | `lesson-retrieval-calibration.md` returned in top results through keyword fallback |
| Q4 | PASS | `lesson-memory-scope-check.md` returned by vector retrieval with score 0.695 |
| Q5 | PASS | `lesson-human-approval-gate.md` returned by vector retrieval with score 0.650 |
| Q6 | PASS | Confidential `lesson-sensitive-configuration.md` was excluded under an internal classification ceiling |

Paragraph pass rate: **4/6 (66.7%)**

## Tuning Experiment — Semantic Chunking

Configuration:

- Chunking: `semantic`
- Boundary threshold: `0.75`

| Query | Result | Evidence |
|---|---|---|
| Q1 | FAIL | Correct `lesson-role-tool-scoping.md` retrieved through keyword fallback; no vector score >= 0.65 |
| Q2 | PASS | `lesson-readonly-reviewer.md` returned by vector retrieval with score 0.674 |
| Q3 | PASS | `lesson-retrieval-calibration.md` returned in top results through keyword fallback |
| Q4 | PASS | `lesson-memory-scope-check.md` returned by vector retrieval with score 0.726 |
| Q5 | PASS | `lesson-human-approval-gate.md` returned by vector retrieval with score 0.708 |
| Q6 | PASS | Confidential `lesson-sensitive-configuration.md` was excluded under an internal classification ceiling |

Semantic pass rate: **5/6 (83.3%)**

## Decision

Use **semantic chunking with boundary threshold 0.75** for the `proj-lessons` retrieval workflow.

Semantic chunking improved the validation result from **4/6 (66.7%)** to **5/6 (83.3%)** and improved vector retrieval for the Reviewer, memory-scope, and human-approval lessons.

Q1 remains a documented retrieval-quality gap. The correct document is found through keyword fallback, but it does not clear the fixed vector similarity threshold of 0.65. The threshold and ground-truth expectation were not weakened to force a passing result.

## Classification Boundary

The confidential lesson `lesson-sensitive-configuration.md` was not returned when retrieval used:

- `project_id = proj-lessons`
- `classification_ceiling = internal`
- `doc_type = lesson`

This confirms that the retrieval classification ceiling prevented confidential knowledge from leaking into an internal-only query.

Final validation status: **5/6 PASS — 83.3%**
