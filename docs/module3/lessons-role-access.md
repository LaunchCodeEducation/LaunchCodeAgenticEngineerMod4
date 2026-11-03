# Lessons Learned Role Access

Project: `proj-lessons`

| Role | Retrieval | Storage | Classification Ceiling | Reason |
|---|---|---|---|---|
| Planner | `retrieve` | None | internal | Retrieves prior lessons before choosing an implementation approach. |
| Implementer | `retrieve` | `write_entry` | internal | Uses prior lessons while coding and records a new lesson after a real code change. |
| Code Reviewer | `retrieve` | None | internal | Retrieves prior lessons and standards before reviewing changes. |
| Tester | `retrieve` | None | internal | Retrieves prior lessons and standards before verification. |
| Verifier | None | `read_entry`, `list_entries` | internal | Verifies persisted lessons through the storage MCP without direct database access. |

## Enforcement

Tool exposure is restricted in each agent definition under `.claude/agents/`.

The MCP role allowlist is defined in `mcp/roles.allowlist.json`.

Retrieval also enforces each role's classification ceiling server-side. A Planner request for a `confidential` ceiling was denied:

`planner may retrieve only up to internal`

Storage enforces the Implementer's `write_entry` permission server-side. Verification showed:

- Implementer `write_entry`: allowed
- Planner `write_entry`: denied

The successful Implementer permission test was recorded in `/memory/storage-audit.log`.
