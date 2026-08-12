# Retrieval Ground-Truth Query Set

Project: `proj-csv`

Confidence threshold: `0.65`

Default pass criterion for precision queries: expected document appears in the top 3 results with `similarity_score >= 0.65`.

## Q1 — Export file format decision

- Query: "What file format did we choose for exporting the task list?"
- Expected top result: `decision-csv-format.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = decision`
- Pass: `decision-csv-format.md` appears in top 3 with score `>= 0.65`.
- Purpose: plain precision.

## Q2 — CSV export implementation notes vs CSV import decoy

- Query: "How does the CSV export feature build its output file?"
- Expected top result: `feature-csv-export.md`
- Decoy present: `feature-csv-import.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = feature`
- Pass: `feature-csv-export.md` appears in top 3 with score `>= 0.65`; the import decoy does not outrank it.
- Purpose: resistance to near-miss.

## Q3 — Literal error-code lookup

- Query: "What does error E_EXPORT_417 mean?"
- Expected result: `error-codes.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = reference`
- Pass: `error-codes.md` is returned. Keyword fallback is acceptable and expected if vector matching is not confident.
- Purpose: literal-keyword fallback.

## Q4 — Retry policy in a multi-topic feature document

- Query: "What retry policy should we use if CSV export generation fails?"
- Expected result: `feature-csv-export.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = feature`
- Pass: `feature-csv-export.md` appears in top 3 with score `>= 0.65`.
- Purpose: chunking sensitivity. Paragraph chunking may dilute this answer if it is merged with neighboring topics; semantic chunking should isolate it.

## Q5 — Ceiling enforcement: must not leak confidential cost document

- Query: "What are the internal cost figures for the export feature?"
- Best semantic match in corpus: `cost-breakdown.md` (`classification: confidential`)
- Filters: `project = proj-csv`, `classification_ceiling = internal`
- Pass: `cost-breakdown.md` does **not** appear in results. The tool returns only internal-or-below matches, or an empty result if none qualify.
- Purpose: classification ceiling.

## Q6 — Review standards

- Query: "What review standards should be applied to the CSV export implementation?"
- Expected top result: `standards-review.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = standard`
- Pass: `standards-review.md` appears in top 3 with score `>= 0.65`.
- Purpose: plain precision for Reviewer role.

## Q7 — User-visible task scoping decision

- Query: "Which tasks are allowed to appear in a CSV export?"
- Expected top result: `security-export-visibility.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = decision`
- Pass: `security-export-visibility.md` appears in top 3 with score `>= 0.65`.
- Purpose: retrieval of a prior security-related design decision.

## Q8 — Spreadsheet library reference

- Query: "Which spreadsheet library do we use to generate exports?"
- Expected top result: `api-spreadsheet-library.md`
- Filters: `project = proj-csv`, `classification_ceiling = internal`, `doc_type = reference`
- Pass: `api-spreadsheet-library.md` appears in top 3 with score `>= 0.65`.
- Purpose: reference-document lookup for Implementer role.
