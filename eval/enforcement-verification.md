# Enforcement Verification

New role: **dependency-auditor** (`docs/governance-policy.md`, "Role: dependency-auditor"; defined in `agents/dependency-auditor.md`).
Run date: 2026-11-10. All output below is copied from the terminal.

## Layer 1: Container Permissions

**Role:** dependency-auditor
Launched with `.\scripts\run-agent.ps1 dependency-auditor bash`:

```
Launching 'dependency-auditor': workspace=ro, memory=omitted
```

**Workspace check**
**Command:** `touch /workspace/should-fail.txt`
**Output:**

```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Memory volume check**
**Command:** `grep -q ' /memory ' /proc/mounts && echo "unexpected: /memory is mounted" || echo "OK: /memory is not mounted"`
**Output:**

```
OK: /memory is not mounted
```

**Result:** blocked as expected. The workspace is read-only and the memory volume is absent, matching the policy line `Container permissions: workspace read-only, memory omitted`.

## Layer 2: MCP Server Allow-Lists

**Denied operation check**
**Command:**

```
npx @modelcontextprotocol/inspector --cli -e AGENT_ROLE=dependency-auditor python3 mcp-servers/storage/server.py --method tools/call --tool-name write_entry --tool-arg key=audit --tool-arg value=findings
```

**Output:**

```
[11/10/26 06:40:29] Error calling tool 'write_entry'
{
  "content": [
    {
      "type": "text",
      "text": "authorization_denied: role 'dependency-auditor' may not call 'write_entry'. See docs/governance-policy.md."
    }
  ],
  "isError": true
}
{"error":{"code":"tool_is_error","message":"Tool 'write_entry' returned isError:true."}}
```

**Granted operation check**
**Command:**

```
npx @modelcontextprotocol/inspector --cli -e AGENT_ROLE=dependency-auditor python3 mcp-servers/storage/server.py --method tools/call --tool-name list_entries
```

**Output:**

```
{
  "content": [
    {
      "type": "text",
      "text": "{\"keys\":[\"probe\"]}"
    }
  ],
  "structuredContent": {
    "keys": [
      "probe"
    ]
  },
  "isError": false
}
```

**Classification ceiling check**
**Command:**

```
npx @modelcontextprotocol/inspector --cli -e AGENT_ROLE=dependency-auditor python3 mcp-servers/retrieval/server.py --method tools/call --tool-name retrieve --tool-arg query="design specification"
```

**Output:**

```
{
  "content": [],
  "isError": false
}
```

The `confidential-design-spec` document was not returned to a role capped at internal.

**Audit log tail:**

```
$ tail -n 2 logs/storage-audit-log.jsonl
{"timestamp": "2026-11-10T06:40:29.069406+00:00", "event": "authorization_denied", "operation": "write_entry", "role": "dependency-auditor", "outcome": "authorization_denied", "detail": null, "policy_reference": "docs/governance-policy.md"}
{"timestamp": "2026-11-10T06:41:44.797059+00:00", "event": "storage_list", "operation": "list_entries", "role": "dependency-auditor", "outcome": "success", "detail": null, "policy_reference": "docs/governance-policy.md"}

$ tail -n 1 logs/retrieval-audit-log.jsonl
{"timestamp": "2026-11-10T06:42:37.737740+00:00", "event": "classification_withheld", "operation": "retrieve", "role": "dependency-auditor", "outcome": "classification_withheld", "detail": "1 result(s) above the 'internal' ceiling were withheld", "policy_reference": "docs/governance-policy.md"}
```

## Skill Activation Scope

`dependency-auditor` is listed under **Denied roles** in `skills/run-tests/SKILL.md` and `skills/draft-pr-description/SKILL.md`, matching `run-tests | NO` and `draft-pr-description | NO` in its policy entry. The coursetools allow-list (`mcp/roles.allowlist.json`) grants it only `file_read` and `codebase_search`; `test_runner`, `file_write`, `shell`, and `task_tracker` are not granted.

## Policy Test Suite

**Command:** `pytest eval/test_policy.py -v 2>&1 | tail -n 5`
**Output:**

```
eval/test_policy.py::test_container_workspace_matches_policy[reviewer] PASSED [ 95%]
eval/test_policy.py::test_container_workspace_matches_policy[tester] PASSED [ 97%]
eval/test_policy.py::test_scripts_launch_no_role_without_policy PASSED   [100%]

============================== 40 passed in 0.58s ==============================
```

40 checks pass with the new role included (36 before; the 4 new parametrized checks cover dependency-auditor's definition file, storage allow-list, retrieval allow-list, and container branch).

**Commit message recording the passing count:**

```
eval: dependency-auditor red-team and policy tests (Prompt 7 blocked at Layer 1; all 40 policy checks passing)
```
