---
classification: internal
project: proj-csv
doc_type: feature
---

## Feature: CSV Export

The CSV export feature builds its output file using a streaming writer that processes tasks row by row without loading the entire dataset into memory. When a user requests an export, the export service opens a writable stream, writes the header row containing column names, then iterates over the filtered task set in batches of 500 records. Each task is serialized to a CSV row and flushed to the stream immediately. Once all records are written the stream is closed and the completed file is handed off to the download handler. This streaming approach keeps memory consumption flat regardless of how many tasks are exported.

If CSV export generation fails at any stage, the service applies an exponential backoff retry policy. The first retry occurs after two seconds, the second after four seconds, and the third after eight seconds. After three failed attempts the job is marked as permanently failed and the user receives an error notification. Transient network errors and temporary storage unavailability are retried automatically. Validation errors and permission errors are not retried because they indicate a problem that will not resolve itself without user intervention.
