---
name: draft-pr-description
description: Draft the pull-request description from the assembled run summary (what was built, review outcome, test outcome).
---

# draft-pr-description

Turns `docs/run-summary.md` into a pull-request description: the change, the review outcome,
the test outcome, and any open risks. The draft is shown to a human before it is posted.

## Activation Scope

- **Permitted roles:** project-manager
- **Denied roles:** orchestrator, planner, implementer, reviewer, tester
- **Reason:** The project manager owns outward-facing status and PR text
  (`docs/governance-policy.md`, skill tables).
