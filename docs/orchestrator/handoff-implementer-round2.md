# Handoff: Implementer (round 2 — address review findings)

The reviewer examined your changes for the CSV export feature and reported 4 issues (0 high, 1 medium, 3 low). Per workflow policy, more than three reported issues triggers a fix-and-re-review loop. Please address all four:

1. **Medium — example-task-app/src/app.js**: No test coverage for the export wiring (`setupExportCsvButton`, `downloadTextFile`, `exportTasksAsCsv`) — the actual click-to-download path is untested. Fix: refactor so the click handler's "save" step is an injectable/callable piece that can be unit-tested without real browser APIs (e.g. export `exportTasksAsCsv`/the row-building call separately from the DOM-triggering part), OR add a minimal test that stubs `document`/`Blob`/`URL.createObjectURL`/`revokeObjectURL` and asserts the handler builds the correct CSV and calls the download trigger with filename `tasks.csv`. Prefer the refactor-for-testability approach if it keeps things simple.

2. **Low — example-task-app/src/csv.js**: `escapeCsvField`'s null/undefined handling is untested. Fix: add test cases `escapeCsvField(null) === ""` and `escapeCsvField(undefined) === ""` to tests/csv.test.js.

3. **Low — example-task-app/src/app.js**: Top-level side effects (`renderTaskList()`, `setupExportCsvButton()`) run on import and reference `document`, which would throw if this module were ever imported under Node's test runner (no DOM). Fix: guard with `if (typeof document !== "undefined") { ... }` or move into a `DOMContentLoaded` listener, so the module stays safely importable for future tests.

4. **Low — example-task-app/src/index.html**: The `#status-message` text was changed beyond what the PRD asked for (PRD only requires adding the button). Fix: confirm nothing depends on the old wording; since this is a fresh starter app with no other references found, it's fine to keep the updated copy — no action required unless you want to minimize the diff further.

Keep all other constraints from the original brief (docs/orchestrator/handoff-implementer.md) in force: no changes to tasks.js/tasks.test.js/package.json, no backend/auth changes.

Report back: what you changed for each of the 4 items (or your reasoning if you judged an item not to need a change, e.g. item 4).
