# Lessons Learned Retrieval Ground-Truth

Project: `proj-lessons`

Confidence threshold: `0.65`

Default pass criterion for precision queries: expected document appears in the top 3 results with `similarity_score >= 0.65`.

## Q1 — Role tool scoping

- Query: "How should we decide which tools each subagent receives?"
- Expected top result: `lesson-role-tool-scoping.md`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-role-tool-scoping.md` appears in top 3 with score `>= 0.65`.
- Purpose: direct match.

## Q2 — Reviewer boundaries

- Query: "Should the Reviewer be allowed to modify the code it is reviewing?"
- Expected top result: `lesson-readonly-reviewer.md`
- Near-miss document: `lesson-role-tool-scoping.md`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-readonly-reviewer.md` appears in top 3 with score `>= 0.65` and is not outranked by the more general tool-scoping lesson.
- Purpose: plausible near-miss.

## Q3 — Retrieval threshold rule

- Query: "What should we do when retrieval finds the right document but it does not clear the 0.65 confidence threshold?"
- Expected top result: `lesson-retrieval-calibration.md`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-retrieval-calibration.md` is returned in the top 3.
- Purpose: literal-keyword / threshold lookup.

## Q4 — Memory project scope

- Query: "What must be checked before reusing stored knowledge from a previous run?"
- Expected top result: `lesson-memory-scope-check.md`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-memory-scope-check.md` appears in top 3 with score `>= 0.65`.
- Purpose: direct match.

## Q5 — Human approval

- Query: "Where should a human approval gate appear in the orchestrated workflow?"
- Expected top result: `lesson-human-approval-gate.md`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-human-approval-gate.md` appears in top 3 with score `>= 0.65`.
- Purpose: direct match.

## Q6 — Confidential configuration boundary

- Query: "What sensitive configuration and authentication details should agents be allowed to access?"
- Best semantic match in corpus: `lesson-sensitive-configuration.md`
- Document classification: `confidential`
- Filters: `project = proj-lessons`, `classification_ceiling = internal`, `doc_type = lesson`
- Pass: `lesson-sensitive-configuration.md` does **not** appear in results.
- Purpose: classification-boundary enforcement.
