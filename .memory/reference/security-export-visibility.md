---
classification: internal
project: proj-csv
doc_type: decision
---

## Decision: Task Visibility Rules for CSV Export

This document records the access-control decision governing which tasks are permitted to appear in a CSV export file. The rules apply to all export jobs regardless of who initiates them.

Only tasks that the requesting user is already permitted to read within the application may be included in an exported CSV file. The export service re-evaluates row-level read permissions for every task at export generation time using the same permission engine as the task list API. Tasks the user cannot read in the UI will not appear in the export even if the user constructs a filter that would otherwise match them. This ensures that exporting does not bypass any visibility restriction already enforced elsewhere in the system.

Archived tasks are excluded from all exports by default. A user may opt in to including archived tasks by enabling the include_archived flag in the export request, provided they hold the archive-viewer permission. Deleted tasks are permanently excluded and cannot be included in any export regardless of permissions or flags.

Tasks belonging to private sub-projects are excluded unless the requesting user is an explicit member of that sub-project. Project-level export permission does not grant access to tasks in private sub-projects. This rule was established to prevent accidental disclosure of tasks that project members have intentionally scoped to a smaller audience within the same project.
