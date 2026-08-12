---
classification: internal
project: proj-csv
doc_type: reference
---

## Export Error Code Reference

This document lists error codes produced by the CSV export service and describes their meaning and recommended remediation steps.

**E_EXPORT_400** — Invalid export request. The request body failed schema validation. Check that all required fields are present and that field values match the expected types. No export job was created.

**E_EXPORT_403** — Permission denied. The requesting user does not have export rights for the specified project. Contact your project administrator to have the export permission granted to your role.

**E_EXPORT_404** — Project not found. The project identifier supplied in the export request does not match any known project. Verify the project ID and retry.

**E_EXPORT_417** — Expectation failed during export generation. This error indicates that the export service received a request it accepted but could not fulfil because an internal precondition was not met at generation time. Common causes include a task filter that returns zero rows, a missing template configuration, or a column mapping that references a field that no longer exists in the task schema. Inspect the job detail record for the specific precondition message and correct the export configuration before retrying.

**E_EXPORT_500** — Internal server error. An unexpected failure occurred inside the export service. The error has been logged automatically. If the error persists after retrying, open a support ticket and include the job ID from the error response.

**E_EXPORT_503** — Export service temporarily unavailable. The service is under maintenance or experiencing high load. Retry after the interval specified in the Retry-After response header.
