---
classification: internal
project: proj-csv
doc_type: feature
---

## Feature: CSV Import

The CSV import feature allows users to bulk-load tasks into the system from a CSV file. When a user uploads a file, the import service reads it line by line, validates each row against the task schema, and inserts valid rows into the database. Rows that fail validation are collected into an error report that the user can download after the import completes.

The import service enforces a maximum file size of 10 MB and a maximum row count of 5,000 tasks per import operation. Files that exceed either limit are rejected immediately with an informative error message before any rows are processed. Duplicate detection is based on the external task ID field. If a row shares an external ID with an existing task, the import service updates the existing record rather than creating a new one.

Column mapping is configurable. Users may upload a column-map JSON file alongside the CSV to specify which CSV column corresponds to which task field. If no column map is provided, the import service expects the CSV header row to use the canonical field names defined in the task schema documentation.
