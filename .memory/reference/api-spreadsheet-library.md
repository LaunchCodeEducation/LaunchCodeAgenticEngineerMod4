---
classification: internal
project: proj-csv
doc_type: reference
---

## Spreadsheet Library Reference

The CSV export service uses **csv-stream-writer** (version 2.x) as its spreadsheet and CSV generation library. This library was selected because it supports true streaming output, has no transitive dependencies, and produces RFC 4180-compliant CSV without requiring the caller to manage quoting or escaping manually.

The library is initialized once per export job with a target writable stream. Column headers are declared at initialization time and cannot be changed after the first row is written. Each row is passed to the library as a plain object whose keys match the declared header names; the library handles type coercion, special-character escaping, and line termination automatically.

The library does not support XLSX or ODS output. Any future requirement to generate spreadsheet formats other than CSV will require either adding a second library or replacing csv-stream-writer with a multi-format library. That decision must go through the standard format-change approval process described in the export format decision document.

Usage example:

```python
writer = CsvStreamWriter(stream, columns=["id", "title", "status", "due_date"])
for task in task_batch:
    writer.write_row(task)
writer.close()
```

The library is pinned to a minor version in the service's dependency manifest. Patch updates may be applied without review. Minor or major version upgrades require a changelog review and a regression run against the export integration test suite before they are merged.
