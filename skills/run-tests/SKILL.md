---
name: run-tests
description: Run the project test suite and report pass/fail per test. Backed by the coursetools test_runner tool.
---

# run-tests

Runs the FashionMate test suite and reports pass or fail for each test. In this harness the
skill is executed through the coursetools `test_runner` tool (`mcp/coursetools_server.py`),
whose allow-list (`mcp/roles.allowlist.json`) must match the Activation Scope below.

## Activation Scope

- **Permitted roles:** implementer, tester
- **Denied roles:** orchestrator, planner, reviewer, project-manager, dependency-auditor
- **Reason:** Running tests is core to implementing and verifying a change. Read-only roles must not
  run it because a test run writes output and can change workspace state
  (`docs/governance-policy.md`, skill tables).
