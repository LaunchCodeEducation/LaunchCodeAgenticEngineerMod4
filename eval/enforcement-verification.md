# Enforcement Verification

Role under test: **dependency-auditor** (read-only auditor; storage read/list only,
retrieval granted at internal ceiling, all writes/delete and confidential denied).

## Layer 1: Container Permissions
**Role:** dependency-auditor

**Workspace check**
**Command:** touch /workspace/should-fail.txt
**Output:**
touch: cannot touch '/workspace/should-fail.txt': Read-only file system

**Memory volume check**
**Command:** grep -q ' /memory ' /proc/mounts && echo "BAD: memory mounted" || echo "OK: no /memory"
**Output:**
OK: no /memory

**Result:** blocked as expected — workspace is read-only and the memory volume is not mounted, matching the policy's container line (workspace read-only, memory omitted).

## Layer 2: MCP Server Allow-Lists
Note: verified by calling each server's `_authorize` gate / `retrieve` directly with
AGENT_ROLE set, rather than MCP Inspector — the installed Inspector (v2.9.0) changed
its CLI. The probe exercises the same allow-list and writes the same audit records.

**Denied operation check**
**Command:** AGENT_ROLE=dependency-auditor python3 /tmp/probe.py mcp-servers/storage/server.py write_entry
            AGENT_ROLE=dependency-auditor python3 /tmp/probe.py mcp-servers/storage/server.py delete_entry
**Output:**
DENIED: write_entry -> authorization_denied: role 'dependency-auditor' may not call 'write_entry'. See docs/governance-policy.md.
DENIED: delete_entry -> authorization_denied: role 'dependency-auditor' may not call 'delete_entry'. See docs/governance-policy.md.

**Granted operation check**
**Command:** AGENT_ROLE=dependency-auditor python3 /tmp/probe.py mcp-servers/storage/server.py read_entry
**Output:**
ALLOWED: read_entry

**Classification ceiling check**
**Command:** AGENT_ROLE=dependency-auditor python3 /tmp/rprobe.py   (query: "design specification")
**Output:**
GRANTED; classifications: []
(the only matching document was classified confidential, above the role's internal ceiling, so it was withheld)

**Audit log tail:**
{"timestamp": "2026-10-06T20:38:57Z", "event": "authorization_denied", "operation": "write_entry", "role": "dependency-auditor", "policy_reference": "docs/governance-policy.md"}
{"timestamp": "2026-10-06T20:38:58Z", "event": "authorization_denied", "operation": "delete_entry", "role": "dependency-auditor", "policy_reference": "docs/governance-policy.md"}
{"timestamp": "2026-10-06T20:39:01Z", "event": "classification_withheld", "operation": "retrieve", "role": "dependency-auditor", "detail": "1 result(s) above the 'internal' ceiling were withheld", "policy_reference": "docs/governance-policy.md"}

