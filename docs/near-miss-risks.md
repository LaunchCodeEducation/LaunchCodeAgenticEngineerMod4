# Near-miss risk statements (input to the governance policy)

1. The Implementer was granted delete_entry, a destructive capability outside its write-only charter, purely because the tool was made available.
   Risk: an Implementer with delete access can silently erase project state other subagents depend on, with nothing structural to stop it.

2. When the over-broad grant was exercised live, only the orchestrator's in-the-moment judgment refused the deletion.
   Risk: a safeguard that depends on an agent choosing to refuse disappears the moment a run reasons differently, so the forbidden action eventually goes through unnoticed.

3. Real storage writes logged calling_role "unknown", so forbidden_operations could not attribute the operation; the lab catch only worked because a fixture supplied a role the live system never records.
   Risk: if the audit log can't tie an operation to a real role, any role-keyed policy check can be evaded and a forbidden action passes unattributed.

4. In-session subagents share one MCP server process, so the server sees a single AGENT_ROLE for every subagent regardless of which one called.
   Risk: when all subagents act through one process, per-role least-privilege is not enforced — an Implementer's call is indistinguishable from the orchestrator's.

5. The server fixes its role from AGENT_ROLE at launch, and an unset or wrong value is applied to every call it serves.
   Risk: a mis-set or over-broad AGENT_ROLE lets a process serve every request at a privilege level the calling agent was never granted.

6. On a query that matched nothing, the retrieval server fell back to returning top_k documents anyway, including a confidential one up to the role's ceiling.
   Risk: a search that returns documents on a zero-score miss hands a role classified material it neither matched nor needed, turning a retrieval miss into a classification leak.
