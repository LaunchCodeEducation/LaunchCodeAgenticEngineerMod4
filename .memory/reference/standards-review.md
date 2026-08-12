---
classification: internal
project: proj-csv
doc_type: standard
---

## Review Standards for the CSV Export Implementation

All pull requests that touch the CSV export implementation must satisfy the following review standards before they can be merged. These standards apply to the export service, the export worker, the column-mapping layer, and any shared libraries used exclusively by the export pipeline.

Code reviewers must verify that streaming is used throughout the output path. No implementation may buffer the full task set in memory before writing. Reviewers should check that the batch size constant is configurable via environment variable and that the default value is documented in the service README. Any change that introduces a new dependency on a third-party library requires sign-off from a senior engineer in addition to the standard two-reviewer requirement.

Security review is mandatory for any change that modifies access-control checks, changes which task fields are included in export output, or alters the authentication path for export download URLs. Security reviews must be completed by a team member who holds the security-reviewer role and must be documented with a checklist comment on the pull request.

Performance review is required for changes that affect the main export loop or the streaming write path. The reviewer must confirm that the change has been benchmarked against the baseline export throughput figure recorded in the performance log. A regression of more than five percent in throughput requires a follow-up task before the change can be merged to the main branch.
