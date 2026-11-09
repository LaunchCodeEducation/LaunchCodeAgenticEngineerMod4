# Retrieval Quality Report

Actual results from running `python3 mcp/retrieval/run_ground_truth.py` in `agentic_engineer_3` on 2026-10-26. (Replaces the prefilled "expected" report that shipped with the sample repo.)

- Corpus: `.memory/reference/` (8 documents; all carry valid classification front-matter: no `WARNING:` lines at startup)
- Server: `mcp/retrieval/server.py` on port `8002`, model `all-MiniLM-L6-v2` (downloaded from Hugging Face on first start, ~91 MB; not baked into the image)
- Threshold: `0.65`, `top_k`: `3`
- Ground truth: `docs/retrieval-ground-truth.md` (8 queries, unchanged throughout)

## Summary

| Run | Chunking | Chunks indexed | Pass rate | Change from previous run |
| :--- | :--- | :--- | :--- | :--- |
| 1 (baseline) | paragraph (default) | 25 | **7/8 (88%)** | — |
| 2 (one fix) | semantic (`--chunking semantic`, boundary 0.75) | 29 | **6/8 (75%)**, below floor | Q8 still FAIL; **Q4 regressed** PASS → FAIL |
| 3 (revert) | **paragraph** (reverted) | 25 | **7/8 (88%)**, above the 80% floor | Identical to run 1 query-for-query and score-for-score (Q1 0.759, Q2 0.682, Q4 0.843, Q8 keyword-only): stable. Semantic rejected because of the Q4 regression; Q8 recorded as a known gap |

## Per-query results

| ID | Kind | Expected | Run 1: paragraph | Run 2: semantic |
| :--- | :--- | :--- | :--- | :--- |
| Q1 | precision | `decision-csv-format.md` | PASS: `decision-csv-format.md#0` vector **0.759** | PASS: #0 vector 0.750 |
| Q2 | precision + decoy (`feature-csv-import.md`) | `feature-csv-export.md` | PASS: `feature-csv-export.md#0` vector **0.682** (decoy not in top 3) | PASS: #0 vector 0.765 |
| Q3 | keyword (`E_EXPORT_417`) | `error-codes.md` | PASS: `error-codes.md#2` vector **0.779**, #0 0.656, #3 0.650 | PASS: #2 vector 0.683, #0 0.650 |
| Q4 | precision, multi-topic doc | `feature-csv-export.md` | PASS: `feature-csv-export.md#1` vector **0.843** | **FAIL**: only keyword results (`feature-csv-export.md#1`, `feature-csv-import.md#2`, `feature-csv-export.md#2`), no vector ≥ 0.65 |
| Q5 | ceiling (`cost-breakdown.md` is confidential) | `cost-breakdown.md` absent | PASS: keyword results `decision-csv-format.md#0`, `feature-csv-import.md#0`, `error-codes.md#2`; confidential doc absent | PASS: confidential doc absent |
| Q6 | precision | `standards-review.md` | PASS: vector **0.866** | PASS: vector 0.866 |
| Q7 | precision | `security-export-visibility.md` | PASS: vector **0.761** (+ `decision-csv-format.md#0` 0.702) | PASS: vector 0.804 |
| Q8 | precision | `api-spreadsheet-library.md` | **FAIL**: correct doc returned only via keyword fallback (chunks #1, #0, #2, score `None`), no vector ≥ 0.65 | **FAIL**: same (chunks #2, #0, #1, keyword) |

## Observations

- **Ceiling holds (Q5):** the confidential `cost-breakdown.md`, the best semantic match for a cost query, never appeared under `classification_ceiling = internal`. No permitted doc cleared 0.65, so the keyword fallback fired and returned only internal docs.
- **Keyword fallback was exercised by Q5 and Q8, not by Q3.** Q3 (`E_EXPORT_417`) was written as the keyword case, but the vector search found `error-codes.md` above 0.65 in both runs, so the fallback never fired for it. Q3 still passes (its rule only requires the doc to be returned), but it does not prove the fallback; Q5/Q8 do. Worth a sharper keyword query in a later revision of the ground truth (a new query, not an edit of Q3).
- **Near-miss decoy resisted (Q2):** `feature-csv-import.md` did not displace `feature-csv-export.md` in either run.

## Failure analysis and fix log

### Q8: spreadsheet library (precision)
- Symptom: the correct document is retrieved, but only by keyword; no chunk reaches 0.65 by meaning.
- Hypothesis: the query's wording ("spreadsheet library ... generate exports") doesn't match the chunks' dominant meaning. The answer paragraph is mostly about `csv-stream-writer`'s streaming, RFC 4180 quoting, and versioning, so its embedding is "CSV streaming library internals", diluted relative to the question. This is the lesson's "appears but below 0.65" case, which points at chunking.
- Fix tried (one change): semantic chunking, which should isolate the "which library" sentence. **Result: no improvement** (still keyword-only) and it **regressed Q4**.
- Decision: revert to paragraph chunking; record Q8 as a **known gap**. The ground-truth entry and threshold are unchanged.
- Next candidates (one at a time, full re-run each): a smaller `max_words` for paragraph chunks; adding a one-sentence summary line ("FashionMate/the export service uses csv-stream-writer as its spreadsheet/CSV library") to the document itself, since the corpus is curated source.
- Impact while open: an implementer asking "which library do we use" still gets the right document, labeled `keyword`, so it should treat the answer as lower-confidence and read the cited chunk.

### Q4: retry policy (regression under semantic chunking)
- Symptom: PASS at 0.843 with paragraph chunks; FAIL (keyword only) with semantic chunks.
- Hypothesis: at boundary 0.75 the semantic chunker split the retry-policy text into smaller fragments; separated from the "CSV export generation" context, no fragment matched the full question above 0.65. This contradicts the ground-truth file's expectation that semantic chunking would help Q4, which is a useful counter-example.
- Resolution: reverting to paragraph chunking restores Q4.

## Bar

**7/8 (88%) with paragraph chunking, stable across the baseline run; above the 80% floor.** Q8 is understood and documented, so the server can be connected to subagents with that gap recorded.
