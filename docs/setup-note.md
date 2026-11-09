# Setup Note: Dummy Course Tools MCP Server

This setup note supplies the missing course-material details referenced by the lesson. It uses the included example server in `mcp/coursetools_server.py` and the server name `coursetools`.

## Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r mcp/requirements.txt
```

## Register the server with Claude Code

From the repository root:

```bash
claude mcp add coursetools --scope project -- python mcp/coursetools_server.py
```

The included `.mcp.json` represents the same project-level configuration.

## Verify the connection

```bash
claude mcp list
```

Inside a Claude Code session, open the MCP panel:

```text
/mcp
```

You should see the `coursetools` server and these individually grantable tools:

- `mcp__coursetools__file_read`
- `mcp__coursetools__file_write`
- `mcp__coursetools__codebase_search`
- `mcp__coursetools__shell`
- `mcp__coursetools__test_runner`
- `mcp__coursetools__task_tracker`
- `mcp__coursetools__web_search`

## Denial verification prompt

Launch the Implementer and ask it to attempt the task-tracker tool:

```text
Use the implementer subagent. Attempt to call mcp__coursetools__task_tracker with role=implementer and ticket_id=CSV-101.
```

Expected result: the server returns an authorization error because `task_tracker` is owned by `project-manager`.
