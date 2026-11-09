# Course Tools Dummy MCP Server

This folder provides an example MCP server for the lesson's tool-scoping exercise. It is intentionally simple and safe. The server exposes individually grantable tools and checks the caller role against `roles.allowlist.json`.

The lesson's definitions use tool identifiers of the form:

```text
mcp__coursetools__<tool_name>
```

For example:

```text
mcp__coursetools__file_read
mcp__coursetools__task_tracker
```

The server expects a `role` argument on each tool call so the authorization check can return a clear error for denied calls during the exercise.
