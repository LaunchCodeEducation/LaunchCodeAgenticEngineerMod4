# Routing and Tool Grant Map

Project: `proj-csv`

This map is the design decision of record. Agent definitions in `.agents/` implement this table. When a definition and this map disagree, update the definition to match the map.

## Storage operation grants

All storage operations are on the `storage` MCP server and are named `mcp__storage__<operation>` in agent definitions.

| Role | Storage operations granted | Storage operations denied (reason) | Classification it may write |
| :--- | :--- | :--- | :--- |
| `planner` | `read_entry`, `list_entries`, `write_entry` | `update_entry`, `delete_entry` — plans are new entries; the Planner does not revise or remove records. | `public`, `internal` |
| `implementer` | `read_entry`, `list_entries`, `write_entry`, `update_entry` | `delete_entry` — may revise its own notes but must never remove records. | `public`, `internal` |
| `reviewer` | `read_entry`, `list_entries`, `write_entry` | `update_entry`, `delete_entry` — read-only toward others' work; writes only its own review. | `public`, `internal` |
| `tester` | `read_entry`, `list_entries`, `write_entry` | `update_entry`, `delete_entry` — records a result; does not alter or remove records. | `public`, `internal` |
| `project-manager` | `read_entry`, `list_entries` | `write_entry`, `update_entry`, `delete_entry` — owns ticket state, not persistent project memory. | none; read-only |

Cross-role check:

- `read_entry` and `list_entries` are granted widely, but they are read-only, project-scoped operations.
- `write_entry` appears on four roles, but writes are schema-bound, classification-limited, project-scoped, and audited.
- `update_entry` appears only on the Implementer.
- `delete_entry` appears on no role.

Alternative considered: granting the Implementer `delete_entry` for scratch cleanup. Ruled out because cleanup is not worth giving a coding role a destructive capability. If cleanup becomes necessary, introduce a dedicated maintenance role with explicit review.

## Retrieval operation grants

The retrieval server exposes one operation, `mcp__retrieval__retrieve`. A grant has two parts: operation access and the classification ceiling pinned to the role.

| Role | Retrieval operation granted | Retrieval ceiling | Retrieval denied (reason) |
| :--- | :--- | :--- | :--- |
| `planner` | `retrieve` | `internal` | none |
| `implementer` | `retrieve` | `internal` | none |
| `reviewer` | `retrieve` | `internal` | none |
| `tester` | none | n/a | `retrieve` — works from supplied acceptance criteria; does not search the reference corpus. |
| `project-manager` | none | n/a | `retrieve` — owns the ticket tool and does not perform reference lookups. |

Cross-role check:

- `retrieve` appears on three roles, which is acceptable because it is read-only, project-scoped, capped at the role's ceiling, and returns citations.
- No role receives a ceiling above `internal`; confidential reference documents remain out of reach by default.

Alternative considered: granting the Tester `retrieve`. Ruled out because the Tester receives acceptance criteria in its task brief and records results against them. An independent corpus search adds a capability the role does not require.

Alternative considered: raising the Reviewer ceiling to `confidential` for cost reviews. Ruled out because no review task in this workflow needs cost figures; the confidential cost document stays out of reach unless a specific task justifies an exception.
