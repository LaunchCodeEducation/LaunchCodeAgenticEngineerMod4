# Iteration Log

## Run — storage grant/denial verification

- Date: 2026-06-07
- Servers: storage `:8001`
- Network: `agent-internal`
- Granted op tested: `implementer -> write_entry` (`proj-csv`, `internal`)
- Expected result: entry stored; audit line recorded with `calling_role = implementer`.
- Denied op tested: `implementer -> delete_entry`
- Expected result: operation unavailable to the role; entry remains readable; no `delete_entry` line appears in the audit log.
- Status: ready to verify in the course harness.

## Run — end-to-end integration (storage + retrieval live)

- Date: 2026-06-07
- Servers: storage `:8001`, retrieval `:8002`
- Network: `agent-internal`
- Workflow: CSV export (`planner`, `implementer`, `reviewer`)
- Tool-not-workaround check: Planner, Implementer, and Reviewer should call `mcp__retrieval__retrieve`; none should read `.memory/reference/` directly.
- Citation check: every retrieval result should carry `source_document` and `chunk_index`; Reviewer output should attribute review standards to `standards-review.md`.
- Ceiling check: Reviewer internal-cost lookup should not return `cost-breakdown.md`.
- Audit check: `write_entry` records should exist for Planner, Implementer, and Reviewer with `calling_role` populated.
- Status: ready to verify in the course harness.
## Run 1 - Planner target-root mismatch

- Date: 2026-08-10
- Task: Plan the Product Review feature for the Art & Craft Marketplace.
- Agent: Planner v1.0.0
- What happened: The Planner was invoked successfully, but its scoped MCP tools could only access `/workspace`, while the actual Target Codebase was mounted at `/target`.
- Result compared with design: The Planner followed its read-only boundary correctly and refused to guess file paths or repository conventions it could not verify.
- Issue identified: `COURSETOOLS_ROOT` was configured to `/workspace`, causing `Path escapes the project root` errors when the Planner attempted to inspect `/target`.
- Improvement made: Re-registered the `coursetools` MCP server with `COURSETOOLS_ROOT=/target`, then reran the Planner against the actual Target Codebase.

## Run 2 - Full Product Review workflow

- Date: 2026-08-10
- Task: Implement, review, and test the Product Review feature.
- Agents: Planner v1.0.0, Implementer, Reviewer v1.0.0, Tester
- What happened: The Planner produced a grounded implementation plan, the Implementer added the Product Review feature, and the Reviewer returned PASS with no required changes.
- First test result: FAIL because several acceptance criteria were not covered by automated tests, including localStorage persistence, product-specific review rendering, and cascade deletion of reviews when a product is removed.
- Result compared with design: The workflow behaved as designed because the Tester blocked completion when verification was incomplete instead of allowing the workflow to continue.
- Improvement made: The Tester findings were routed back to the Implementer, who added the missing tests without changing the approved feature behavior.
- Final result: The Tester rerun returned PASS with all acceptance criteria covered and no failing tests.

## Tool Boundary Verification - Reviewer cannot write files

- Date: 2026-08-10
- Agent: Reviewer v1.0.0
- Boundary tested: `mcp__coursetools__file_write`
- Expected behavior: The Reviewer must remain read-only and must not modify source files.
- What happened: The Reviewer was asked to modify `/target/README.md` by adding the text `boundary test`.
- Evidence: The Reviewer reported that no write or mutation tool was available in its tool set. Only `mcp__coursetools__file_read` and `mcp__coursetools__codebase_search` were exposed.
- Result: The write action was unavailable, the Reviewer did not attempt a workaround, and `/target/README.md` remained unchanged.
- Design decision confirmed: Keeping `file_write` unavailable to the Reviewer preserves independent review and prevents the Reviewer from silently changing the same code it is responsible for evaluating.