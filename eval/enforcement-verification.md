\# Enforcement Verification



\## Layer 1: Container Permissions



\*\*Role:\*\* documentation-writer



\*\*Workspace check\*\*



\*\*Command:\*\*

`touch /workspace/should-fail.txt`



\*\*Output:\*\*

`touch: cannot touch '/workspace/should-fail.txt': Read-only file system`



\*\*Memory volume check\*\*



\*\*Command:\*\*

`if grep -q ' /memory ' /proc/mounts; then echo "unexpected: /memory is mounted"; else echo "OK: /memory is not mounted"; fi`



\*\*Output:\*\*

`OK: /memory is not mounted`



\*\*Result:\*\* Blocked as expected. The documentation-writer has a read-only workspace and no memory volume, matching its governance policy.
## Layer 2: MCP Server Allow-Lists

**Denied operation check**

**Command:**
`npx @modelcontextprotocol/inspector --cli python mcp-servers/storage/server.py -e AGENT_ROLE=documentation-writer --transport stdio --method tools/call --tool-name write_entry --tool-args-json '{"key":"probe","value":"should-be-denied"}'`

**Output:**
`authorization_denied: role 'documentation-writer' may not call 'write_entry'. See docs/governance-policy.md.`

**Result:** Blocked as expected.

**Granted operation check**

**Command:**
`npx @modelcontextprotocol/inspector --cli python mcp-servers/storage/server.py -e AGENT_ROLE=documentation-writer --transport stdio --method tools/call --tool-name read_entry --tool-args-json '{"key":"probe"}'`

**Output:**
`{"key":"probe","value":null}`

`"isError": false`

**Result:** Allowed as expected.

**Classification ceiling check**

**Command:**
`npx @modelcontextprotocol/inspector --cli python mcp-servers/retrieval/server.py -e AGENT_ROLE=documentation-writer --transport stdio --method tools/call --tool-name retrieve --tool-args-json '{"query":"design specification"}'`

**Output:**
`"result": []`

`"isError": false`

**Audit log tail:**

`{"event":"authorization_denied","operation":"write_entry","role":"documentation-writer","outcome":"authorization_denied","policy_reference":"docs/governance-policy.md"}`

`{"event":"storage_read","operation":"read_entry","role":"documentation-writer","outcome":"success","policy_reference":"docs/governance-policy.md"}`

`{"event":"classification_withheld","operation":"retrieve","role":"documentation-writer","outcome":"classification_withheld","detail":"1 result(s) above the 'internal' ceiling were withheld","policy_reference":"docs/governance-policy.md"}`

**Result:** The documentation-writer was denied a forbidden storage write, allowed a permitted storage read, and prevented from receiving content above its internal classification ceiling.
## Policy Test Suite

**Command:**
`pytest eval/test_policy.py -v`

**Output:**
`6 passed in 0.17s`

**Result:** All policy tests passed, including the documentation-writer policy/enforcement alignment check.
## Final Commit Evidence

**Passing policy test count:** 6 passed

**Commit message recording the passing check count:**
`eval: verify documentation-writer governance (6 policy checks passing)`