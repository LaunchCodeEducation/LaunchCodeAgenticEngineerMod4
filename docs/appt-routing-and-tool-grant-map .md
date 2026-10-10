# Routing-and-Tool-Grant Map — Appointment-App Backend Fix Pipeline

One row per role. Tools use the coursetools MCP identifiers (mcp__coursetools__<tool>).

| Role | Receives | Produces | Tools granted | Tools denied (reason) | Context isolation reason | Autonomy |
|------|----------|----------|---------------|-----------------------|--------------------------|----------|
| Planner | Issue text + repo path | Fix plan + file list | file_read, codebase_search | file_write (writes no code), shell, test_runner (does not test), task_tracker, web_search | Reads code but never changes it; write/execute withheld keeps blast radius at zero | High (plans are cheap to fix) |
| Implementer | Plan + file list | Modified files | file_read, file_write, codebase_search | shell, test_runner (Tester owns it), task_tracker, web_search | Needs read+write; withholding test_runner means it cannot grade its own work | Medium (writes files) |
| Security-Reviewer | Modified files | Review report | file_read, codebase_search | file_write (proposes, never edits), shell, test_runner, task_tracker, web_search | Read-only by design; no write/execute means it can only report, never change | High (read-only) |
| Tester | Modified files | Pass/fail report | file_read, test_runner | file_write (must not "fix" code to mask failures), codebase_search, shell, task_tracker, web_search | Owns test execution only; no file_write means it cannot edit code to force a pass | Medium (executes, bounded to tests) |

Cross-role check:
- file_read on 3 roles, codebase_search on 3 — read-only primitives, acceptable.
- file_write on 1 role (Implementer). test_runner on 1 role (Tester). No flags.
- shell, task_tracker, web_search on no role — withheld until a specific need justifies them.

Alternatives considered:
- Giving the Security-Reviewer test_runner to verify its own findings. Ruled out: test execution
  belongs to the Tester; a reviewer that can also run tests blurs ownership when a test fails.
- Giving the Implementer test_runner so it can check its work. Ruled out: keeping the test runner
  out means the Implementer cannot grade its own change and mask a failure; the Tester is the
  independent check.
- Granting shell anywhere as an escape hatch. Ruled out: shell runs any command (large, unauditable
  surface); no role here has a concrete need it doesn't already meet with a narrower tool.
