# Product Requirements Document: Export Tasks to CSV

## Summary

Add an "Export CSV" control to the task-tracking web app so a user can download the currently visible task list as a CSV file.

## User story

As a user who tracks tasks in the app, I want to export my task list to a CSV file so I can open the data in a spreadsheet or share it with another system.

## Scope

The starter app is in `example-task-app/`. If you are using your own project, replace this path with your real app path in the orchestrator prompt.

## Functional requirements

1. Add an "Export CSV" button near the task list.
2. When clicked, the button downloads a file named `tasks.csv`.
3. The CSV includes these headers in order:
   - `id`
   - `title`
   - `status`
   - `dueDate`
   - `completed`
4. Each visible task appears as one row in the file.
5. CSV values with commas, double quotes, or line breaks are escaped correctly.
6. If the list is empty, the downloaded file still contains the header row.
7. The app does not require a server call to export CSV.

## Non-goals

- Do not add authentication.
- Do not change the task data model unless the existing model prevents CSV export.
- Do not add a backend endpoint for export.

## Acceptance criteria

- A user can click "Export CSV" and receive a valid `tasks.csv` file.
- Spreadsheet software can open the exported file with the expected columns.
- Tests cover CSV formatting, including commas and quotes.
- Existing task list behavior remains unchanged.
