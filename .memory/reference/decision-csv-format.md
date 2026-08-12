---
classification: internal
project: proj-csv
doc_type: decision
---

## Decision: CSV as the Export File Format for the Task List

After evaluating several candidate formats including JSON, XLSX, and plain CSV, the team decided to use CSV as the standard file format for exporting the task list. CSV was chosen because it is universally supported by spreadsheet applications, requires no special libraries to open, and produces compact output that is easy to diff in version control. The format aligns with what our primary users—project managers and team leads—already use in their day-to-day tooling.

Alternative formats were considered and rejected for the following reasons. JSON was ruled out because non-technical stakeholders cannot open it without additional tooling. XLSX was ruled out due to binary format complexity, licensing concerns around third-party spreadsheet libraries, and the additional dependency weight it would add to the export service. Plain text was too unstructured to be useful for downstream import workflows.

The decision is considered stable. Any future proposal to change the export format must include a migration plan for existing integrations and must be approved by the product lead before implementation begins.
