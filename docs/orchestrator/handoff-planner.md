# Handoff: Planner

## Feature request
Add an "Export CSV" button to the task list, per the PRD at docs/prd.md:
- Button near the task list; on click downloads `tasks.csv`.
- CSV headers in order: id, title, status, dueDate, completed.
- One row per currently visible task.
- Correctly escape commas, double quotes, and line breaks.
- Empty list still produces a header-only file.
- No server call required for export.
- Non-goals: no auth changes, no data model changes (unless export is blocked without it), no backend endpoint.

## Repo path
Project root (mounted at /workspace). App code lives under `example-task-app/`.

## Requested output
A short, ordered implementation plan and a list of files to change to satisfy the PRD's functional requirements and acceptance criteria.
