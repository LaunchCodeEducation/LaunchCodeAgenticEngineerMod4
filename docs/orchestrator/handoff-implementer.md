# Handoff: Implementer

## Approved plan (human-approved, proceed exactly as below)

1. Create `example-task-app/src/csv.js` — pure CSV module:
   - Field-escaping helper: wrap a value in double quotes and double internal quotes whenever it contains a comma, double quote, or line break (`\n` or `\r`).
   - Header constant/order: `id, title, status, dueDate, completed`.
   - `tasksToCsv(tasks)`: emits header row first, then one row per task (stringify `completed` as `true`/`false`), joined with a consistent line separator. Empty array -> header-only output, no trailing blank row.
   - No browser-only APIs (`document`, `Blob`, `URL`) in this module — must be unit-testable under plain Node.

2. Create `example-task-app/tests/csv.test.js` using the existing `node:assert/strict` + `node:test` pattern (auto-picked up by `tests/*.test.js`). Cover:
   - Header row has exactly the five headers in required order.
   - One row per task, correct column order/values.
   - Escaping: comma, double quote, embedded line break.
   - Empty input -> header-only output.

3. Modify `example-task-app/src/index.html` — add an "Export CSV" `<button>` (e.g. `id="export-csv-button"`) near `<ul id="task-list">`. Optionally update the stale `#status-message` text ("Starter app: CSV export has not been implemented yet.") since it will no longer be accurate.

4. Modify `example-task-app/src/app.js`:
   - Import `tasksToCsv` from `./csv.js`.
   - Add a small browser-only helper that takes a CSV string + filename, builds a `Blob`, creates an object URL, triggers download via a temporary `<a download>` element, then revokes the URL.
   - Attach a click listener on `#export-csv-button` that calls `getTasks()`, builds CSV via `tasksToCsv`, downloads as `tasks.csv`.
   - Wire this at module load alongside the existing `renderTaskList()` call. Do not otherwise change `renderTaskList`'s behavior.

## Explicit constraints
- No changes to `example-task-app/src/tasks.js`, `example-task-app/tests/tasks.test.js`, or `example-task-app/package.json` (no new dependencies).
- No backend endpoint, no auth changes (per PRD non-goals).
- Ignore `.memory/reference/security-export-visibility.md`'s server-side re-evaluation guidance — not applicable here (PRD explicitly requires no server call).
- Row separator: `\r\n` recommended, but plain `\n` acceptable if consistent and tested.

## Reference
Full PRD: docs/prd.md
